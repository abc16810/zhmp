from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import FileField
from mp.common.models import TimestampsWithAuto
import os
from django.forms import forms
from django.template.defaultfilters import filesizeformat


class RestrictedFileField(FileField):
    """ max_upload_size:
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """

    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types", [])
        self.max_upload_size = kwargs.pop("max_upload_size", [])
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        file = data.file
        try:
            content_type = file.content_type
            if content_type in self.content_types:
                if file.size > self.max_upload_size:
                    raise forms.ValidationError('Please keep filesize under {}. Current filesize {}'
                                                .format(filesizeformat(self.max_upload_size),
                                                        filesizeformat(file.size)))
            else:
                raise forms.ValidationError('This file type is not allowed.')
        except AttributeError:
            pass
        return data


def upload(instance, filename, path='workflow'):
    filename = '%s_%s' % (instance.work_name, filename)
    return os.path.join(path, filename)


# 工单
class WorkFlow(TimestampsWithAuto):
    TYPE = (
             (0, '自动更新资产信息'),
             (1, '业务上线'),
             (2, '问题排查'),
             (3, '漏洞修复'),
             (4, '系统优化'),
             (5, '应用更新')
            )
    WORK_CHOICES = (
        ('finish', "正常结束"),
        ('abort', "终止流程"),
        ('manreviewing', "等待审核"),
        ('review_pass', "审核通过"),
        ('timingtask', "定时执行"),
        ('queuing', "排队中"),
        ('executing', "执行中/处理中"),
        ('autoreviewwrong', "自动执行错误"),
        ('exception', "执行异常"))

    work_name = models.CharField("名称", max_length=50)
    work_user = models.CharField('发起人', max_length=30)
    work_user_display = models.CharField('发起人中文名', max_length=50, default='')
    # 应用组
    app_group_id = models.IntegerField('业务组ID')
    app_name = models.CharField('业务组名称', max_length=100)

    work_type = models.SmallIntegerField(choices=TYPE, verbose_name='类型')
    work_status = models.CharField("状态", max_length=50, choices=WORK_CHOICES)

    file = RestrictedFileField("附件", blank=True, null=True, upload_to=upload, max_upload_size=2621440,
                               content_types=['application/pdf', 'application/excel', 'application/msword'])

    run_date_start = models.DateTimeField('可执行起始时间', null=True, blank=True)
    run_date_end = models.DateTimeField('可执行结束时间', null=True, blank=True)

    finish_time = models.DateTimeField('结束时间', null=True, blank=True)

    def __str__(self):
        return self.work_name

    class Meta:
        db_table = 'mp_workflow'
        verbose_name = '工作流'
        verbose_name_plural = '工作流管理'
        default_permissions = ()
        permissions = (
            ("add_workflow", "添加工作流"),
            ("change_workflow", "修改工作流"),
            ("delete_workflow", "删除工作流"),
            ("view_workflow", "查看工作流"),
        )

    def clean(self):
        if self.run_date_start >= self.run_date_end:
            raise ValidationError("End date cannot be before start date")


class WorkflowAuditLog(TimestampsWithAuto):
    """
    工作流审核状态表
    """
    workflow_status_choices = ((0, "待审核"), (1, "审核通过"), (2, "审核不通过"), (3, "审核取消"))

    audit_id = models.AutoField(primary_key=True)
    app_group_id = models.IntegerField('组ID')
    app_group_name = models.CharField('组名称', max_length=100)
    workflow_id = models.BigIntegerField('工单id')
    workflow_type = models.IntegerField('申请类型', choices=WorkFlow.TYPE)
    workflow_title = models.CharField('申请标题', max_length=50)
    workflow_remark = models.CharField('申请备注', default='', max_length=140, blank=True)
    audit_auth_groups = models.CharField('审批权限组列表', max_length=255)
    current_audit = models.CharField('当前审批权限组', max_length=20)
    next_audit = models.CharField('下级审批权限组', max_length=20)
    current_status = models.SmallIntegerField('审核状态', choices=workflow_status_choices)
    create_user = models.CharField('申请人', max_length=30)
    create_user_display = models.CharField('申请人中文名', max_length=50, default='')
    create_time = models.DateTimeField('申请时间', auto_now_add=True)
    result = models.TextField("执行结果", blank=True, null=True)

    def __int__(self):
        return self.audit_id

    class Meta:
        db_table = 'mp_workflow_audit_log'
        unique_together = ('workflow_id', 'workflow_type')
        verbose_name = u'工作流审批列表'
        verbose_name_plural = u'工作流审批列表'


class WorkFlowAudit(TimestampsWithAuto):
    """
    审批流程表
    """
    audit_id = models.AutoField("ID", primary_key=True)
    apps_group_id = models.IntegerField("业务组ID")
    apps_group_name = models.CharField("业务组名称", max_length=100)
    workflow_type = models.SmallIntegerField("审批类型", choices=WorkFlow.TYPE)
    audit_auth_groups = models.CharField("审批权限组列表", max_length=255)

    def __str__(self):
        return '%s' % self.audit_id

    class Meta:
        db_table = "mp_workflow_audit"
        unique_together = ("apps_group_id", "workflow_type")
        verbose_name = "审批流程配置"
        verbose_name_plural = "审批流程配置"


class WorkflowLog(TimestampsWithAuto):
    """
    工作流日志表
    """

    operation_type_choices = (
        (0, "提交/待审核"),
        (1, "审核通过"),
        (2, "审核不通过"),
        (3, "审核取消"),
        (4, "定时执行"),
        (5, "执行工单"),
        (6, "执行结束"),
    )

    id = models.AutoField(primary_key=True)
    audit_id = models.IntegerField("工单审批id", db_index=True)
    operation_type = models.SmallIntegerField("操作类型", choices=operation_type_choices)
    operation_type_desc = models.CharField("操作类型描述", max_length=10)
    operation_info = models.CharField("操作信息", max_length=1000)
    operator = models.CharField("操作人", max_length=30)
    operator_display = models.CharField("操作人中文名", max_length=50, default="")

    def __int__(self):
        return self.audit_id

    class Meta:
        db_table = "mp_workflow_log"
        verbose_name = "工作流日志"
        verbose_name_plural = "工作流日志"
