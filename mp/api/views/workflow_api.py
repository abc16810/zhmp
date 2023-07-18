from rest_framework.response import Response
from rest_framework.views import APIView
from mp.workflow.models import WorkFlow, WorkflowAuditLog, WorkflowLog, WorkFlowAudit
from mp.workflow.utils import get_audit_auth_groups
from mp.apps.models import ResourceGroup
from mp.api.utils import CustomObjectPermissions
from mp.users.models import MyGroup
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView
import mp.api.workflow_serializers as serializers
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import mixins
from rest_framework import generics
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.parsers import FileUploadParser
from django.urls import reverse
import logging


logger = logging.getLogger('root')


class AppsGroupAuditors(APIView):
    """
    获取业务组审核
    """
    permission_classes = [CustomObjectPermissions]

    def get_queryset(self):
        return WorkFlow.objects.all()

    def post(self, request, format=None):
        result = {
            "status": 0,
            "msg": "ok",
            "data": {"auditors": "", "auditors_display": ""},
        }
        apps_group_id = request.POST.get('id')
        workflow_type = request.POST.get('workflow_type')
        try:
            rg_obj = ResourceGroup.objects.get(pk=int(apps_group_id))
        except ValueError or ResourceGroup.DoesNotExist:
            result["msg"] = "未知错误"
            result["status"] = 1
            return Response(result, status=200)

        audit_auth_groups = get_audit_auth_groups(apps_group_id, workflow_type)
        if audit_auth_groups:
            for auth_group_id in audit_auth_groups.split(","):
                try:
                    MyGroup.objects.get(id=auth_group_id)
                except MyGroup.DoesNotExist or ValueError:
                    result["status"] = 1
                    result["msg"] = "审批流程权限组不存在，请重新配置！"
                    return Response(result, status=200)
            audit_auth_groups_name = "->".join(
                [
                    MyGroup.objects.get(id=auth_group_id).name
                    for auth_group_id in audit_auth_groups.split(",")
                ]
            )
            result["data"]["auditors"] = audit_auth_groups
            result["data"]["auditors_display"] = audit_auth_groups_name

        return Response(result, status=200)


class AppGroupAuditorsChangeOrCreate(CreateAPIView):
    """
    增加/修改不同类型工作流下的业务组审核人
    """
    serializer_class = serializers.AppsGroupAuditorsSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlowAudit.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        result = {"status": 0, "msg": "ok", "data": []}
        if serializer.is_valid():
            serializer.save()
            return Response(result, status=200)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddWorkFlow(CreateAPIView):
    """
    增加工单/工单列表
    """
    serializer_class = serializers.AddWorkFlowSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()
    renderer_classes = [JSONRenderer]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            logging.warning('类型错误 %s' % f)
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数或者非法类型或者上传空文件'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            instance = serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)

        res = self.get_success_headers(instance)
        return Response(res, status=status.HTTP_201_CREATED)

        # return HttpResponseRedirect(reverse("workflow-detail", kwargs={"pk": instance.pk}))

    def get_success_headers(self, instance):
        try:
            return {'Location': reverse("workflow-detail", kwargs={"pk": instance.pk})}
        except (TypeError, KeyError):
            return {'Location': '/'}


class WorkFlowPassed(CreateAPIView):
    """
    工单审核通过
    """
    serializer_class = serializers.WorkFlowPassedSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)
        return Response({"detail": "审核成功"}, status=status.HTTP_201_CREATED)


class WorkFlowCancel(CreateAPIView):
    """
    工单终止(审核不通过/审核取消)
    """
    serializer_class = serializers.WorkFlowCancelSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)
        return Response({"detail": "终止成功"}, status=status.HTTP_201_CREATED)


class WorkFlowTiming(CreateAPIView):
    """
    定时更新
    """
    serializer_class = serializers.WorkFlowtimingSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)
        return Response({"detail": "定时成功"}, status=status.HTTP_201_CREATED)


class WorkFlowExec(CreateAPIView):
    """
    立即更新
    """
    serializer_class = serializers.WorkFlowExecSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)
        return Response({"detail": "执行成功"}, status=status.HTTP_201_CREATED)


class WorkFlowhandler(CreateAPIView):
    """
    处理其它类型的工单
    """
    serializer_class = serializers.WorkFlowHandlerSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)
        return Response({"detail": "执行成功"}, status=status.HTTP_201_CREATED)


class WorkFlowFinish(CreateAPIView):
    """
    工单结束
    """
    serializer_class = serializers.WorkFlowFinishSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数'}
            return Response(res, status=status.HTTP_201_CREATED)
        try:
            serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED)
        return Response({"detail": "结束成功"}, status=status.HTTP_201_CREATED)


class WorkFlowList(ListAPIView):
    """
    工单列表
    """
    serializer_class = serializers.AddWorkFlowSerializer
    permission_classes = [CustomObjectPermissions]
    # queryset = WorkFlow.objects.all()
    ordering = ("-created_at",)  # 指定默认排序字段
    # renderer_classes = [JSONRenderer]
    search_fields = ['work_name']
    filterset_fields = ['work_type', 'work_user', 'app_group_id']

    def get_queryset(self):
        if self.request.user.is_superuser:
            q = WorkFlow.objects.all()
        else:
            q = WorkFlow.objects.filter(work_user=self.request.user.username)
        return q


class WorkFlowLog(ListAPIView):
    """
    工单审批日志
    """
    serializer_class = serializers.WorkFlowLogListSerializer
    permission_classes = [CustomObjectPermissions]
    filter_backends = []
    lookup_field = 'pk'

    def get_queryset(self):
        workflow_id = self.request.query_params.get('workflow_id', '')
        workflow_type = self.request.query_params.get('workflow_type', '')
        try:
            audit_id = WorkflowAuditLog.objects.get(
                workflow_id=int(workflow_id), workflow_type=int(workflow_type)
            ).audit_id
            queryset = WorkflowLog.objects.filter(audit_id=audit_id)
        except Exception as f:
            queryset = WorkflowLog.objects.all()
        return queryset
