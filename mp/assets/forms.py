from django.forms import ModelForm, Textarea, CharField, PasswordInput
from .models import SshUser


class PasswordField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = PasswordInput(render_value=False,
                                         attrs={'placeholder': kwargs.get("label"),
                                                'class': 'form-control',})
        super(PasswordField, self).__init__(*args, **kwargs)


class SshUserAdminForm(ModelForm):
    password = PasswordField(label="输入密码", required=False)

    class Meta:
        model = SshUser
        exclude = ('created_by',)
        help_texts = {
            'username': '请输入远程用户名',
            'port': '远程主机开放的端口号 默认22',
            'password': '密码，如果使用私钥连接可以不填',
            'pkey': '剪贴私钥,或者上传私钥文件',
            'pkey_password': '私钥密码如果有，请输入'

        }
        widgets = {
            'PKey': Textarea(attrs={'cols': 40, 'rows': 8}),
        }

    def clean(self):
        super(SshUserAdminForm, self).clean()
        password = self.cleaned_data.get('password')
        pkey_path = self.cleaned_data.get('pkey_path')
        pkey = self.cleaned_data.get('pkey')
        if  not password and not any((pkey_path,pkey)):
            msg = '密码和密钥必须填一项或者上传密钥文件'
            self.add_error('password', msg)
            self.add_error('pkey', msg)
        return self.cleaned_data
