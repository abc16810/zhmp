from rest_framework import serializers
from mp.apps.models import ResourceGroup, Apps
from mp.users.models import MyUser
from django.db import transaction
from mp.workflow.utils import get_audit_auth_groups, CommonAudit
# from sites.workflow.signals import save_workflow
from itertools import chain
from mp.workflow.models import WorkFlow, WorkFlowAudit, WorkflowAuditLog, WorkflowLog
from django.db.models import F, Value, IntegerField
import json, string
from django.utils.html import format_html


class AppsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apps
        fields = ["id", "name"]


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'display_name']


class AppGroupSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    apps_count = serializers.SerializerMethodField(read_only=True)
    # user = serializers.SlugRelatedField(many=True, read_only=True, slug_field='username') # 目标上的字段
    # user = serializers.PrimaryKeyRelatedField(many=True, read_only=True) # 目标 id
    # user = serializers.StringRelatedField(many=True) # 目标 __str__
    user = UsersSerializer(many=False, read_only=True)  # 递归
    apps = AppsSerializer(many=True, read_only=True)
    member = serializers.SerializerMethodField(read_only=True, required=False)
    node_paths = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ResourceGroup
        fields = ["id", 'name', 'created_at', 'updated_at', 'user',
                  'apps_count', 'apps', 'node_paths', 'member']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for x in ret:
            if x == 'user' and not ret[x]:
                ret['user'] = {}
        return ret

    @staticmethod
    def get_apps_count(obj):
        return obj.apps.count()

    @staticmethod
    def get_node_paths(obj):
        return obj.node_paths()

    @staticmethod
    def get_member(obj):
        res = []
        if hasattr(obj, 'to_member'):
            for item in obj.to_member:
                data = item.to_json()
                if obj.user and int(data['id']) == obj.user.id:
                    data['is_major'] = True
                res.append(data)
        # 负责人也是成员之一
        if obj.user:
            tmp = obj.user.to_json()
            if tmp not in res:
                tmp['is_major'] = True
                res.append(tmp)
        return res


class AppGroupDetailSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    update_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    rows = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ResourceGroup
        fields = ["group_id", 'group_name', 'is_deleted', 'create_date', 'update_date', 'rows']

    @staticmethod
    def get_rows(obj):
        rows_users = obj.user.annotate(object_id=F('id'), object_type=Value(0, output_field=IntegerField()),
                                       object_name=F('display'),group_id=F('resourcegroup__group_id'),
                                       group_name=F('resourcegroup__group_name')).values(
            'object_type', 'object_id', 'object_name', 'group_id', 'group_name')
        rows_apps= obj.app.annotate(object_id=F('id'), object_type=Value(1, output_field=IntegerField()),
                                    object_name=F('name'),
                                    group_id=F('resourcegroup__group_id'),
                                    group_name=F('resourcegroup__group_name')
                                    ).values(
            'object_type', 'object_id', 'object_name',
            'group_id', 'group_name')
        return  list(chain(rows_users, rows_apps))


class SingleAppGroupListSerializer(serializers.BaseSerializer):

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def to_internal_value(self, data):
        pass

    def to_representation(self, instance):

        return {
            'object_id': instance[0],
            'object_type': instance[1],
            'object_name': instance[2],
            'group_name': instance[3]
        }


class SingleAppGroupUnassociatedSerializer(serializers.Serializer):
    object_type = serializers.IntegerField(label="类型")
    object_ids = serializers.CharField(help_text="格式: [\"1\",\"2\"]" , label="对象ID")

    def update(self, instance, validated_data):
        object_type = validated_data.get('object_type')
        object_ids = validated_data.get('object_ids')
        ids = [x for x in object_ids if x in string.digits]
        if object_type == 0:  # 用户
            instance.user.add(*MyUser.objects.filter(pk__in=ids))
        else:
            instance.app.add(*Apps.objects.filter(pk__in=ids))
        return self.instance

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        t = ret.get('object_type')
        ids = ret.get('object_ids')
        try:
            id_list = json.loads(ids)
            assert isinstance(id_list, list)
        except Exception as err:
            raise serializers.ValidationError({
                'object_ids': "请输入正确的格式"
            })
        if not int(t) in [0, 1]:
            raise serializers.ValidationError({
                'object_type': "类型不正确"
            })
        return ret

    def create(self, validated_data):
        pass

    def to_representation(self, instance):
        if isinstance(instance, ResourceGroup):
            return {
                "status": 0,
                "msg": "更新成功"
            }
        return {
            'object_id': instance.get('object_id'),
            'object_name': instance.get('object_name'),
        }


class AddWorkFlowSerializer(serializers.ModelSerializer):
    work_status = serializers.CharField(required=False, read_only=True)
    app_name = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = WorkFlow
        fields = ["id", "work_name", "work_user_display", "work_status", "created_at", "app_name",
                  'app_group_id', "work_type", "run_date_start", "run_date_end"]

    def to_internal_value(self, data):
        ret = super(AddWorkFlowSerializer, self).to_internal_value(data)
        run_date_start = ret.get('run_date_start')
        run_date_end = ret.get('run_date_end')
        p = run_date_end - run_date_start
        if ( p.total_seconds() / 60 ) < 60:
            raise serializers.ValidationError({
                'msg': "可执行时间范围不应该短于60分钟"
            })
        request = self._context['request']
        if not request.user.is_superuser:
            app_group_id = ret.get('app_group_id')
            try:
                app_group_obj = ResourceGroup.objects.filter(is_deleted=False).filter(group_id=app_group_id).get()
            except:
                raise serializers.ValidationError({
                    'msg': "内部错误"
                })
            try:
                # 验证组权限（用户是否在该业务组）
                app_group_obj.user.filter(username=request.user.username).get()
            except:
                raise serializers.ValidationError({
                    'msg': "你不在该业务组，请联系管理员"
                })
        return ret

    def create(self, validated_data):
        request = self._context['request']
        # 调用工作流生成工单
        # 使用事务保持数据一致性
        workflow_type = validated_data.get('work_type')
        app_group_id = validated_data.get('app_group_id')
        # try:
        #     audit_auth_groups =  WorkFlowAudit.objects.get(
        #             workflow_type=workflow_type, group_id=app_group_id
        #         ).audit_auth_groups
        # except Exception:
        #     audit_auth_groups =  None
        items = validated_data.copy()
        items['work_user'] = request.user.username
        items['work_user_display'] = request.user.username
        try:
            app_group_obj = ResourceGroup.objects.filter(is_deleted=False).get(group_id=app_group_id)
            items['app_name'] = app_group_obj.group_name
            items['work_status'] = 'manreviewing'
            with transaction.atomic():
                # 存进数据库里
                workflow_obj = WorkFlow.objects.create(**items)
                # save_workflow.send(sender=workflow_obj.__class__,)
                # 检查是否已存在待审核数据
                CommonAudit.add(workflow_obj, request, app_group_id)
                return workflow_obj
        except Exception as f:
            msg = str(f) or "内部错误"
            return msg


    def save(self, **kwargs):
        instance = super().save(**kwargs)
        if isinstance(instance, str):
            raise Exception(instance)
        return instance


class WorkFlowLogListSerializer(serializers.ModelSerializer):
    operation_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = WorkflowLog
        fields = ['id', 'operation_info', 'operation_type_desc', 'operator_display', 'operation_time']


class AppsSerializer(serializers.ModelSerializer):
    get_env_display = serializers.CharField(required=False, read_only=True)

    group = serializers.SerializerMethodField(read_only=True, required=False)

    assets = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = Apps
        exclude = ('lft', 'rght', 'tree_id', 'env')

    @staticmethod
    def get_group(obj):
        return {
            'group_name': obj.group.node_paths() if obj.group else "无",
            'group_id': obj.group.pk if obj.group else None
        }

    @staticmethod
    def get_assets(obj):
        res = []
        if obj.to_assets:
            for item in obj.to_assets:
                res.append(item.to_json())
        return res
