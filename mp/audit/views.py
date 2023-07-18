from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_login_failed, user_logged_out
from django.db.models import Q
from django.dispatch import receiver
from django_q.tasks import async_task

from mp.common.utils import get_client_ip, localtime
from mp.users.signals import user_logged_in


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    req = kwargs.get('request')
    ip = get_client_ip(req) if req else None
    now = localtime()

    user_model = get_user_model()
    login_name = credentials.get('username') or credentials.get('email')
    user = None
    name = ""
    if login_name:
        login_name = login_name.strip()
        try:
            user = user_model.objects.filter(Q(username=login_name) | Q(email=login_name)).get()
        except user_model.DoesNotExist:
            pass
    if user:
        name = user.username

    async_task('mp.audit.tasks.save_audit_log', user, ip, '登入失败', now, name)


@receiver(user_logged_in)
def user_logged_in_callback(sender, **kwargs):
    now = localtime()
    request = kwargs.get('request')
    user = kwargs.get('user')
    ip = get_client_ip(request)
    name = user.username
    async_task('mp.audit.tasks.save_audit_log', user, ip, '登入成功', now, name)


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    now = localtime()
    name = user.username
    async_task('mp.audit.tasks.save_audit_log', user, ip, '登出', now, name)
