import traceback
from datetime import datetime

from django.db import transaction
from django_q.tasks import async_task
from rest_framework import serializers

from mp.apps.models import ResourceGroup
from mp.common.tasks import add_workflow_schedule
from mp.common.tasks import del_schedule
from mp.users.models import MyGroup
from mp.workflow.models import WorkFlow, WorkFlowAudit, WorkflowLog
from mp.workflow.utils import CommonAudit, detail_by_workflow_id, can_cancel, add_log, can_timingtask, can_execute, \
    can_handle, can_finish


class AppsGroupAuditorsSerializer(serializers.Serializer):

    apps_group_id = serializers.IntegerField(required=True, label='业务组ID')
    workflow_type = serializers.ChoiceField(choices=WorkFlow.TYPE, label='工单类型')
    auth_group_name = serializers.CharField(required=True, max_length=255, label='审核组', help_text="组1,组2")

    @staticmethod
    def validate_apps_group_id(value):
        try:
            ResourceGroup.objects.get(pk=value)
        except ResourceGroup.DoesNotExist:
            raise serializers.ValidationError("不可用的业务组ID")
        else:
            return value

    @staticmethod
    def validate_auth_group_name(value):
        try:
            [
                MyGroup.objects.get(name=auth_group)
                for auth_group in value.split(",")
            ]
        except MyGroup.DoesNotExist:
            raise serializers.ValidationError("不可用的业务组ID")
        else:
            return value

    # def to_representation(self, instance):
    #     result = {"status": 0, "msg": "ok", "data": []}
    #     return result

    def create(self, validated_data):
        """
        """
        apps_group_obj = ResourceGroup.objects.get(pk=validated_data.get('apps_group_id'))
        auth_groups = validated_data.get('auth_group_name')
        workflow_type = validated_data.get('workflow_type')
        audit_auth_groups = [
            str(MyGroup.objects.get(name=auth_group).id)
            for auth_group in auth_groups.split(",")
        ]
        obj, create = WorkFlowAudit.objects.get_or_create(apps_group_id=apps_group_obj.id,
                                                          workflow_type=workflow_type)
        obj.apps_group_name = apps_group_obj.name
        obj.audit_auth_groups = ",".join(audit_auth_groups)
        obj.save()
        return obj


class WorkFlowBase(serializers.Serializer):

    workflow_id = serializers.IntegerField(required=True, label='工单ID')
    audit_remark = serializers.CharField(required=True, max_length=255, label='审核备注')

    def update(self, instance, validated_data):
        """更新存在的实例"""
        pass

    def create(self, validated_data):
        pass

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        if isinstance(instance, str):
            raise Exception(instance)
        return instance


class WorkFlowPassedSerializer(WorkFlowBase):

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        workflow_id = ret.get('workflow_id')
        try:
            workflow_obj = WorkFlow.objects.get(pk=workflow_id)
        except WorkFlow.DoesNotExist:
            raise serializers.ValidationError({
                'msg': "无效ID"
            })
        else:
            if not CommonAudit.cat_review(workflow_obj, self._context['request']):
                raise serializers.ValidationError({
                    'msg': "你无权操作当前工单！"
                })
        ret['workflow_obj'] = workflow_obj
        return ret

    def create(self, validated_data):
        """
        创建新实例
        """
        request = self._context['request']
        items = validated_data.copy()
        workflow_obj = items.get('workflow_obj')
        audit_remark = items.get('audit_remark')
        try:
            with transaction.atomic():
                audit_id = detail_by_workflow_id(workflow_obj.id, workflow_obj.work_type).audit_id
                audit_result = CommonAudit.audit_pass(audit_id, request, audit_remark)
                if audit_result == 1:  # 审核通过
                    workflow_obj.work_status = 'review_pass'
                    workflow_obj.save(update_fields=["work_status"])
                return workflow_obj
        except Exception as f:
            msg = str(f) or f"审核工单报错，错误信息：{traceback.format_exc()}"
            return msg


class WorkFlowCancelSerializer(WorkFlowBase):

    def to_internal_value(self, data):
        ret = super(WorkFlowCancelSerializer, self).to_internal_value(data)
        workflow_id = ret.get('workflow_id')
        try:
            workflow_obj = WorkFlow.objects.get(pk=workflow_id)
        except WorkFlow.DoesNotExist:
            raise serializers.ValidationError({
                'msg': "无效ID"
            })
        else:
            if not can_cancel(workflow_obj.pk, self._context['request']):
                raise serializers.ValidationError({
                    'msg': "你无权操作当前工单！"
                })
        ret['workflow_obj'] = workflow_obj
        return ret

    def create(self, validated_data):
        request = self._context['request']
        items = validated_data.copy()
        workflow_obj = items.get('workflow_obj')
        audit_remark = items.get('audit_remark')
        try:
            with transaction.atomic():
                audit_id = detail_by_workflow_id(workflow_obj.id, workflow_obj.work_type).audit_id
                if workflow_obj.work_status != 'manreviewing':  # 定时执行
                    if request.user.username == workflow_obj.work_user:
                        add_log(
                            audit_id=audit_id,
                            operation_type=3,
                            operation_type_desc="取消执行",
                            operation_info="取消原因：{}".format(audit_remark),
                            operator=request.user.username,
                            operator_display=request.user.display_name,
                        )
                    else:
                        add_log(
                            audit_id=audit_id,
                            operation_type=2,
                            operation_type_desc="审批不通过",
                            operation_info="审批备注：{}".format(audit_remark),
                            operator=request.user.username,
                            operator_display=request.user.display_name,
                        )
                else:
                    # 待审核状态 申请人取消审核
                    if request.user.username == workflow_obj.work_user:
                        CommonAudit.audit_abort_reject(
                            audit_id,
                            request,
                            3,   # 审核取消
                            audit_remark,
                        )
                    else:
                        CommonAudit.audit_abort_reject(
                            audit_id,
                            request,
                            2,  # 审核不通过
                            audit_remark,
                        )

                # 删除定时执行task
                if workflow_obj.work_status == "workflow_obj":
                    pass

                # 将流程状态修改为人工终止流程
                workflow_obj.work_status = "abort"
                workflow_obj.save()
            return workflow_obj
        except Exception as f:
            msg = f"取消工单报错，错误信息：{str(f)}"
            return msg


class WorkFlowtimingSerializer(WorkFlowBase):
    """
    定时执行 Serializer
    """

    audit_remark = serializers.CharField(required=False, read_only=True)
    run_date = serializers.DateTimeField(required=True, label="执行时间")

    def to_internal_value(self, data):
        ret = super(WorkFlowtimingSerializer, self).to_internal_value(data)
        workflow_id = ret.get('workflow_id')
        run_date = ret.get('run_date')
        try:
            workflow_obj = WorkFlow.objects.get(pk=workflow_id)
        except WorkFlow.DoesNotExist:
            raise serializers.ValidationError({
                'msg': "无效ID"
            })
        if not run_date:
            raise serializers.ValidationError({
                'msg': "无效的执行时间"
            })
        else:
            if workflow_obj.run_date_end and run_date > workflow_obj.run_date_end:
                raise serializers.ValidationError({
                    'msg': "不在可执行时间范围内，如果需要修改执行时间请重新提交工单"
                })
            tamp = int(run_date.timestamp())
            now = int(datetime.now().timestamp())
            if tamp < now:
                raise serializers.ValidationError({
                    'msg': "时间不能小于当前时间"
                })
        if not can_timingtask(workflow_obj.pk, self._context['request']):
            raise serializers.ValidationError({
                'msg': "你无权操作当前工单！"
            })

        ret['workflow_obj'] = workflow_obj
        return ret

    def create(self, validated_data):
        request = self._context['request']
        items = validated_data.copy()
        workflow_obj = items.get('workflow_obj')
        run_date = items.get('run_date')
        try:
            with transaction.atomic():
                # 将流程状态修改为定时执行
                workflow_obj.work_status = "timingtask"
                workflow_obj.save()
                # 调用添加定时任务
                schedule_name = f'Ansible-WorkFlow-Setup-{workflow_obj.id}'
                add_workflow_schedule(schedule_name, run_date, workflow_obj)
                # 增加工单日志
                audit_id = detail_by_workflow_id(workflow_obj.id, workflow_obj.work_type).audit_id
                add_log(
                    audit_id=audit_id,
                    operation_type=4,
                    operation_type_desc="定时执行",
                    operation_info="定时执行时间：{}".format(run_date),
                    operator=request.user.username,
                    operator_display=request.user.display_name
                )
            return workflow_obj
        except Exception as f:
            msg = f"定时执行工单报错，错误信息：{str(f)}"
            return msg


class WorkFlowExecSerializer(WorkFlowBase):
    """
    立即执行 Serializer
    """
    audit_remark = serializers.CharField(required=False, read_only=True)

    def to_internal_value(self, data):
        ret = super(WorkFlowExecSerializer, self).to_internal_value(data)
        workflow_id = ret.get('workflow_id')
        try:
            workflow_obj = WorkFlow.objects.get(pk=workflow_id)
        except WorkFlow.DoesNotExist:
            raise serializers.ValidationError({
                'msg': "无效ID"
            })
        if not can_execute(workflow_obj.pk, self._context['request']):
            raise serializers.ValidationError({
                'msg': "你无权操作当前工单！"
            })
        ctime = int(datetime.now().timestamp())
        if workflow_obj.run_date_end:
            ftime = int(workflow_obj.run_date_end.timestamp())
            if ctime > ftime:
                raise serializers.ValidationError({
                    'msg': "不在可执行时间范围内，如果需要修改执行时间请重新提交工单"
                })
        ret['workflow_obj'] = workflow_obj
        return ret

    def create(self, validated_data):
        request = self._context['request']
        items = validated_data.copy()
        workflow_obj = items.get('workflow_obj')
        try:
            with transaction.atomic():
                # 将流程状态修改为定时执行
                workflow_obj.work_status = "queuing"
                workflow_obj.save()
                # 删除定时执行任务
                schedule_name = f'Ansible-WorkFlow-Setup-{workflow_obj.id}'
                del_schedule(schedule_name)
                app_group_id = workflow_obj.app_group_id
                async_task(
                    "mp.common.exec_workflow.ansible_batch_update_by_apps",
                    app_group_id,
                    timeout=-1,
                    pk=workflow_obj.id,
                    work_type=workflow_obj.work_type,
                    user=request.user,
                    group=f"execute-{workflow_obj.id}",
                )

                # 增加工单日志
                audit_id = detail_by_workflow_id(workflow_obj.id, workflow_obj.work_type).audit_id
                add_log(
                    audit_id=audit_id,
                    operation_type=5,
                    operation_type_desc="执行工单",
                    operation_info="工单执行排队中",
                    operator=request.user.username,
                    operator_display=request.user.display_name
                )
            return workflow_obj
        except Exception as f:
            msg = f"执行工单报错，错误信息：{str(f)}"
            return msg


class WorkFlowHandlerSerializer(WorkFlowBase):
    """
    立即执行 Serializer
    """
    audit_remark = serializers.CharField(required=False, read_only=True)

    def to_internal_value(self, data):
        ret = super(WorkFlowHandlerSerializer, self).to_internal_value(data)
        workflow_id = ret.get('workflow_id')
        try:
            workflow_obj = WorkFlow.objects.get(pk=workflow_id)
        except WorkFlow.DoesNotExist:
            raise serializers.ValidationError({
                'msg': "无效ID"
            })
        if not can_handle(workflow_obj.pk, self._context['request']):
            raise serializers.ValidationError({
                'msg': "你无权操作当前工单！"
            })
        ctime = int(datetime.now().timestamp())
        if workflow_obj.run_date_end:
            ftime = int(workflow_obj.run_date_end.timestamp())
            if ctime > ftime:
                raise serializers.ValidationError({
                    'msg': "不在可处理时间范围内，如果需要修改处理时间请重新提交工单"
                })
        ret['workflow_obj'] = workflow_obj
        return ret

    def create(self, validated_data):
        request = self._context['request']
        items = validated_data.copy()
        workflow_obj = items.get('workflow_obj')
        try:
            with transaction.atomic():
                # 将流程状态修改为处理中
                workflow_obj.work_status = "executing"
                workflow_obj.save()
                # 增加工单日志
                audit_id = detail_by_workflow_id(workflow_obj.id, workflow_obj.work_type).audit_id
                add_log(
                    audit_id=audit_id,
                    operation_type=5,
                    operation_type_desc="处理工单",
                    operation_info="工单处理中",
                    operator=request.user.username,
                    operator_display=request.user.display_name
                )
            return workflow_obj
        except Exception as f:
            msg = f"处理工单报错，错误信息：{str(f)}"
            return msg


class WorkFlowFinishSerializer(WorkFlowBase):

    def to_internal_value(self, data):
        ret = super(WorkFlowFinishSerializer, self).to_internal_value(data)
        workflow_id = ret.get('workflow_id')
        try:
            workflow_obj = WorkFlow.objects.get(pk=workflow_id)
        except WorkFlow.DoesNotExist:
            raise serializers.ValidationError({
                'msg': "无效ID"
            })
        else:
            if not can_finish(workflow_obj.pk, self._context['request']):
                raise serializers.ValidationError({
                    'msg': "你无权操作当前工单！"
                })
        ret['workflow_obj'] = workflow_obj
        return ret

    def create(self, validated_data):
        request = self._context['request']
        items = validated_data.copy()
        workflow_obj = items.get('workflow_obj')
        audit_remark = items.get('audit_remark')
        try:
            with transaction.atomic():
                # 将流程状态修改为定时执行
                workflow_obj.work_status = "finish"
                workflow_obj.save()

                # 增加工单日志
                audit_id = detail_by_workflow_id(workflow_obj.id, workflow_obj.work_type).audit_id
                add_log(
                    audit_id=audit_id,
                    operation_type=6,
                    operation_type_desc="结束工单",
                    operation_info="结束备注：{}".format(audit_remark),
                    operator=request.user.username,
                    operator_display=request.user.display_name
                )
                return workflow_obj
        except Exception as f:
            msg = f"结束工单报错，错误信息：{str(f)}"
            return msg


class AddWorkFlowSerializer(serializers.ModelSerializer):

    work_status = serializers.CharField(required=False, read_only=True)
    app_name = serializers.CharField(required=False, read_only=True)
    work_user_display = serializers.CharField(required=False, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = WorkFlow
        fields = ["id", "work_name", "work_user_display", "work_status", "created_at", "app_name",
                  'app_group_id', "work_type", "run_date_start", "run_date_end", "file"]

    @staticmethod
    def validate_app_group_id(value):
        try:
            ResourceGroup.objects.get(pk=value)
        except ResourceGroup.DoesNotExist:
            raise serializers.ValidationError("不可用的业务组ID")
        else:
            return value

    def to_internal_value(self, data):
        ret = super(AddWorkFlowSerializer, self).to_internal_value(data)
        run_date_start = ret.get('run_date_start')
        run_date_end = ret.get('run_date_end')
        if run_date_start and run_date_end and isinstance(run_date_end, datetime) and \
                isinstance(run_date_start, datetime):
            interval = run_date_end - run_date_start
            if (interval.total_seconds() / 60) < 60:
                raise serializers.ValidationError({
                    'msg': "可执行时间范围不应该小于60分钟"
                })

        request = self._context['request']

        if not request.user.is_superuser:
            app_group_id = ret.get('app_group_id')
            app_group_obj = ResourceGroup.objects.get(pk=app_group_id)

            if request.user != app_group_obj.user and not app_group_obj.member.filter(pk=request.user.id):
                raise serializers.ValidationError({
                    'msg': "你不在该业务组，请联系管理员"
                })
        return ret

    def create(self, validated_data):

        request = self._context['request']
        # 调用工作流生成工单
        # 使用事务保持数据一致性
        items = validated_data.copy()
        items['work_user'] = request.user.username
        items['work_user_display'] = request.user.display_name

        app_group_id = validated_data.get('app_group_id')
        app_group_obj = ResourceGroup.objects.get(pk=app_group_id)
        items['app_name'] = app_group_obj.node_paths()
        items['work_status'] = 'manreviewing'
        try:
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
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = WorkflowLog
        fields = ['id', 'operation_info', 'operation_type_desc', 'operator_display', 'created_at']
