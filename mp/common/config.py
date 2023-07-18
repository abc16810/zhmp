# -*- coding: utf-8 -*
from django.conf import settings


# class SysConfig(object):
#     def __init__(self):
#         self.sys_config = {}
#         self.get_all_config()
#
#     def get_all_config(self):
#         try:
#             # 获取系统配置信息
#             all_config = Config.objects.all().values('item', 'value')
#             sys_config = {}
#             for items in all_config:
#                 if items['value'] in ('true', 'True'):
#                     items['value'] = True
#                 elif items['value'] in ('false', 'False'):
#                     items['value'] = False
#                 sys_config[items['item']] = items['value']
#             self.sys_config = sys_config
#         except Exception as m:
#             logger.error(f"获取系统配置信息失败:{m}{traceback.format_exc()}")
#             self.sys_config = {}


class AppSettings(object):
	class AuthenticationMethod:
		USERNAME = 'username'
		EMAIL = 'email'
		USERNAME_EMAIL = 'username_email'

	def __init__(self, prefix):
		self.prefix = prefix

	def _setting(self, name, flt):
		getter = lambda name, flt: getattr(settings, name, flt)
		return getter(self.prefix + name, flt)

	@property
	def AUTHENTICATION_METHOD(self):
		ret = self._setting("AUTHENTICATION_METHOD",
							self.AuthenticationMethod.USERNAME)
		return ret

	@property
	def USERNAME_FIELD(self):
		return self._setting('USERNAME_FIELD', 'username')

	@property
	def PASSWORD_INPUT_RENDER_VALUE(self):
		return self._setting("PASSWORD_INPUT_RENDER_VALUE", False)

	@property
	def SESSION_REMEMBER(self):
		return self._setting("SESSION_REMEMBER", None)

	@property
	def LOGIN_ATTEMPTS_LIMIT(self):
		return self._setting('LOGIN_ATTEMPTS_LIMIT', 5)

	@property
	def LOGIN_ATTEMPTS_TIMEOUT(self):
		return self._setting('LOGIN_ATTEMPTS_TIMEOUT', 60 * 5)

	@property
	def USER_MODEL_EMAIL_FIELD(self):
		return self._setting('USER_MODEL_EMAIL_FIELD', 'email')

	@property
	def USER_MODEL_USERNAME_FIELD(self):
		return self._setting('USER_MODEL_USERNAME_FIELD', 'username')

	@property
	def SESSION_COOKIE_AGE(self):
		return self._setting('SESSION_COOKIE_AGE', settings.SESSION_COOKIE_AGE)


app_settings = AppSettings('MP_')
