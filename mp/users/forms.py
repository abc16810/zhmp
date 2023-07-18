# -*- coding: utf-8 -*
from django import forms
from django.conf import settings
from mp.common.utils import get_username_max_length
from django.utils.translation import pgettext


class PasswordField(forms.CharField):

    def __init__(self, *args, **kwargs):
        render_value = kwargs.pop('render_value', "")
        kwargs['widget'] = forms.PasswordInput(render_value=render_value,
                                               attrs={'placeholder':
                                                      kwargs.get("label"),
                                                      'class':
                                                      'form-control'})
        super(PasswordField, self).__init__(*args, **kwargs)


class LoginForm(forms.Form):
    password = PasswordField(label="密码")
    # remember = forms.BooleanField(label="记住",
    #                               required=False, widget=forms.CheckboxInput(attrs={"class": ""}))
    error_messages = {
        'account_inactive': "此帐户目前不活跃",
        'email_password_mismatch': "您输入的email或密码不正确",
        'username_password_mismatch': "您输入的用户名和/或密码不正确",
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LoginForm, self).__init__(*args, **kwargs)
        redirect = kwargs.get('initial', {}).get('redirect_url')
        if redirect:
            self.fields["redirect"] = forms.CharField(label='redirect', required=False,
                                                      widget=forms.TextInput(attrs={'type': 'hidden'},
                                                                            ), initial=redirect)
        if settings.CUSTOM_AUTHENTICATION_METHOD == "email":
            login_widget = forms.TextInput(attrs={'type': 'email',
                                                  'placeholder': '输入 E-mail 地址',
                                                  'autofocus': 'autofocus',
                                                  'class': 'form-control form-control-user'})
            login_field = forms.EmailField(label="E-mail",
                                           widget=login_widget)
            self.fields["email"] = login_field
        elif settings.CUSTOM_AUTHENTICATION_METHOD == "username":
            login_widget = forms.TextInput(attrs={'placeholder': "输入用户名",
                                                  'autofocus': 'autofocus',
                                                  'class': "form-control form-control-user"})

            login_field = forms.CharField(
                label="用户名",
                widget=login_widget,
                max_length=get_username_max_length())
            self.fields["username"] = login_field
        else:
            assert settings.CUSTOM_AUTHENTICATION_METHOD == "username_email"
            login_widget = forms.TextInput(attrs={'placeholder':
                                                  '用户名 or E-mail ',
                                                  'autofocus': 'autofocus',
                                                  'class': 'form-control form-control-user'})
            login_field = forms.CharField(label=pgettext("field label",
                                                         "Login"),
                                          widget=login_widget)
            self.fields["username_email"] = login_field
        # if app_settings.SESSION_REMEMBER is not None:
        #     del self.fields['remember']
    # def clean_login(self):
    #     login = self.cleaned_data['login']
    #     return login.strip()

    def clean(self):
        super(LoginForm, self).clean()
        if self._errors:
            return



