import datetime

from django.db import transaction
from django_q.conf import logger
from django_q.tasks import async_task

from mp.apps.models import ResourceGroup
from mp.common.ansible.api_29 import ansibleexecapi29
from mp.workflow.models import WorkFlow
from mp.workflow.utils import detail_by_workflow_id, add_log


def get_assets(app_group_id):
    """
    通过业务组获取server资产
    :param app_group_id:
    :return: list
    """
    data = []
    try:
        obj = ResourceGroup.objects.get(id=app_group_id)
        app_list = obj.apps.all()

        for app in app_list:
            assets = app.assets.all()
            for asset in assets:
                if asset.assets.assets_type in ["server", "vmser"]:
                    an = asset.to_ansible
                    if an.get('has_user'):
                        data.append(an)
                    else:
                        logger.warning("%s 资产没有关联管理用户，忽略" % asset)
                else:
                    logger.warning('%s 资产类型不支持，忽略' % asset)
        if not data:
            raise Exception("没有资产")
        else:
            return data
    except ResourceGroup.DoesNotExist:
        raise Exception("业务组不存在")


def ansible_batch_update_by_apps(apps_id, **kwargs):
    """
    :param apps_id: int
    :param kwargs
    :return:
    """
    workflow_id = kwargs.get('pk')
    work_type = kwargs.get('work_type')
    audit_id = detail_by_workflow_id(workflow_id, work_type).audit_id
    user = kwargs.get('user', None)
    # 使用当前读防止重复执行
    with transaction.atomic():
        workflow_detail = WorkFlow.objects.select_for_update().get(id=workflow_id)
        # 只有排队中和定时执行的数据才可以继续执行，否则直接抛错
        if workflow_detail.work_status not in ["queuing", "timingtask"]:
            operation_info = "工单状态不正确，禁止执行！"
            raise Exception(operation_info)
        # 将工单状态修改为执行中
        else:
            WorkFlow(id=workflow_id, work_status="executing").save(
                update_fields=["work_status"]
            )

    add_log(
        audit_id=audit_id,
        operation_type=5,
        operation_type_desc="执行工单",
        operation_info="工单开始执行" if user else "系统定时执行工单",
        operator=user.username if user else "",
        operator_display=user.display_name if user else "系统",
    )

    inventory = []

    try:
        inventory = get_assets(apps_id)
    except Exception as f:
        logger.error(f)

    if inventory:
        taskid = "Ansible_Workflow_%s_%s" % (workflow_id, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        async_task('mp.common.exec_workflow.ansible_batch_update',
                   inventory, taskid, workflow_id,
                   hook="mp.common.exec_workflow.get_result"
                   )
    else:
        add_log(
            audit_id=audit_id,
            operation_type=6,
            operation_type_desc="执行结束",
            operation_info="资产为空,结束工单",
            operator=user.username if user else "",
            operator_display=user.display_name if user else "系统",
        )
        WorkFlow(id=workflow_id, work_status="finish").save(
            update_fields=["work_status"]
        )


def ansible_batch_update(inventory, taskid, workflow_id):
    """
    :param inventory: [{},{}]
    :param taskid: str
    :param workflow_id: int
    :return:
    """
    if inventory:
        if not taskid:
            taskid = "Ansible_Batch_Setup_%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # 异步执行ansibel api 需要如下配置
        import multiprocessing
        current_process = multiprocessing.current_process
        current_process()._config['daemon'] = False

        logger.info("开始执行 ansible 批量任务")
        ansibleexecapi29(taskid, 'setup', "", inventory_data=inventory)
    else:
        logger.error("资产为空，忽略")
    return taskid


def get_result(task):
    logger.info("开始执行 ansible setup 批量任务的回调函数")

    workflow_id = task.args[2]
    taskid = task.result
    # 判断工单状态，如果不是执行中的，不允许更新信息，直接抛错记录日志
    if workflow_id:
        with transaction.atomic():
            workflow = WorkFlow.objects.get(id=workflow_id)
            if workflow.work_status != "executing":
                raise Exception(f"工单{workflow.id}状态不正确，禁止重复更新执行结果！")
        workflow.finish_time = task.stopped

        if not task.success:
            workflow.work_status = 'exception'
        else:
            workflow.work_status = 'finish'
        workflow.save()
        # 增加工单日志
        audit_id = detail_by_workflow_id(
            workflow_id=workflow_id, workflow_type=0
        ).audit_id
        add_log(
            audit_id=audit_id,
            operation_type=6,
            operation_type_desc="执行结束",
            operation_info="执行ID：{}".format(taskid),
            operator="",
            operator_display="系统",
        )
    if task.success:
        async_task('mp.assets.tasks.ansible_batch_setup_to_save_db',
                   task.result, is_mem=False)
    else:
        logger.error("%s 任务执行失败" % task)




