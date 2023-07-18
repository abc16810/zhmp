from django_q.tasks import schedule
from django_q.models import Schedule
import logging


logger = logging.getLogger("root")


def add_workflow_schedule(name, run_date, workflow_obj):
    """添加/修改定时任务"""
    del_schedule(name)
    app_group_id = workflow_obj.app_group_id
    schedule(
        "mp.common.exec_workflow.ansible_batch_update_by_apps",
        app_group_id,
        name=name,
        schedule_type=Schedule.ONCE,
        next_run=run_date,
        timeout=-1,
        pk=workflow_obj.id,
        work_type=workflow_obj.work_type
    )
    logger.info(f"添加ansible定时执行任务：{name} 执行时间：{run_date}")


def del_schedule(name):
    """删除schedule"""
    try:
        sql_schedule = Schedule.objects.get(name=name)
        Schedule.delete(sql_schedule)
        logger.info(f"删除schedule：{name}")
    except Schedule.DoesNotExist:
        pass





