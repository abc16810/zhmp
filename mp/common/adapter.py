# -*- coding: utf-8 -*
from django.contrib.auth.models import AbstractUser
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import force_str
from django import forms
from django.urls import reverse
from django.contrib.auth import authenticate
from django.contrib.auth import (
    authenticate,
    get_backends,
    login as django_login,
    logout as django_logout,
)
from django.contrib.sites.shortcuts import get_current_site
from .config import app_settings
from . import ratelimit
import json


class DefaultAccountAdapter(object):

    def __init__(self, request=None):
        self.request = request

    error_messages = {
        'username_blacklisted': "用户名不能使用。请使用其他用户名",
        'username_taken': AbstractUser._meta.get_field('username').error_messages['unique'],
        'too_many_login_attempts': "登录失败次数太多。稍后再试",
        'email_taken': "用户已使用此电子邮件地址注册"
    }

    def ajax_response(self, request, response, redirect_to=None, form=None,
                      data=None):
        resp = {}
        status = response.status_code

        if redirect_to:
            status = 200
            resp['location'] = redirect_to
        if form:
            if request.method == 'POST':
                if form.is_valid():
                    status = 200
                else:
                    status = 400
            else:
                status = 200
            resp['form'] = self.ajax_response_form(form)
            if hasattr(response, 'render'):
                response.render()
            resp['html'] = response.content.decode('utf8')
            if data is not None:
                resp['data'] = data
        return HttpResponse(json.dumps(resp),
                            status=status,
                            content_type='application/json')

    def ajax_response_form(self, form):
        form_spec = {
            'fields': {},
            'field_order': [],
            'errors': form.non_field_errors()
        }
        for field in form:
            field_spec = {
                'label': force_str(field.label),
                'value': field.value(),
                'help_text': force_str(field.help_text),
                'errors': [
                    force_str(e) for e in field.errors
                ],
                'widget': {
                    'attrs': {
                        k: force_str(v)
                        for k, v in field.field.widget.attrs.items()
                    }
                }
            }
            form_spec['fields'][field.html_name] = field_spec
            form_spec['field_order'].append(field.html_name)
        return form_spec

    def is_ajax(self, request):
        return any(
            [
                request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest",
                request.content_type == "application/json",
                request.META.get("HTTP_ACCEPT") == "application/json",
            ]
        )

    def _delete_login_attempts_cached_email(self, request, **credentials):
        if app_settings.LOGIN_ATTEMPTS_LIMIT:
            cache_key = self._get_login_attempts_cache_key(request, **credentials)
            ratelimit.clear(request, action="login_failed", key=cache_key)

    def _get_login_attempts_cache_key(self, request, **credentials):
        site = get_current_site(request)
        login = credentials.get('email', credentials.get('username', '')).lower()
        return "{site}:{login}".format(site=site.domain or 'mp', login=login)

    def pre_authenticate(self, request, **credentials):
        if app_settings.LOGIN_ATTEMPTS_LIMIT:
            cache_key = self._get_login_attempts_cache_key(request, **credentials)
            if not ratelimit.consume(
                request,
                action="login_failed",
                key=cache_key,
                amount=app_settings.LOGIN_ATTEMPTS_LIMIT,
                duration=app_settings.LOGIN_ATTEMPTS_TIMEOUT,
            ):
                raise forms.ValidationError(
                    self.error_messages["too_many_login_attempts"]
                )

    def authenticate(self, request, **credentials):
        """只认证，不实际登录"""
        from common.auth_backends import MyBackend
        self.pre_authenticate(request, **credentials)
        MyBackend.unstash_authenticated_user()
        user = authenticate(request, **credentials)
        alt_user = MyBackend.unstash_authenticated_user()
        user = user or alt_user
        if user and app_settings.LOGIN_ATTEMPTS_LIMIT:
            self._delete_login_attempts_cached_email(request, **credentials)
        else:
            self.authentication_failed(request, **credentials)
        return user

    def authentication_failed(self, request, **credentials):
        pass

    def respond_user_inactive(self):
        return HttpResponseRedirect(reverse("account_inactive"))

    def login(self, request, user):
        if not hasattr(user, "backend"):
            from .auth_backends import MyBackend
            backends = get_backends()
            backend = None
            for b in backends:
                if isinstance(b, MyBackend):
                    backend = b
                    break
                elif not backend and hasattr(b, "get_user"):
                    backend = b
            backend_path = ".".join([backend.__module__, backend.__class__.__name__])
            user.backend = backend_path
        django_login(request, user)

    def logout(self, request):
        django_logout(request)


def get_adapter(request=None):
    return DefaultAccountAdapter(request)
