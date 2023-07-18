from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.core import exceptions, validators
from rest_framework import serializers
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.utils import unix_epoch

from mp.common import ratelimit
from mp.common.utils import get_client_ip
from mp.users.signals import user_logged_in
from mp.users.models import LoginLogs


def get_username_field():
    return get_user_model().USERNAME_FIELD


def get_email_field():
    return get_user_model().EMAIL_FIELD


def get_login_attempts_cache_key(request, **credentials):
    ip = get_client_ip(request)
    login = credentials.get('email', credentials.get('username', '')).lower()
    return "{ip}:{login}".format(ip=ip, login=login)


def delete_login_attempts_cached_email(request, **credentials):
    cache_key = get_login_attempts_cache_key(request, **credentials)
    ratelimit.clear(request, action="login_failed", key=cache_key)


class JSONWebTokenSerializer(serializers.Serializer):
    """
    Serializer class used to validate a username/email and password.

    'username/email' is identified by the custom UserModel.USERNAME_FIELD.

    Returns a JSON Web Token that can be used to authenticate later calls.
    """
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'})
    token = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        """Dynamically add the USERNAME_FIELD to self.fields."""
        super(JSONWebTokenSerializer, self).__init__(*args, **kwargs)
        self.fields['redirect'] = serializers.CharField(write_only=True, required=False)
        if settings.CUSTOM_AUTHENTICATION_METHOD == 'username':
            self.fields[self.username_field] = serializers.CharField(write_only=True, required=True, help_text='用户名登陆')
        elif settings.CUSTOM_AUTHENTICATION_METHOD == 'email':
            self.fields[self.email_field] = serializers.EmailField(write_only=True, required=True, help_text='邮箱登陆')
        else:
            self.fields[self.username_email_field] = serializers.CharField(write_only=True, required=True, help_text="支持邮箱或者用户名登陆")

    def is_email(self, value):
        try:
            validators.EmailValidator(value)
            ret = True
        except exceptions.ValidationError:
            ret = False
        return ret

    def user_credentials(self, data):
        """
        验证用户登陆
        """
        credentials = {}
        if settings.CUSTOM_AUTHENTICATION_METHOD == 'email':
            credentials[self.email_field] = data.get(self.email_field)
        elif settings.CUSTOM_AUTHENTICATION_METHOD == 'username':
            credentials[self.username_field] = data.get(self.username_field)
        else:
            f = data.get(self.username_email_field)
            if self.is_email(f):
                credentials[self.email_field] = f
            credentials[self.username_field] = f
        return credentials

    @staticmethod
    def pre_validate(request, **credentials):
        if settings.CUSTOM_LOGIN_ATTEMPTS_LIMIT:
            cache_key = get_login_attempts_cache_key(request, **credentials)
            if not ratelimit.consume(
                    request,
                    action="login_failed",
                    key=cache_key,
                    amount=settings.CUSTOM_LOGIN_ATTEMPTS_LIMIT,
                    duration=settings.CUSTOM_LOGIN_ATTEMPTS_TIMEOUT or 300,
            ):
                msg = '尝试次数过多，请稍后再试。'
                raise serializers.ValidationError(msg)

    def validate(self, data):
        credentials = self.user_credentials(data)
        credentials['password'] = data.get('password')
        request = self.context['request']

        from config.backends.auth_backends import MyBackend
        self.pre_validate(request, **credentials)
        MyBackend.unstash_authenticated_user()
        user = authenticate(request, **credentials)
        alt_user = MyBackend.unstash_authenticated_user()
        user = user or alt_user
        if user and settings.CUSTOM_LOGIN_ATTEMPTS_LIMIT:
            delete_login_attempts_cached_email(request, **credentials)

        if not user:
            msg = '无法使用提供的凭据登录。'
            raise serializers.ValidationError(msg)
        else:
            # 登陆成功
            signal_kwargs = {'message': '登陆成功'}
            user_logged_in.send(
                sender=user.__class__,
                request=request,
                user=user,
            )

        payload = JSONWebTokenAuthentication.jwt_create_payload(user)

        return {
            'token': JSONWebTokenAuthentication.jwt_encode_payload(payload),
            'user': user,
            'issued_at': payload.get('iat', unix_epoch()),
            'redirect': data.get('redirect')
        }

    @property
    def username_field(self):
        return get_username_field()

    @property
    def email_field(self):
        return get_email_field()

    @property
    def username_email_field(self):
        return "username_email"


class LoginLogsListSerializer(serializers.ModelSerializer):
    action_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = LoginLogs
        fields = '__all__'


