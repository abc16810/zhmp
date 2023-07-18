import time
from mp.common.ansible.api_29 import ansibleexecapi29, handle_setup_data
from django_q.conf import logger
import datetime
from django.db.models import Q
from .models import ServerAssets, DISK, NIC, Assets, RAM
from mp.common.ansible.redis_queue import FifoQueue
import ansible.constants as C
from config.env import BASE_DIR


# test
def test_task(user):
    time.sleep(2)
    res = 'this is a test'
    return res


def id_asset_list(ids):
    asset_list = Assets.objects.filter(id__in=ids).select_related('serverassets')
    data = []
    logger.info("ansible 开始批量更新资产.")
    for asset in asset_list:
        if hasattr(asset, 'serverassets'):
            if asset.assets_type in ['server', 'vmser']:
                an = asset.serverassets.to_ansible
                if an.get('has_user'):
                    data.append(an)
                else:
                    logger.warning("%s 资产没有关联管理用户，忽略" % asset)
            else:
                logger.warning('%s 资产类型不支持，忽略' % asset)
        else:
            logger.warning('%s 资产没有关联server资产, 忽略' % asset)
    return data


def ansible_batch_update(ids):
    """
    :param ids: []
    :return:
    """
    inventory = id_asset_list(ids)
    taskid = "Ansible_Batch_Setup_%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if inventory:
        # 异步执行ansibel api 需要如下配置
        import multiprocessing
        current_process = multiprocessing.current_process
        current_process()._config['daemon'] = False

        logger.info("开始执行ansible 批量任务")
        ansibleexecapi29(taskid, 'setup', "", inventory_data=inventory)
    return taskid


def ansible_batch_update_memory(ids):
    """
    批量更新资产内存信息
    :param ids:
    :return:
    """
    inventory = id_asset_list(ids)
    taskid = "Ansible_Batch_Setup_Mem_%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if inventory:
        # 异步执行ansibel api 需要如下配置
        import multiprocessing
        current_process = multiprocessing.current_process
        current_process()._config['daemon'] = False

        logger.info("开始执行ansible 批量获取主机内存信息任务")
        custom_module_path = BASE_DIR + 'mp/common/library/modules'
        C.DEFAULT_MODULE_PATH.insert(0, custom_module_path)
        ansibleexecapi29(taskid, 'get_memory', "", inventory_data=inventory)
    return taskid


def ansible_batch_setup_to_save_db(taskid, is_mem):
    """
    :param taskid: 任务ID
    :param is_mem:
    :return:
    """
    logger.info("开始处理结果保存任务 %s" % taskid)
    data = FifoQueue(taskid)
    len_result = len(data)
    for _ in range(len_result):
        item = data.pop()
        if item:
            assert isinstance(item, dict)
            ip_or_hostname = item.get('host')
            status = item.get('status')
            result = item['result']
            if status == 'success':
                try:
                    s_asset = ServerAssets.objects.filter(Q(ip=ip_or_hostname) | Q(hostname=ip_or_hostname))
                    obj = s_asset.get()
                except Exception as err:
                    logger.warning('【%s】重复资产' % ip_or_hostname)
                else:
                    base_obj = obj.assets

                    if is_mem:
                        mem_data = {}
                        r_obj = RAM.objects.filter(assets=base_obj)
                        info = result.get('ansible_facts')
                        mem_data['ram_max_slot'] = info.get('ansible_ram_slot_num')
                        mem_data['ram_max_size'] = info.get('ansible_ram_max_size')
                        for mem in info.get('ansible_ram', []):
                            if mem.get('asset_tag'):
                                mem.pop('asset_tag')
                            keyword = {'slot': mem.pop('slot')}
                            mem.update(mem_data)
                            mem.update({'assets': base_obj})
                            _, s = r_obj.update_or_create(defaults=mem, **keyword)
                            if s:
                                logger.info('【%s】创建内存资产%s' % (ip_or_hostname, keyword.get('slot')))
                            else:
                                logger.info('【%s】更新内存资产%s' % (ip_or_hostname, keyword.get('slot')))
                    else:
                        data_list = handle_setup_data(result)

                        ser_update_fields = []
                        for k, v in data_list.items():
                            if k.startswith('s_'):
                                key = k.split('s_', 1)[-1]
                                ser_update_fields.append(key)
                                setattr(obj, key, v)
                        logger.info("【%s】更新Server信息" % ip_or_hostname)
                        obj.save(update_fields=ser_update_fields)

                        base_update_fields = []
                        for k, v in data_list.items():
                            if k.startswith('base_'):
                                key = k.split('base_', 1)[-1]
                                base_update_fields.append(key)
                                setattr(base_obj, key, v)
                        logger.info("【%s】更新基础信息" % ip_or_hostname)
                        base_obj.save(update_fields=base_update_fields)

                        d_obj = DISK.objects.filter(assets=base_obj)
                        n_obj = NIC.objects.filter(assets=base_obj)
                        logger.info(data_list.get('disk'))
                        for disk in data_list.get('disk', []):
                            if disk.get('wwn'):
                                keyword = {'wwn': disk.pop('wwn')}
                                disk.update({'assets': base_obj})
                            else:
                                keyword = {'name': disk.pop('name'), 'assets': base_obj}
                            logger.info('【%s】更新或创建硬盘资产 %s' % (ip_or_hostname, keyword))
                            d_obj.update_or_create(defaults=disk, **keyword)
                        for nic in data_list.get('nic', []):
                            keyword = {'assets': base_obj, 'mac': nic.pop('mac')}
                            logger.info('【%s】更新或创建网络资产 %s' % (ip_or_hostname, keyword))
                            n_obj.update_or_create(defaults=nic, **keyword)

            else:
                logger.warning('资产 %s 执行失败, 状态 %s, 详细信息 %s' % (ip_or_hostname, status, result))




