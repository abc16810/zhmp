from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import TemplateView


# 登陆日志html
class LoginLogView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "users.view_loginlogs"
    template_name = "users/login-logs.html"

    @staticmethod
    def get_action_type():
        res = ["登入失败", "登入", "登出"]
        return res

    def get_context_data(self, **kwargs):
        res = {
            'action_type': self.get_action_type()
        }
        kwargs.update(res)
        return super(LoginLogView, self).get_context_data(**kwargs)
