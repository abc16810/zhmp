from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, Group, AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from mirage import fields
import uuid
from mp.common.models import TimestampsWithAutoAndDefault, TimestampsWithDefault


# 用户模块，可以通过用户名和密码 或者 邮箱和密码登陆
class MyUser(TimestampsWithAutoAndDefault, AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        verbose_name='用户名',
        max_length=150,
        unique=True,
        help_text='要求，150字以内。字母、数字和@/。/ + / - / _。',
        validators=[username_validator],
        error_messages={
            "unique": '该用户名已经存在',
        },
    )

    email = models.EmailField(
        verbose_name="email 地址",
        max_length=255,
        unique=True,
        error_messages={
            "unique": '该email地址已经存在',
        },
        blank=True)

    is_staff = models.BooleanField(
        verbose_name='staff status',
        default=False,
        help_text='指定用户是否可以登录到此管理站点',
    )
    is_active = models.BooleanField(
        verbose_name='激活状态',
        default=True,
        help_text='指定是否应将此用户视为活动用户。'
    )

    nickname = models.CharField('昵称', max_length=50, unique=True, null=True, blank=True)

    jwt_key = models.UUIDField(default=uuid.uuid4)

    failed_login_count = models.IntegerField('失败计数', default=0)
    last_login_failed_at = models.DateTimeField('上次失败登录时间', blank=True, null=True)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    objects = UserManager()

    def save(self, *args, **kwargs):
        self.failed_login_count = min(127, self.failed_login_count)
        self.failed_login_count = max(0, self.failed_login_count)
        super(MyUser, self).save(*args, **kwargs)

    def __str__(self):
        if self.nickname:
            return self.nickname
        return self.username

    @property
    def display_name(self):
        if self.nickname:
            return self.nickname
        return self.username or self.email

    class Meta:
        managed = True
        db_table = 'mp_users'
        verbose_name = '用户管理'
        verbose_name_plural = '用户管理'
        default_permissions = ()
        permissions = (
            ("add_user", "添加用户"),
            ("change_user", "修改用户"),
            ("delete_user", "删除用户"),
            ("view_user", "查看用户"),
        )

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser
        }


class MyGroup(Group):
    description = models.CharField('描述', max_length=200, default='', blank=True)

    class Meta:
        db_table = 'mp_groups'
        verbose_name = '用户组'
        verbose_name_plural = '用户组'
        default_permissions = ()
        permissions = (
            ("add_mpgroup", "添加用户组"),
            ("change_mygroup", "修改用户组"),
            ("delete_mygroup", "删除用户组"),
            ("view_mygroup", "查看用户组"),
        )


# 登陆日志
class LoginLogs(models.Model):
    """
    登录审计日志
    """
    user_id = models.IntegerField('用户ID')
    user_name = models.CharField('用户名称', max_length=30, null=True)
    user_display = models.CharField('用户中文名', max_length=50, null=True)
    action = models.CharField('动作', max_length=255)
    extra_info = models.TextField('额外的信息', null=True)
    ip = models.GenericIPAddressField("登陆IP", null=True)
    action_time = models.DateTimeField('操作时间', auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'mp_login_logs'
        verbose_name = '登陆日志'
        verbose_name_plural = verbose_name
        default_permissions = ()
        permissions = (
            ("add_loginlogs", "添加登陆日志"),
            ("change_loginlogs", "修改审计日志"),
            ("delete_loginlogs", "删除审计日志"),
            ("view_loginlogs", "查看审计日志"),
        )

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.user_name, self.ip, self.action)


# 配置信息表
class Config(TimestampsWithDefault):
    item = models.CharField(verbose_name='配置项', max_length=100, primary_key=True)
    value = fields.EncryptedCharField(verbose_name='配置项值', max_length=200)
    description = models.CharField('描述', max_length=200, default='', blank=True)

    class Meta:
        managed = True
        db_table = 'mp_config'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'

    def save(self, *args, **kwargs):
        if not self.item.startswith('mp_'):
            self.item = 'mp_%s' % self.item.strip()
        super().save(*args, **kwargs)
