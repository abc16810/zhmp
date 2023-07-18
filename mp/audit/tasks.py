from mp.users.models import LoginLogs


def save_audit_log(instance, ip, action, time, name):
    LoginLogs.objects.create(user_id=instance.id if instance else '0',
                             user_display=instance.nickname if instance else '',
                             ip=ip,
                             extra_info='' if instance else '非法尝试登陆',
                             action_time=time,
                             action=action,
                             user_name=name
                             )
