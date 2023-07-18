from ansible.plugins.callback import CallbackBase
from .redis_queue import FifoQueue


class ResultsCollectorJSONCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultsCollectorJSONCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result


def AdHoccallback(websocket, background=None):
    if websocket:
        pass

    elif background:
        pass

    else:
        return ResultsCollectorJSONCallback()


class RedisCallBack(CallbackBase):
    def __init__(self, task_id):
        super().__init__()
        self.server = FifoQueue(task_id)

    def _write_to_save(self, data):
        # msg = json.dumps(data, ensure_ascii=False)
        self.server.push(data)

    def v2_playbook_on_start(self, playbook, *k, **kw):
        print('v2_playbook_on_start', playbook.__dict__)

    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host
        self._write_to_save({
            "host": host.get_name(),
            "result": result._result,
            "task": result.task_name,
            "status": "success"
        })

    def v2_runner_on_failed(self, result, ignore_errors=False, *k, **kwargs):    # 执行失败
        """处理执行失败的任务，有些任务失败会被忽略，所有有两种状态"""
        host = result._host
        if ignore_errors:
            status = "ignoring"
        else:
            status = 'failed'
        self._write_to_save({
                "host": host.get_name(),
                "result": result._result,
                "task": result.task_name,
                "status": status
            })

    def v2_runner_on_skipped(self, result, *args, **kwargs):    # 任务跳过
        """处理跳过的任务"""
        self._write_to_save({
                "host": result._host.get_name(),
                "result": result._result,
                "task": result.task_name,
                "status": "skipped"}
            )

    def v2_runner_on_unreachable(self, result, **kwargs):   ##  主机不可达
        """处理主机不可达的任务"""
        self._write_to_save({
                "host": result._host.get_name(),
                "status": "unreachable",
                "task": result.task_name,
                "result": result._result}
        )
