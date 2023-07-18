from django.shortcuts import render
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import TemplateView, View, CreateView, DetailView
from .models import WorkFlow, WorkFlowAudit, WorkflowLog
from .utils import get_audit_auth_groups, CommonAudit, can_execute, can_cancel,\
detail_by_workflow_id, auth_group_users, can_timingtask, review_info, can_handle, can_finish
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from mp.apps.models import ResourceGroup
from django.contrib.auth.models import Group
from mp.users.models import MyGroup
# Create your views here.


class Base:

    @staticmethod
    def get_apps_group_list():
        res = []
        rg = ResourceGroup.objects.all()
        for x in rg:
            tmp = (x.id, x.node_paths())
            res.append(tmp)
        return res


class WorkFlowConfigView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """审核流程配置html"""
    # raise_exception = True
    template_name = "workflow/config.html"
    permission_required = ["apps.view_resourcegroup", "workflow.view_workflow",
                           "users.view_mygroup"]

    @staticmethod
    def get_apps_group_list():
        res = []
        rg = ResourceGroup.objects.all()
        for x in rg:
            tmp = (x.id, x.node_paths())
            res.append(tmp)
        return res

    @staticmethod
    def get_group_list():
        return MyGroup.objects.only("id", "name")

    def get_context_data(self, **kwargs):
        kwargs['workflow_type'] = dict(WorkFlow.TYPE)
        kwargs['apps_group_list'] = self.get_apps_group_list()
        kwargs["auth_group_list"] = self.get_group_list()
        return super(WorkFlowConfigView, self).get_context_data(**kwargs)


# 工单提交界面
class AddWorkFlowView(Base, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = ["apps.view_resource_group", "workflow.view_workflow",
                           "workflow.add_workflow"]
    # raise_exception = True
    template_name = "workflow/add.html"

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        perms = self.get_permission_required()
        print(perms)
        return self.request.user.has_perms(perms)

    def get_context_data(self, **kwargs):
        kwargs['workflow_type'] = dict(WorkFlow.TYPE)
        kwargs['apps_group_list'] = self.get_apps_group_list()
        return super(AddWorkFlowView, self).get_context_data(**kwargs)


# 工单列表
class WorkFlowListView(Base, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = ["workflow.view_workflow"]
    raise_exception = True

    template_name = "workflow/list.html"

    @staticmethod
    def get_user():
        return WorkFlow.objects.values_list('work_user', flat=True).distinct()

    def get_context_data(self, **kwargs):
        kwargs['workflow_type'] = dict(WorkFlow.TYPE)
        kwargs['user'] = self.get_user()
        kwargs['apps_group_list'] = self.get_apps_group_list()
        return super(WorkFlowListView, self).get_context_data(**kwargs)


# 工单详情
class WorkFlowDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = ["workflow.view_workflow"]
    model = WorkFlow
    raise_exception = True

    template_name = "workflow/detail.html"

    def get_audit_log(self):
        audit_detail = detail_by_workflow_id(self.object.pk, self.object.work_type)
        audit_id = audit_detail.audit_id   # pk
        last_operation_info = (
            WorkflowLog.objects.filter(audit_id=audit_id).latest('id').operation_info
        )
        if self.object.work_status == "manreviewing":  # 等待审核
            # auth_group_name = MyGroup.objects.get(id=audit_detail.current_audit).name
            current_audit_users = Group.objects.get(id=audit_detail.current_audit).user_set.all()
            # current_audit_users = auth_group_users(
            #     [auth_group_name], audit_detail.app_group_id
            # )
            current_audit_users_display = [
                user.display_name for user in current_audit_users
            ]
            if not current_audit_users_display:
                last_operation_info += "，当前审批人：" + "暂无"
            else:
                last_operation_info += "，当前审批人：" + ",".join(current_audit_users_display)
        return last_operation_info

    def get_context_data(self, **kwargs):

        # 获取当前审批和审批流程
        audit_auth_group, current_audit_auth_group = review_info(self.object.pk,
                                                                 self.object.work_type)

        # 是否可审核 （请求用户如果在当前审核组中则可以审核）
        is_can_review = CommonAudit.cat_review(self.object, self.request)
        # 是否可执行 （定时执行任务立即执行）
        is_can_exec = can_execute(self.object.id, self.request)
        # 是否可定时执行 (自动更新资产信息可以定时执行)
        is_can_timingtask = can_timingtask(self.object.id, self.request)
        # 是否可取消
        is_can_cancel = can_cancel(self.object.id, self.request)

        is_can_finish = can_finish(self.object.id, self.request)
        # 是否可以处理工单
        is_can_handle = can_handle(self.object.id, self.request)
        try:
            last_operation_info = self.get_audit_log()
        except Exception as err:
            print("无审核日志记录，错误信息{e}")
            last_operation_info = ""

        context = {
            'is_can_review': is_can_review,
            'is_can_exec': is_can_exec,
            'is_can_cancel': is_can_cancel,
            'is_can_timingtask': is_can_timingtask,
            'last_operation_info': last_operation_info,
            'audit_auth_group': audit_auth_group,
            'is_can_handle': is_can_handle,
            'is_can_finish': is_can_finish,
            'current_audit_auth_group': current_audit_auth_group

        }
        kwargs.update(context)
        return super(WorkFlowDetailView, self).get_context_data(**kwargs)


class MyAdminView(UserPassesTestMixin):
    """验证是否是管理员"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            self.raise_exception = True
            return False
        elif not self.request.user.is_superuser:
            self.raise_exception = True
            return False
        return True


    # def get_context_data(self, **kwargs):
    #     if self.object.work_status != "autoreviewwrong":  # 审核不通过
    #         # 获取当前审批和审批流程
    #         audit_auth_group, current_audit_auth_group = review_info(self.object.pk,
    #                                                                  self.object.work_type)
    #
    #         # 是否可审核 （请求用户如果在当前审核组中则可以审核）
    #         is_can_review = CommonAudit.cat_review(self.object, self.request)
    #         # 是否可执行
    #         is_can_exec = can_execute(self.object.id, self.request)
    #         # 是否可定时执行 (自动更新资产信息可以定时执行)
    #         is_can_timingtask = can_timingtask(self.object.id, self.request)
    #         # 是否可取消
    #         is_can_cancel = can_cancel(self.object.id, self.request)
    #         try:
    #             last_operation_info = self.get_audit_log()
    #         except Exception as err:
    #             print("无审核日志记录，错误信息{e}")
    #             last_operation_info = ""
    #     else:
    #         audit_auth_group = "申请被驳回"
    #         current_audit_auth_group = "申请被驳回"
    #         is_can_review = False
    #         is_can_exec = False
    #         is_can_timingtask = False
    #         is_can_cancel = False
    #         last_operation_info = None
    #
    #     context = {
    #         'is_can_review': is_can_review,
    #         'is_can_exec': is_can_exec,
    #         'is_can_cancel': is_can_cancel,
    #         'is_can_timingtask': is_can_timingtask,
    #         'last_operation_info': last_operation_info,
    #         'audit_auth_group': audit_auth_group,
    #         'current_audit_auth_group': current_audit_auth_group
    #
    #     }
    #     kwargs.update(context)
    #     return super(WorkFlowDetailView, self).get_context_data(**kwargs)



