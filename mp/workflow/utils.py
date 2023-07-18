from mp.workflow.models import WorkFlowAudit, WorkflowAuditLog, WorkflowLog, WorkFlow
# from sites.users.models import MyGroup
from django.contrib.auth.models import Group
from django.db import transaction
from mp.apps.models import ResourceGroup


def get_audit_auth_groups(apps_group_id, workflow_type):
    """
    通过业务组ID和工作流类型获取审核组
    :param apps_group_id:
    :param workflow_type:
    :return:
    """
    try:
        return WorkFlowAudit.objects.get(
            workflow_type=workflow_type, apps_group_id=apps_group_id
        ).audit_auth_groups
    except WorkFlowAudit.DoesNotExist:
        return None


# 通过业务id获取审核信息
def detail_by_workflow_id(workflow_id, workflow_type):
    try:
        return WorkflowAuditLog.objects.get(
            workflow_id=workflow_id, workflow_type=workflow_type
        )
    except WorkflowAuditLog.DoesNotExist:
        return None


# 操作流程日志
def add_log(
        audit_id,
        operation_type,
        operation_type_desc,
        operation_info,
        operator,
        operator_display,
):
    """
    :param audit_id:  工单审计ID
    :param operation_type:
    :param operation_type_desc:
    :param operation_info:
    :param operator:
    :param operator_display:
    :return:
    """
    WorkflowLog(
        audit_id=audit_id,
        operation_type=operation_type,
        operation_type_desc=operation_type_desc,
        operation_info=operation_info,
        operator=operator,
        operator_display=operator_display,
    ).save()


# 获取当前工单审批流程和当前审核组
def review_info(workflow_id, workflow_type):
    audit_info = WorkflowAuditLog.objects.get(
        workflow_id=workflow_id, workflow_type=workflow_type
    )
    if not audit_info.audit_auth_groups:
        audit_auth_group = "无需审批"
    else:
        try:
            group_ids = audit_info.audit_auth_groups.split(",")
            g = Group.objects.filter(id__in=[2,1]).values_list('id', 'name')
            g_d = dict(g)
            tmp = []
            for x in group_ids:
                tmp.append(g_d.get(int(x)))
            # audit_auth_group = "->".join([name[0] for name in Group.objects.filter(id__in=group_ids).values_list("name")])
            audit_auth_group = '->'.join(tmp)
        except Exception:
            audit_auth_group = audit_info.audit_auth_groups
    if audit_info.current_audit == "-1":
        current_audit_auth_group = None
    else:
        try:
            current_audit_auth_group = Group.objects.get(
                    id=audit_info.current_audit
                ).name
        except Group.DoesNotExist:
            current_audit_auth_group = audit_info.current_audit
    return audit_auth_group, current_audit_auth_group


def auth_group_users(auth_group_names, app_group_id):
    """
    获取资源组内关联成员或者负责人
    :param auth_group_names:
    :param app_group_id:
    :return:
    """
    # 获取资源组关联的用户
    users = ResourceGroup.objects.get(pk=app_group_id).user.all()
    # 过滤在该权限组中的用户
    users = users.filter(groups__name__in=auth_group_names, is_active=1)
    return users


def user_groups(user):
    """
    获取用户关联资源组列表
    :param user:
    :return:
    """
    if user.is_superuser:
        group_list = [group for group in ResourceGroup.objects.filter(is_deleted=0)]
    else:
        group_list = [group for group in ResourceGroup.objects.filter(is_deleted=0).filter(user=user)]
    return group_list


def can_handle(workflow_id, request):
    """
    认领工单  目前只允许管理员
    :param workflow_id: 工单ID
    :param request:
    :return: bool
    """
    result = False
    workflow_detail = WorkFlow.objects.get(id=workflow_id)
    if workflow_detail.work_status == "review_pass" and workflow_detail.work_type != 0:
        if request.user.is_superuser:
            result = True
    return result


def can_execute(workflow_id, request):
    """
    判断用户当前是否可立即执行，两种情况下用户有执行权限
    1.登录用户为管理员
    2.当前登录用户为提交人
    :param workflow_id:  工单ID
    :param request:
    :return: bool
    """
    result = False
    # 保证工单当前是可执行状态
    with transaction.atomic():
        workflow_detail = WorkFlow.objects.select_for_update().get(id=workflow_id)

        # 只有审核通过和定时执行的数据才可以立即执行
        if workflow_detail.work_status not in [
            "review_pass",
            "timingtask",
            "queuing"
        ]:
            return False

    if workflow_detail.work_type == 0:
        # 管理员可以执行
        if request.user.is_superuser:
            result = True
        # 当前登录用户为提交人，并且有执行权限
        if workflow_detail.work_user == request.user.username:
            result = True
    return result


def can_cancel(workflow_id, request):
    """
    判断用户当前是否是可终止（取消工单/审核不通过），
    等待审核的提交人可终止
    :param workflow_id: 工单ID
    :param request:
    :return: bool
    """
    result = False
    workflow_detail = WorkFlow.objects.get(id=workflow_id)
    # 审核中的工单，审核人和提交人可终止
    if workflow_detail.work_status == "manreviewing":  # 等待审核可以取消
        # 管理员可以取消
        if request.user.is_superuser:
            return True
        # 发起人可以取消/审核人可以取消
        return any(
            [
                request.user.username == workflow_detail.work_user,
                CommonAudit.cat_review(workflow_detail, request)

            ]
        )
    if workflow_detail.work_status in ["timingtask"]:
        # 管理员可以取消
        if request.user.is_superuser:
            return True
    # 审核通过或者定时执行状态 申请人可以终止
    # elif workflow_detail.work_status in ["review_pass", "timingtask"]:
    #     if request.user.is_superuser:
    #         return True
    #     else:
    #         return request.user.username == workflow_detail.work_user
    return result


def can_finish(workflow_id, request):
    """
    正常结束
    :param workflow_id:
    :param request:
    :return: Bool
    """
    result = False
    workflow_obj = WorkFlow.objects.get(id=workflow_id)
    if workflow_obj.work_type != 0 and workflow_obj.work_status == 'executing':
        if request.user.is_superuser:
            result = True
    return result


def can_timingtask(workflow_id, request):
    """
    判断用户当前是否可定时执行，两种情况下用户有定时执行权限
    1.登录用户为管理员
    2.当前登录用户为提交人
    :param workflow_id: 工单ID
    :param request
    :return: bool
    """
    workflow_detail = WorkFlow.objects.get(id=workflow_id)
    if workflow_detail.work_type == 0 and workflow_detail.work_status in ["review_pass", "timingtask"]:
    # if workflow_detail.work_status in ["review_pass", "timingtask"]:
        if request.user.is_superuser:
            return True
        return request.user.username == workflow_detail.work_user
    return False


class CommonAudit(object):
    """
    # 新增工单审核 及日志记录
    """
    @staticmethod
    def add(work_obj, request, app_group_id):
        """
        :param work_obj: 工单obj
        :param request:
        :param app_group_id:  业务组ID
        :return:
        """
        # 检查是否已存在待审核数据
        workflow_id = work_obj.pk
        workflow_info = WorkflowAuditLog.objects.filter(
            workflow_type=work_obj.work_type,
            workflow_id=workflow_id,
            current_status=0,
        )
        if len(workflow_info) >= 1:
            msg = "该工单当前状态为待审核，请勿重复提交"
            raise Exception(msg)
        audit_auth_groups = get_audit_auth_groups(app_group_id, work_obj.work_type)
        app_group_id = work_obj.app_group_id
        app_group_name = work_obj.app_name
        workflow_remark = ""

        # 校验是否配置审批流程
        if not audit_auth_groups:
            msg = "审批流程不能为空，请先配置审批流程"
            raise Exception(msg)
        else:
            audit_auth_groups_list = audit_auth_groups.split(",")

        # 管理员无需审批
        if request.user.is_superuser:
            work_obj.work_status = "review_pass"
            work_obj.save()
            workflow_remark = "管理员申请，无需审核"
            audit_auth_groups_list = None

        res = {
            "app_group_id": app_group_id,
            "app_group_name": app_group_name,
            "workflow_id": workflow_id,   # 工单ID
            "workflow_type": work_obj.work_type,
            "workflow_title": work_obj.work_name,
            "workflow_remark": workflow_remark,
            "create_user": request.user.username,
            "create_user_display": request.user.display_name
        }
        if audit_auth_groups_list is None:
            operation_type = 1
            # 向审核主表插入审核通过的数据
            res['audit_auth_groups'] = ""   # 审批权限组列表
            res['current_audit'] = "-1"   # 当前审批权限组ID
            res['next_audit'] = "-1"   # 下级审批权限组ID
            res['current_status'] = operation_type  # 审核状态 (审核通过)
            audit_detail = WorkflowAuditLog.objects.create(**res)
            operation_info = "无需审批，管理员申请系统直接审核通过"
        else:
            operation_type = 0
            res['audit_auth_groups'] = ",".join(audit_auth_groups_list)
            res['current_audit'] = audit_auth_groups_list[0]
            # 判断有无下级审核
            if len(audit_auth_groups_list) == 1:
                next_audit = "-1"
            else:
                next_audit = audit_auth_groups_list[1]
            res['next_audit'] = next_audit
            res['current_status'] = operation_type  # 等待审核
            audit_detail = WorkflowAuditLog.objects.create(**res)

            audit_auth_group, current_audit_auth_group = review_info(
                audit_detail.workflow_id, audit_detail.workflow_type
            )
            operation_info = "等待审批，审批流程：%s" % audit_auth_group
        add_log(audit_id=audit_detail.pk, operation_type=operation_type,
                operation_type_desc="提交工单",
                operation_info=operation_info,
                operator=audit_detail.create_user,
                operator_display=audit_detail.create_user_display)

    @staticmethod
    def audit_pass(audit_id, request, audit_remark):
        """
        工单审核通过
        :param audit_id: 工作流审核状态ID
        :param request:
        :param audit_remark: 审核备注
        :return:
        """
        audit_detail = WorkflowAuditLog.objects.get(audit_id=audit_id)
        if audit_detail.current_status != 0:
            msg = "工单不是待审核状态，请返回刷新"
            raise Exception(msg)
        # 判断是否还有下一级审核
        if audit_detail.next_audit == "-1":
            # 更新主表审核状态为审核通过
            audit_result = WorkflowAuditLog()
            audit_result.audit_id = audit_id
            audit_result.current_audit = "-1"
            audit_result.current_status = 1  # 审核通过
            audit_result.save(update_fields=["current_audit", "current_status"])
        else:
            # 更新主表审核下级审核组和当前审核组
            audit_result = WorkflowAuditLog()
            audit_result.audit_id = audit_id
            audit_result.current_status = 0  # 待审核
            audit_result.current_audit = audit_detail.next_audit
            # 判断后续是否还有下下一级审核组
            audit_auth_groups_list = audit_detail.audit_auth_groups.split(",")
            for index, auth_group in enumerate(audit_auth_groups_list):
                if auth_group == audit_detail.next_audit:
                    # 无下下级审核组
                    if index == len(audit_auth_groups_list) - 1:
                        audit_result.next_audit = "-1"
                        break
                    # 存在下下级审核组
                    else:
                        audit_result.next_audit = audit_auth_groups_list[index + 1]
            audit_result.save(
                update_fields=["current_audit", "next_audit", "current_status"]
            )

        # 增加工单日志
        audit_auth_group, current_audit_auth_group = review_info(
            audit_detail.workflow_id, audit_detail.workflow_type
        )
        operation_info = "审批备注：{}，下级审批：{}".format(audit_remark, current_audit_auth_group)
        add_log(audit_id=audit_detail.pk,
                operation_type=1,
                operation_type_desc="审批通过",
                operation_info=operation_info,
                operator=request.user.username,
                operator_display=request.user.display_name)

        # 返回审核结果
        return audit_result.current_status

    @staticmethod
    def audit_abort_reject(audit_id, request, audit_status, audit_remark):
        """
        工单取消（申请人取消工单）
        工单终止 (审核人或者管理员终止)
        :param audit_id: 工作流审核状态ID
        :param request:
        :param audit_status: 状态
        :param audit_remark:  备注
        :return:
        """
        audit_detail = WorkflowAuditLog.objects.get(audit_id=audit_id)

        if audit_detail.current_status != 0:
            msg = "工单不是待审核状态，请返回刷新"
            raise Exception(msg)

        # 更新主表审核状态
        audit_result = WorkflowAuditLog()
        audit_result.audit_id = audit_id
        audit_result.next_audit = "-1"
        audit_result.current_status = audit_status
        if audit_status == 2:
            audit_result.current_audit = "-1"
            audit_result.save(
                update_fields=["current_audit", "next_audit", "current_status"]
            )
            operation_type_desc = "审批不通过"
            operation_info = "审批备注：{}".format(audit_remark)
        if audit_status == 3:
            audit_result.save(update_fields=["current_status", "next_audit"])
            operation_type_desc = "审批取消"
            operation_info = "取消原因：{}".format(audit_remark)

        add_log(
            audit_id=audit_id,
            operation_type=audit_status,
            operation_type_desc=operation_type_desc,
            operation_info=operation_info,
            operator=request.user.username,
            operator_display=request.user.display_name
        )

        return audit_detail.current_status

    @staticmethod
    def cat_review(work_obj, request):
        """
        审批权限组中的成员可以审核
        :param work_obj: 工单obj
        :param request:
        :return: bool
        """
        app_group_id = work_obj.app_group_id
        user = request.user
        result = False

        try:
            audit_info = WorkflowAuditLog.objects.get(
                workflow_id=work_obj.pk, workflow_type=work_obj.work_type
            )
            if audit_info.current_status == 0:  # 待审核
                if user.is_superuser:
                    result = True
                auth_group_id = audit_info.current_audit
                # 请求用户如果在当前审核组中则可以审核
                if Group.objects.get(id=auth_group_id).user_set.filter(id=user.id).exists():
                    result = True
                # audit_auth_group = Group.objects.get(id=auth_group_id).name
                # if auth_group_users([audit_auth_group], app_group_id).filter(id=user.id).exists():
                #     result = True
        except Exception as err:
            print(err)
        return result







