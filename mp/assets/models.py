import hashlib
import os
import re
import time

from django.db import models
from mirage import fields
from django.conf import settings
from config.env import BASE_DIR
from mp.common.models import TimestampsWithAuto
import paramiko
from io import StringIO


class Idc(TimestampsWithAuto):
    idc_name = models.CharField("机房名称", max_length=32, unique=True)
    idc_zone_name = models.CharField("区域名称", max_length=100)
    idc_operator = models.CharField("运营商", max_length=32, default="自营")
    idc_contact = models.CharField("机房联系人", max_length=16)
    idc_phone = models.CharField("联系人电话", max_length=20, blank=True, null=True, default="")
    idc_bandwidth = models.CharField("机房带宽", max_length=32, blank=True, default="")
    idc_address = models.CharField("机房地址", max_length=200)
    # idc_position = PointField("位置坐标", null=True, blank=True, srid=4326) # 地理坐标
    idc_comment = models.TextField("备注", max_length=200, blank=True)

    def __str__(self):
        return self.idc_name

    class Meta:
        db_table = 'mp_idc_assets'
        verbose_name = "机房管理"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        default_permissions = ()
        permissions = (
            ("add_idc", "添加机房"),
            ("change_idc", "修改机房"),
            ("delete_idc", "删除机房"),
            ("view_idc", "查看机房"),
        )


class Cabinet(TimestampsWithAuto):
    idc = models.ForeignKey(
        Idc, related_name='cabinet_assets', on_delete=models.SET_NULL, null=True, verbose_name="所属机房"
    )
    cabinet_name = models.CharField("机柜标签", max_length=100)
    cabinet_band = models.PositiveIntegerField("机柜带宽 MB", null=True, blank=True)
    cabinet_cost = models.DecimalField("费用", blank=True, null=True, max_digits=8, decimal_places=2)
    cabinet_comment = models.TextField("备注", max_length=200, blank=True)
    expired_time = models.DateTimeField("到期时间", blank=True, null=True)

    def __str__(self):
        return '%s' % self.cabinet_name

    class Meta:
        unique_together = (('idc', 'cabinet_name'),)
        db_table = 'mp_cabinet_assets'
        verbose_name = "机柜管理"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        default_permissions = ()
        permissions = (
            ("add_cabinet", "添加机柜"),
            ("change_cabinet", "修改机柜"),
            ("delete_cabinet", "删除机柜"),
            ("view_cabinet", "查看机柜"),
        )

    @property
    def zone(self):
        return '%s-%s' % (self.idc, self.cabinet_name)


def md5_for_file(chunks):
    md5 = hashlib.md5()
    for data in chunks:
        md5.update(data)
    return md5.hexdigest()


def simple_upload_to(field_name, path='keys'):
    def upload(instance, filename):
        name = md5_for_file(getattr(instance, field_name).chunks())
        filename = '%s_%s' % (name, instance.sign)
        return os.path.join(path, filename)
    return upload


def upload(instance, filename, field_name='pkey_path', path='keys'):
    name = md5_for_file(getattr(instance, field_name).chunks())
    filename = '%s_%s' % (name, instance.sign)
    return os.path.join(path, filename)


class SshUser(TimestampsWithAuto):
    sign = models.CharField("唯一标识", max_length=100, unique=True)
    username = models.CharField("用户名", max_length=100)
    port = models.DecimalField("端口", max_digits=6, decimal_places=0, default=22, blank=True)
    password = fields.EncryptedCharField(verbose_name="密码", max_length=200, blank=True, default='', null=True)
    pkey = fields.EncryptedTextField(verbose_name="密钥", max_length=6000, blank=True, null=True)
    pkey_path = models.FileField("密钥地址", blank=True, null=True, upload_to=upload)
    pkey_password = fields.EncryptedCharField(verbose_name='密钥密码', max_length=300, default='', blank=True, null=True)

    become = models.BooleanField("become", default=False)
    become_method = models.CharField("become 方法", max_length=10, default='sudo', blank=True, null=True)
    become_user = models.CharField("become 用户", max_length=20, default='root', blank=True, null=True)
    become_pass = fields.EncryptedCharField(verbose_name="become 密码", max_length=100, blank=True,
                                            default='', null=True)
    created_by = models.CharField("创建者", max_length=32, null=True, blank=True)
    comment = models.TextField("备注", blank=True, null=True)

    def __str__(self):
        return self.sign

    def short_pkey(self):
        if len(str(self.pkey)) > 20:
            return '{}...'.format(str(self.pkey)[0:19])
        else:
            return str(self.pkey)

    @property
    def get_pkey_path(self):
        if self.pkey_path:
            return self.pkey_path.path
        if self.pkey:
            md5_name = hashlib.md5(self.pkey.encode()).hexdigest()
            filename = '%s_%s' % (md5_name, self.sign)
            key_path = os.path.join(settings.MEDIA_ROOT, 'keys', filename)
            key = None
            try:
                key = paramiko.RSAKey.from_private_key(StringIO(self.pkey))
            except paramiko.SSHException:
                try:
                    key = paramiko.DSSKey.from_private_key(StringIO(self.pkey))
                except paramiko.SSHException:
                    pass
            if not key:
                return ''
                # raise ValueError('Unknown private key format')
            if not os.path.exists(key_path):
                key.write_private_key_file(key_path)
            return key_path

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'mp_auth_users'
        verbose_name = "ssh 账号管理"
        verbose_name_plural = verbose_name
        default_permissions = ()
        permissions = (
            ("add_ssh_user", "添加ssh账号"),
            ("change_ssh_user", "修改ssh账号"),
            ("delete_ssh_user", "删除ssh账号"),
            ("view_ssh_user", "查看ssh账号"),
        )


class Assets(TimestampsWithAuto):
    assets_type_choices = (
        ('server', '物理机'),
        ('vmser', '虚拟机'),
        ('switch', '交换机'),
        ('route', '路由器'),
        ('printer', '打印机'),
        ('scanner', '扫描仪'),
        ('firewall', '防火墙'),
        ('storage', '存储设备'),
        ('wifi', '无线设备'),
        ('other', "其它设备")
    )
    assets_status = (
        ('on', "使用中"),
        ('off', "未使用"),
        ('maintenance', "维护"),
        ('other', '其它状态')
    )
    assets_u = (
        (1, "1U"),
        (2, "2U"),
        (4, "4U")
    )

    assets_type = models.CharField("资产类型", choices=assets_type_choices, max_length=100, default='server')
    status = models.CharField("资产状态", choices=assets_status, max_length=30, default='on used')
    number = models.CharField("资产编号", max_length=32, unique=True)

    sn = models.CharField("序列号SN", max_length=128, null=True, blank=True)  # 设备序列号
    manufacturer = models.CharField("制造商", max_length=64, null=True, blank=True)  # 制造商
    version = models.CharField("版本", max_length=100, null=True, blank=True)  # 版本
    model = models.CharField("资产型号", max_length=54, null=True, blank=True)  # 资产型号

    management_ip = models.GenericIPAddressField('管理IP', blank=True, null=True)
    group = models.SmallIntegerField("使用组", blank=True, null=True)

    created_by = models.CharField("创建者", max_length=32, blank=True, default="")
    u = models.IntegerField("U数", choices=assets_u, null=True, blank=True)

    jg = models.ForeignKey(Cabinet, verbose_name="所属机柜", null=True, blank=True, related_name='asset',
                           on_delete=models.SET_NULL)
    comment = models.TextField("备注", blank=True, null=True)

    def __str__(self):
        return self.number + self.assets_type

    class Meta:
        db_table = 'mp_assets'
        verbose_name = "资产管理"
        verbose_name_plural = "总资产表"
        ordering = ['-created_at']
        default_permissions = ()
        permissions = (
            ("add_assets", "添加资产"),
            ("change_assets", "修改资产"),
            ("delete_assets", "删除资产"),
            ("view_assets", "查看资产")
        )

    def to_json(self):
        detail = {}
        if hasattr(self, 'serverassets'):
            detail = self.serverassets.to_json()
        return {
            'id': self.id,
            'number': self.number,
            'get_assets_type_display': self.get_assets_type_display(),
            'get_status_display': self.get_status_display(),
            'get_u_display': self.get_u_display(),
            'detail': detail,
        }


class ServerAssets(TimestampsWithAuto):
    assets = models.OneToOneField('Assets', on_delete=models.CASCADE)
    ip = models.GenericIPAddressField("IP地址", max_length=100)
    hostname = models.CharField(max_length=80, verbose_name="主机名", unique=True)

    cpu_model = models.CharField("cpu 型号", max_length=100, blank=True, null=True)
    cpu_number = models.SmallIntegerField("cpu 数量", blank=True, null=True)
    vcpu_number = models.SmallIntegerField("虚拟核数", blank=True, null=True)
    cpu_core = models.SmallIntegerField("cpu 核数", blank=True, null=True)

    platform = models.CharField("平台", max_length=128, null=True, blank=True)
    os = models.CharField("系统", max_length=128, null=True, blank=True)
    os_version = models.CharField("系统版本", max_length=16, null=True, blank=True)
    os_arch = models.CharField("系统架构", max_length=16, blank=True, null=True)
    kernel = models.CharField("内核信息", max_length=200, blank=True, null=True)

    disk_total = models.IntegerField("总硬盘容量", blank=True, null=True)
    ram_total = models.IntegerField("总内存容量", blank=True, null=True)

    hosted_on = models.ForeignKey('self', related_name='hosted_on_server', blank=True, null=True,
                                  verbose_name="所属物理机", on_delete=models.SET_NULL)
    hostname_raw = models.CharField("原始主机名", max_length=128, blank=True, null=True)

    ssh = models.ForeignKey(SshUser, verbose_name="ssh user", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = (('ip', 'hostname'),)
        db_table = 'mp_server_assets'
        default_permissions = ()
        permissions = (
            ("add_server_assets", "添加服务资产"),
            ("change_server_asset", "修改服务资产"),
            ("delete_server_asset", "删除服务资产"),
            ("view_server_asset", "查看服务资产"),
        )
        verbose_name = "资产管理"
        verbose_name_plural = "服务器资产表"

    def __str__(self):
        return '[%s]-%s' % (self.hostname, self.ip)

    def save(self, *args, **kwargs):
        if self.hostname_raw and self.hostname_raw != self.hostname:
            self.hostname = self.hostname_raw
        super().save(*args, **kwargs)

    @property
    def cpu(self):
        if self.cpu_model:
            return '{}*{}*{}'.format(re.sub(r'\s+', '_', self.cpu_model), self.cpu_number, self.cpu_core)
        else:
            return '未知'

    @property
    def system(self):
        if self.os:
            return '{} {} {}'.format(self.os, self.os_version, self.os_arch)
        else:
            return '未知'

    def to_base_kwargs(self):
        return {
            'ip': self.ip,
            'hostname': self.hostname,
            'port': 22,
            'has_user': False,
            'type': self.assets.assets_type
        }

    @property
    def to_ansible(self):
        data = self.to_base_kwargs()
        if self.ssh:
            if self.ssh.port:
                data['port'] = int(self.ssh.port)
            if self.ssh.become:
                b = {'method': self.ssh.become_method,
                     'user': self.ssh.become_user,
                     'pass': self.ssh.become_pass
                     }
                data['become'] = b
            if self.ssh.password:
                data['password'] = self.ssh.password
            else:
                data['private_key'] = self.ssh.get_pkey_path
            data['username'] = self.ssh.username
            data['has_user'] = True
        return data

    def to_json(self):
        json_format = {
            "id": self.id,
            "hostname": self.hostname,
            "ip": self.ip,
            "cpu": self.cpu,
            "system": self.system,
            "platform": self.platform,
            "hostname_raw": self.hostname_raw,
            'ram_total': self.ram_total
        }
        return json_format


class RAM(TimestampsWithAuto):
    """
    内存条
    """
    assets = models.ForeignKey('Assets', null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='ram', verbose_name="所属资产")
    size = models.IntegerField("内存大小（MB）")
    sn = models.CharField("SN", max_length=128, blank=True, null=True)
    model = models.CharField("内存型号", max_length=128, blank=True, null=True)
    slot = models.CharField("内存插槽", max_length=64, blank=True, null=True)
    manufactory = models.CharField("内存生产商", max_length=64, blank=True, null=True)
    speed = models.CharField("内存速率", max_length=64, blank=True, null=True)

    ram_max_size = models.CharField("最大内存", max_length=24, blank=True, null=True)
    ram_max_slot = models.IntegerField("插槽个数", blank=True, null=True)
    comment = models.TextField("备注", blank=True, null=True)

    def __str__(self):
        return '%s:%s:%s' % (self.assets, self.slot, self.size)

    class Meta:
        db_table = 'mp_asset_ram'
        verbose_name = "内存管理"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        default_permissions = ()
        permissions = (
            ("add_ram", "添加内存"),
            ("change_ram", "修改内存"),
            ("delete_ram", "删除内存"),
            ("view_ram", "查看内存"),
        )

    @property
    def to_json(self):
        json_format = {
            "sn": self.sn,
            "slot": self.slot,
            "model": self.model,
            "manufactory": self.manufactory,
            "size": self.size,
            "speed": self.speed,
            "ram_max_size": self.ram_max_size,
            "ram_max_slot": self.ram_max_slot,
            "comment": self.comment,
        }
        return json_format


class NIC(TimestampsWithAuto):
    assets = models.ForeignKey('Assets', on_delete=models.SET_NULL, related_name='nic',
                               verbose_name="所属资产", null=True, blank=True)
    name = models.CharField("名称", max_length=64)
    mac = models.CharField("MAC地址", max_length=64, blank=True, null=True)
    ip = models.GenericIPAddressField("IP地址", blank=True, null=True)
    netmask = models.CharField("掩码", max_length=64, blank=True, null=True)
    promisc = models.BooleanField("混杂模式", default=True)
    is_ipv4_default = models.BooleanField("是否为默认IP地址", default=False)
    gateway = models.GenericIPAddressField("网关", blank=True, null=True)
    speed = models.CharField("速率", max_length=10, blank=True, null=True)
    types = models.CharField("类型", max_length=20, blank=True, null=True)
    module = models.CharField("模块", max_length=100, blank=True, null=True)
    active = models.SmallIntegerField(blank=True, null=True, verbose_name='是否在线')
    comment = models.TextField("备注", blank=True, null=True)

    def __str__(self):
        return '%s:%s' % (self.assets_id, self.ip)

    class Meta:
        db_table = 'mp_asset_nic'
        verbose_name = "网卡管理"
        verbose_name_plural = verbose_name
        unique_together = ("assets", "mac")
        ordering = ['-created_at']
        default_permissions = ()
        permissions = (
            ("add_nic", "增加网卡"),
            ("change_nic", "修改网卡"),
            ("delete_nic", "删除网卡"),
            ("view_nic", "查看网卡"),
        )

    @property
    def to_json(self):
        json_format = {
            "name": self.name,
            "mac": self.mac,
            "ip": self.ip,
            "is_ipv4_default": self.is_ipv4_default,
            "netmask": self.netmask,
            "gateway": self.gateway,
            "speed": self.speed,
            "module": self.module,
            "active": self.active,
        }
        return json_format


class DISK(TimestampsWithAuto):
    assets = models.ForeignKey('Assets', null=True, blank=True, on_delete=models.SET_NULL, related_name='disk')
    name = models.CharField("设备名称", max_length=64, blank=True, null=True)
    wwn = models.CharField('硬盘序列号（WWN）', null=True, blank=True, max_length=50, unique=True)  # 全球惟一名字(硬盘序列号)
    host = models.CharField("硬盘控制器", max_length=255, null=True, blank=True)  # 控制器
    device_size = models.CharField("硬盘容量", max_length=100, blank=True, null=True)
    device_vendor = models.CharField("硬盘生产商", max_length=64, null=True, blank=True)  # 供应商
    device_model = models.CharField("硬盘型号", max_length=128, blank=True, null=True)  # 磁盘型号
    partitions = models.JSONField("分区信息", blank=True, null=True)
    comment = models.TextField("备注", blank=True, null=True)

    def __str__(self):
        return '%s_%s_%s' % (self.assets, str(self.name), self.wwn)

    class Meta:
        db_table = 'mp_asset_disk'
        verbose_name = "硬盘管理"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        default_permissions = ()
        permissions = (
            ("add_disk", "添加硬盘"),
            ("change_disk", "修改硬盘"),
            ("delete_disk", "删除硬盘"),
            ("view_disk", "查看硬盘"),
        )

    @property
    def to_json(self):
        json_format = {
            "name": self.name,
            "wwn": self.wwn,
            "host": self.host,
            "size": self.device_size,
            "vendor": self.device_vendor,
            "model": self.device_model,
            "partitions": self.partitions or {},
            "comment": self.comment,
        }
        return json_format

# class AssetUpdateLog(models.Model):
#     """
#     资产更新日志
#     """
#
#     operation_type_choices = (
#         (0, "提交/待审核"),
#         (1, "审核通过"),
#         (2, "审核不通过"),
#         (3, "审核取消"),
#         (4, "定时执行"),
#         (5, "执行工单"),
#         (6, "执行结束"),
#     )
#
#     id = models.AutoField(primary_key=True)
#     audit_id = models.IntegerField("工单审批id", db_index=True)
#     operation_type = models.SmallIntegerField("操作类型", choices=operation_type_choices)
#     operation_type_desc = models.CharField("操作类型描述", max_length=10)
#     operation_info = models.CharField("操作信息", max_length=1000)
#     operator = models.CharField("操作人", max_length=30)
#     operator_display = models.CharField("操作人中文名", max_length=50, default="")
#     operation_time = models.DateTimeField(auto_now_add=True)
#
#     def __int__(self):
#         return self.audit_id
#
#     class Meta:
#         managed = True
#         db_table = "workflow_log"
#         verbose_name = "工作流日志"
#         verbose_name_plural = "工作流日志"