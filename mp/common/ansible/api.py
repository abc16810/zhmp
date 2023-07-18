# -*- coding: utf-8 -*
import ansible.constants as C
import shutil
from ansible import context
from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.utils.vars import load_options_vars
from ansible.vars.manager import VariableManager
import json
from .callback import AdHoccallback
from .inventory import get_inventory

C.HOST_KEY_CHECKING = False  # 关闭第一次使用ansible连接客户端时输入确认命令



context.CLIARGS = ImmutableDict(
    syntax=False,
    connection='smart',  # smart ssh
    module_path='',
    forks=C.DEFAULT_FORKS,  # 默认线程5
    timeout=C.DEFAULT_TIMEOUT,  # 默认10s
    remote_user=C.DEFAULT_REMOTE_USER,  # 远程用户默认''
    private_key_file=None,
    ssh_common_args="",
    ssh_extra_args="",
    sftp_extra_args="",
    scp_extra_args="",
    become=None,
    become_method=None,
    become_user=None,
    verbosity=0,
    check=False,
    extra_vars=[],
    playbook_path='/etc/ansible/',
    passwords=None,
    diff=False,
    gathering='implicit',
    remote_tmp='/tmp/.ansible',
    listtags=False,
    listtasks=False,
    listhosts=False,
    start_at_task=None,
)


class ANSRunner(object):
    """ansible runner"""

    def __init__(self, inventory,
                 passwords=None,
                 websocket=None,
                 background=None,
                 **kwargs):
        """
        :param kwargs:  重新定义 options里的值
        """
        if kwargs:
            context.CLIARGS = context.CLIARGS.union(kwargs)

        self.loader = DataLoader()
        self.inventory = get_inventory(inventory)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.variable_manager._options_vars = load_options_vars('6.0.0')
        self.websocket = websocket
        self.background = background
        self.passwords = passwords or {}
        self.results_raw = {}

    @staticmethod
    def check_module_args(module_name, module_args=''):
        if module_name in C.MODULE_REQUIRE_ARGS and not module_args:
            err = "No argument passed to '%s' module." % module_name
            raise AnsibleError(err)

    def check_pattern(self, pattern):
        if not pattern:
            msg = "[Pattern] or [Host list] `{}` is not valid!".format(pattern)
            raise AnsibleError(msg)
        if not self.inventory.list_hosts("all"):
            msg = "Inventory is empty."
            raise AnsibleError(msg)
        if isinstance(pattern, str) and not self.inventory.list_hosts(pattern):
            msg = 'pattern: %s  dose not match any hosts.' % pattern
            raise AnsibleError(msg)

    def run_model(self, host_list, module_name, module_args, gather_facts='no'):
        """运行模块
        {'action': {'module': 'debug', 'args': {'msg': '{{shell_out.stdout}}'}}}
        tasks = [dict(action=dict(module='shell', args='ls'), register='shell_out'),]
        :params tasks:  [{'action': {'module': 'shell', 'args': 'ls'}, 'register': 'shell_out'} ...]
        :host_list: 主机列表或者组名称如'all'
        """
        self.check_module_args(module_name, module_args)
        self.check_pattern(host_list)
        self.callback = AdHoccallback(self.websocket, self.background)
        play_source = dict(
            name="Ansible Ad-hoc",
            hosts=host_list,
            gather_facts=gather_facts,
            tasks=[dict(action=dict(module=module_name, args=module_args))]
        )
        play = Play().load(play_source, loader=self.loader, variable_manager=self.variable_manager)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                passwords=self.passwords,
                stdout_callback=self.callback
            )
            tqm._stdout_callback = self.callback
            tqm.run(play)
        except Exception as err:
            # logger.error(msg="run model failed: {err}".format(err=str(err)))
            if self.websocket:self.websocket.send(str(err))
        finally:
            if tqm is not None:
                tqm.cleanup()
            if self.loader:
                self.loader.cleanup_all_tmp_files()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    def get_model_result(self):
        self.results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}

        for host, result in self.callback.host_ok.items():
            self.results_raw['success'][host] = result._result

        for host, result in self.callback.host_failed.items():
            self.results_raw['failed'][host] = result._result

        for host, result in self.callback.host_unreachable.items():
            self.results_raw['unreachable'][host] = result._result

        return json.dumps(self.results_raw, indent=4)

    def get_result(self, value, module_name, args=None, failed=False, success=False, unreachable=False):
        data_list = []
        for ip, value in value.items():
            res = {'args': args, 'status': None, 'module_name': module_name, 'ip': ip}
            if failed:
                res['status'] = 'failed'
                try:
                    res['msg'] = value.get('stdout').strip() or value.get('msg')
                except:
                    res['msg'] = None
                if value.get('rc') == 0:
                    res['status'] = 'succeed'
            if success:
                res['status'] = 'succeed'
                try:
                    res['msg'] = value.get('stdout_lines')
                except:
                    res['msg'] = None
                if value.get('rc') != 0:
                    res['status'] = 'failed'
            if unreachable:
                res['status'] = 'unreachable'
                res['msg'] = value.get('msg')
            data_list.append(res)
        return data_list

    def handle_model_data(self, data, module_name, module_args=None):
        """
        处理 raw,command,script,shell 等模块
        :param data:
        :param module_name:
        :param module_args:
        :return:
        """
        module_data = json.loads(data)
        failed = module_data.get('failed')
        success = module_data.get('success')
        unreachable = module_data.get('unreachable')
        data_list = []
        if module_name in ["raw", "shell", "script", "command"]:
            if failed:
                res = self.get_result(failed, module_name, failed=True, args=module_args)
                data_list.extend(res)
            if success:
                res = self.get_result(success, module_name, success=True, args=module_args)
                data_list.extend(res)
            if unreachable:
                res = self.get_result(unreachable, module_name, unreachable=True, args=module_args)
                data_list.extend(res)
        elif module_name == 'ping':
            if success:
                for ip, value in success.items():
                    res = {'args': module_args, 'status': None, 'module_name': module_name, 'ip': ip}
                    if y.get('ping') == 'pong':
                        data['msg'] = value.get('ping')
                        data['status'] = 'succeed'
                    else:
                        data['status'] = 'failed'
                    data_list.append(data)
        return data_list

    @staticmethod
    def handle_setup_data(data):
        """
        处理setup返回结果方法
        :param data: '{}'
        :return: dict
        """
        data_list = []
        for k, v in json.loads(data).items():
            if k == 'success':
                for key, value in v.items():
                    base_info = {}
                    info = value.get('ansible_facts')
                    # cpu
                    cpu_vendor = info['ansible_processor'][-1]
                    base_info['cpu_number'] = info['ansible_processor_count']
                    base_info['vcpu_number'] = info['ansible_processor_vcpus']
                    base_info['cpu_core'] = info['ansible_processor_cores']

                    # 序列号SN
                    base_info['sn'] = info['ansible_product_serial']
                    # 制造商
                    base_info['manufacturer'] = info.get('ansible_system_vendor')
                    # 型号
                    base_info['model'] = info.get('ansible_product_name').split(':')[0]
                    # 版本
                    base_info['version'] = info.get('ansible_product_version')

                    # 平台
                    base_info['platform'] = info.get('ansible_system')
                    # 系统
                    base_info['s_os'] = info.get('ansible_distribution')
                    # 系统版本
                    base_info['os_version'] = info.get('ansible_distribution_version')
                    # 架构
                    base_info['os_arch'] = info.get('ansible_architecture')
                    # 内核
                    base_info['kernel'] = info.get('ansible_kernel')

                    # 主机名
                    base_info['s_hostname_raw'] = info.get('ansible_hostname')

                    # 内存
                    base_info['ram_total'] = int(info['ansible_memtotal_mb'])   # MB

                    disk_sizes = 0
                    all_disk = []
                    for dev, dev_info in info['ansible_devices'].items():
                        disk_info = {}
                        if dev[0:2] in ['sd', 'hd', 'ss', 'vd']:
                            disk_info['name'] = dev
                            disk_size = float(dev_info.get('size').split()[0]) or int(
                                (int(dev_info.get('sectors')) *
                                 int(dev_info.get('sectorsize', 512))) / 1024 / 1024 / 1024.0)
                            disk_sizes = disk_size + disk_sizes
                            disk_info['device_size'] = disk_size
                            disk_info['host'] = dev_info.get('host', '')
                            disk_info['device_model'] = dev_info.get('model')
                            disk_info['device_vendor'] = dev_info.get('vendor')
                            disk_info['partitions'] = dev_info.get('partitions', {})
                            disk_info['wwn'] = dev_info.get('wwn') or dev_info.get('serial')
                            # links = dev_info['links'].get('ids', [])
                            # disk_info['links_name'] = ' '.join([link for link in links if not link.startswith('wwn')])
                            all_disk.append(disk_info)
                    base_info['disk'] = all_disk
                    base_info['disk_total'] = int(disk_sizes)

                    all_nic = []
                    nic_info = info['ansible_interfaces']
                    default_nic = info['ansible_default_ipv4']
                    for nic in nic_info:
                        if nic == "lo" or nic.startswith('br-') or nic == 'docker0' or nic.startswith('veth'):
                            continue
                        nic_items = {}
                        net = 'ansible_' + nic
                        nic_data = info.get(net)
                        nic_items['name'] = nic
                        nic_items['mac'] = nic_data.get('macaddress')
                        nic_items['active'] = nic_data.get('active')
                        nic_items['promisc'] = nic_data.get('promisc')
                        nic_items['types'] = nic_data.get('type', '')
                        nic_items['speed'] = nic_data.get('speed')
                        nic_items['module'] = nic_data.get('module')
                        if nic_data.get('ipv4'):
                            nic_items['ip'] = nic_data['ipv4'].get('address', '')
                            nic_items['netmask'] = nic_data['ipv4'].get('netmask', '')

                        if nic_items.get('ip') and nic_items['ip'] == default_nic.get('address'):
                            nic_items['gateway'] = default_nic['gateway']
                            nic_items['is_ipv4_default'] = True
                        all_nic.append(nic_items)
                    base_info['nic'] = all_nic
                    base_info['status'] = 0
                    base_info['ip'] = key
                    data_list.append(base_info)
            elif k == 'failed' or k == 'unreachable':
                for key, value in v.items():
                    base_info = {'status': 1, 'ip': key, 'msg': value.get('msg')}
                    data_list.append(base_info)
        return data_list


if __name__ == '__main__':
    inventory = [
           {"hostname": "10.4.56.108", 'ip': '10.4.56.108', 'username': 'zh', 'password': 'MP52!Hcm'},
           {"hostname": "10.4.56.11", 'ip': '10.4.56.11', 'username': 'root', 'password': 'Link@506'},
    ]
    # inventory = {
    # 	"dynamic_host": {
    # 		"hosts": [
    # 			{"hostname": "192.168.1.34", "port": "22", "username": "root", "password": "jinzhuan2015"},
    # 			{"hostname": "192.168.1.130", "port": "22", "username": "root", "password": "jinzhuan2015"}
    # 		],
    # 		"vars": {
    # 			"var1":"ansible",
    # 			"var2":"saltstack"
    # 		}
    # 	}
    # }
    rbt = ANSRunner(inventory)
    # rbt.run_model(host_list='all', module_name='raw', module_args="ls /tmp")
    # data = rbt.get_model_result()
    # c = rbt.handle_model_data(data, 'raw')
    # print(c)
    rbt.run_model(host_list='all', module_name='setup', module_args="")
    data = rbt.get_model_result()
    print(data)
    c = rbt.handle_setup_data(data)
    print(c)

