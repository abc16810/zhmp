# -*- coding: utf-8 -*
import unicodedata
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme


# from account import signals


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    norm_s1 = unicodedata.normalize("NFKC", s1).casefold()
    norm_s2 = unicodedata.normalize("NFKC", s2).casefold()
    return norm_s1 == norm_s2


def get_request_param(request, param, default=None):
    return request.POST.get(param) or request.GET.get(param, default)


def get_next_redirect_url(request, redirect_field_name="next", allowed_hosts=None):
    redirect_to = get_request_param(request, redirect_field_name)
    url_is_safe = url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts=allowed_hosts,
        require_https=request.is_secure(),
    )
    return redirect_to if url_is_safe else ""


def get_login_redirect_url(request, url=None, redirect_field_name="next"):
    if url and callable(url):
        url = url()
    redirect_url = (
            url or
            get_next_redirect_url(
                request,
                redirect_field_name=redirect_field_name)
    )
    return redirect_url


def get_username_max_length():
    user_model = get_user_model()
    username_field = user_model.USERNAME_FIELD
    if username_field is not None:
        max_length = user_model._meta.get_field(username_field).max_length
    else:
        max_length = 0
    return max_length


def localtime() -> datetime:
    """Override for timezone.localtime to deal with naive times and local times"""
    if settings.USE_TZ:
        return timezone.now()
    return datetime.now()


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
