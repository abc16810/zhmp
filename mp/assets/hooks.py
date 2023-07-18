from django_q.conf import logger
from django_q.tasks import async_task


def get_result(task):
    logger.info("开始执行ansible setup 批量任务的回调函数")
    logger.info(task)
    if task.success:
        async_task('mp.assets.tasks.ansible_batch_setup_to_save_db',
                   task.result, is_mem=False)
    else:
        logger.error("%s 任务执行失败" % task)


def get_mem_result(task):
    logger.info("开始执行ansible get_memory批量任务的回调函数")
    if task.success:
        async_task('mp.assets.tasks.ansible_batch_setup_to_save_db',
                   task.result, is_mem=True)
    else:
        logger.error("%s 任务执行失败" % task)
