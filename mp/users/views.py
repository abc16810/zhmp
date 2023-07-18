import json

from django.conf import settings
from django.contrib.auth.views import RedirectURLMixin
from django.http import HttpResponse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import resolve_url
from django.views.generic import FormView

from mp.common.utils import get_login_redirect_url, get_next_redirect_url
from .forms import LoginForm


# Create your views here.


def is_ajax(request):
    return any(
        [
            request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest",
            request.content_type == "application/json",
            request.META.get("HTTP_ACCEPT") == "application/json",
            ]
    )


class RedirectAuthenticatedUserMixin(object):
    """
    登陆状态重定向
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and settings.LOGIN_REDIRECT_URL:
            redirect_to = self.get_authenticated_redirect_url()
            response = HttpResponseRedirect(redirect_to)
            if is_ajax(request):
                if (isinstance(response, HttpResponseRedirect) or isinstance(
                        response, HttpResponsePermanentRedirect)):
                    redirect_to = response['Location']
                else:
                    redirect_to = None

                resp = {}
                status = response.status_code
                if redirect_to:
                    status = 200
                    resp['location'] = redirect_to

                response = HttpResponse(json.dumps(resp), status=status, content_type='application/json')
        else:
            response = super(RedirectAuthenticatedUserMixin,
                             self).dispatch(request,
                                            *args,
                                            **kwargs)
        return response

    def get_authenticated_redirect_url(self):
        redirect_field_name = self.redirect_field_name
        return get_login_redirect_url(self.request,
                                      url=self.get_success_url(),
                                      redirect_field_name=redirect_field_name)


# 登陆html实现
class LoginView(RedirectURLMixin,
                RedirectAuthenticatedUserMixin,
                FormView):
    form_class = LoginForm
    template_name = "login.html"
    success_url = None
    redirect_field_name = "next"
    extra_context = {'site_describe': '登录'}

    def get(self, request, *args, **kwargs):
        response = super(LoginView, self).get(
            request, *args, **kwargs)
        return response

    def get_initial(self):
        redirect_url = self.get_redirect_url()
        self.initial['redirect_url'] = redirect_url
        return self.initial.copy()

    def get_redirect_url(self):
        allowed_hosts = self.get_success_url_allowed_hosts()
        ret = (get_next_redirect_url(
            self.request,
            self.redirect_field_name,
            allowed_hosts) or resolve_url(self.success_url or settings.LOGIN_REDIRECT_URL))
        return ret
