
from ansible.parsing.dataloader import DataLoader
from ansible import context
from ansible.executor.task_queue_manager import TaskQueueManager
import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.playbook.play import Play
from ansible.module_utils.common.collections import ImmutableDict
from ansible.vars.manager import VariableManager
from .inventory import get_inventory
from .callback import RedisCallBack
from django_q.conf import logger
import datetime
import shutil


def get_default_options():
    options = dict(
        syntax=False,
        timeout=30,  # C.DEFAULT_TIMEOUT,  # 默认10s
        connection='ssh',  # smart ssh
        forks=C.DEFAULT_FORKS,  # 默认线程5
        remote_user=C.DEFAULT_REMOTE_USER,  # 远程用户默认''
        module_path='',
        private_key_file=None,
        ssh_common_args="",
        ssh_extra_args="",
        sftp_extra_args="",
        scp_extra_args="",
        become=None,
        become_method=None,
        become_user=None,
        verbosity=0,
        extra_vars=[],
        check=False,
        diff=False,
        start_at_task=None,
        gathering='implicit',
        remote_tmp='/tmp/.ansible'
    )
    return options


def check_module_args(module_name, *, module_args=''):
    if module_name in C.MODULE_REQUIRE_ARGS and not module_args:
        msg = "No argument passed to '%s' module." % module_name
        logger.error(msg)
        raise AnsibleError(msg)


def check_pattern(inventory_data, pattern):
    if not pattern:
        msg = "[Pattern] or [Host list] `{}` is not valid!".format(pattern)
        logger.error(msg)
        raise AnsibleError(msg)
    if not inventory_data.list_hosts("all"):
        msg = "Inventory is empty."
        logger.error(msg)
        raise AnsibleError(msg)
    if isinstance(pattern, str) and not inventory_data.list_hosts(pattern):
        msg = 'pattern: %s  dose not match any hosts.' % pattern
        logger.error(msg)
        raise AnsibleError(msg)


class TaskQueueManager_V2(TaskQueueManager):

    def __init__(self, inventory, variable_manager, loader, passwords, stdout_callback=None,
                 run_additional_callbacks=True, run_tree=False):
        super().__init__(inventory, variable_manager, loader, passwords, stdout_callback,
                         run_additional_callbacks, run_tree)

        self.forks = context.CLIARGS.get('forks')
        self._stdout_callback = stdout_callback

    def load_callbacks(self):   # 为callback 设置存储id
        pass


# 执行 ansible 模块任务
def ansibleexecapi29(taskid, module_name, module_args, inventory_data, *,
                     host_list='all', gather_facts='no', **kwargs):
    """
    :param taskid: 任务ID
    :param module_name:  模块名称
    :param module_args:  模块参数
    :param inventory_data:  资产list
    :param host_list: 主机列表或者组名称如'all'
    :param gather_facts:
    :param kwargs:
    :return:
    """
    check_module_args(module_name, module_args=module_args)
    options = get_default_options()
    context.CLIARGS = ImmutableDict(options)
    if kwargs:
        context.CLIARGS.union(kwargs)
    loader = DataLoader()
    passwords = dict(vault_pass='secret')
    results_callback = RedisCallBack(taskid)
    inventory = get_inventory(inventory_data)
    check_pattern(inventory, host_list)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    play_source = dict(
        name="Ansible Ad-hoc",
        hosts=host_list,
        gather_facts=gather_facts,
        tasks=[dict(action=dict(module=module_name, args=module_args))],
    )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    tqm = None
    try:
        tqm = TaskQueueManager_V2(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
            stdout_callback=results_callback,
        )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
        if loader:
            loader.cleanup_all_tmp_files()

    # Remove ansible tmpdir
    shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)


def handle_setup_data(data):
    """
    处理setup返回结果方法
    :param data:
    :return: dict
    """

    base_info = {}

    info = data.get('ansible_facts', {})

    if info:
        # cpu
        base_info['s_cpu_model'] = info['ansible_processor'][-1]
        base_info['s_cpu_number'] = info['ansible_processor_count']
        base_info['s_vcpu_number'] = info['ansible_processor_vcpus']
        base_info['s_cpu_core'] = info['ansible_processor_cores']

        # 序列号SN
        base_info['base_sn'] = info['ansible_product_serial']
        # 制造商
        base_info['base_manufacturer'] = info.get('ansible_system_vendor')
        # 型号
        base_info['base_model'] = info.get('ansible_product_name').split(':')[0]
        # 版本
        base_info['base_version'] = info.get('ansible_product_version')

        # 平台
        base_info['s_platform'] = info.get('ansible_system')
        # 系统
        base_info['s_os'] = info.get('ansible_distribution')
        # 系统版本
        base_info['s_os_version'] = info.get('ansible_distribution_version')
        # 架构
        base_info['s_os_arch'] = info.get('ansible_architecture')
        # 内核
        base_info['s_kernel'] = info.get('ansible_kernel')

        # 主机名
        base_info['s_hostname_raw'] = info.get('ansible_hostname')

        # 内存
        base_info['s_ram_total'] = int(info['ansible_memtotal_mb'])   # MB

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
        base_info['s_disk_total'] = int(disk_sizes)

        all_nic = []
        nic_info = info['ansible_interfaces']
        default_nic = info['ansible_default_ipv4']
        for nic in nic_info:
            if nic == "lo" or nic.startswith('br-') or nic == 'docker0' \
                    or nic.startswith('veth') or nic.startswith('virbr'):
                continue
            nic_items = {}
            net = 'ansible_' + nic.replace("-", '_')
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

    return base_info


if __name__ == '__main__':
    task_id = "Ansible_Batch_Setup_%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    tasks = [
        dict(action=dict(module='setup', args='')),
    ]
    inventory = [{'ip': '10.4.55.209', 'hostname': 'devops', 'port': 22, 'has_user': True, 'type': 'server',
                  'password': '0h!4K$y0Z8#h11'}]
    ansibleexecapi29(task_id, tasks, inventory)


## https://github.com/search?q=AnsibleExecApi29&type=code
