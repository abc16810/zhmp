# -*- coding: UTF-8 -*-
import re

from django.apps import apps
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_str
from rest_framework.authentication import (
    get_authorization_header,
)
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.blacklist.exceptions import (
    InvalidAuthorizationCredentials,
)

IGNORE_URL = [
    '/user/login/',
    '/api/info'
]

IGNORE_URL_RE = r'/api/(v1|auth)/\w+'


class CheckLoginMiddleware(MiddlewareMixin):
    """
    该函数在每个函数之前检查是否登录，若未登录，则重定向到/account/login/
    """
    def process_request(self, request):
        if not request.user.is_authenticated:
            if request.path not in IGNORE_URL and re.match(IGNORE_URL_RE, request.path) is None:
                return HttpResponseRedirect('/user/login/')


class JSONWebTokenMiddleware(MiddlewareMixin):
    """
    用于非api界面的认证
    """
    def process_request(self, request):
        if not request.user.is_authenticated:
            try:
                token = self.get_token_from_request(request)
                payload = JSONWebTokenAuthentication.jwt_decode_token(token)
                if apps.is_installed('rest_framework_jwt.blacklist'):
                    from rest_framework_jwt.blacklist.models import BlacklistedToken
                    if not BlacklistedToken.is_blocked(token, payload):
                        username = JSONWebTokenAuthentication.jwt_get_username_from_payload(payload)
                        if username:
                            user_model = get_user_model()
                            try:
                                user = user_model.objects.get_by_natural_key(username)
                                if user.is_active:
                                    request.user = user
                            except user_model.DoesNotExist:
                                pass
            except Exception:
                pass

    @classmethod
    def get_token_from_request(cls, request):
        try:
            authorization_header = force_str(get_authorization_header(request))

            return JSONWebTokenAuthentication.get_token_from_authorization_header(authorization_header)
        except (InvalidAuthorizationCredentials, UnicodeDecodeError):
            return JSONWebTokenAuthentication.get_token_from_cookies(request.COOKIES)
