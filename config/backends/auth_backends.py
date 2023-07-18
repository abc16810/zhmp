# -*- coding: utf-8 -*

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from threading import local


UserModel = get_user_model()
_stash = local()


class MyBackend(ModelBackend):
	"""
	auth with username or email and both
	"""
	def authenticate(self, request, **credentials):
		username = credentials.get(UserModel.USERNAME_FIELD)
		email = credentials.get(UserModel.EMAIL_FIELD)
		password = credentials.get('password')
		user = None
		if (not username and not email) or not password:
			return
		if username:
			user = self.authenticate_by_username(username)
		elif email:
			user = self.authenticate_by_email(email)

		if user and self._check_password(user, password):
			return user

	@staticmethod
	def authenticate_by_email(email):
		q_dict = {UserModel.EMAIL_FIELD + '__exact': email.lower()}
		try:
			user = UserModel.object.get(**q_dict)
		except UserModel.DoesNotExist:
			user = None
		return user

	@staticmethod
	def authenticate_by_username(username):
		try:
			user = UserModel._default_manager.get_by_natural_key(username)
		except UserModel.DoesNotExist:
			user = None
		return user

	def _check_password(self, user, password):
		ret = user.check_password(password)
		if ret:
			ret = self.user_can_authenticate(user)
			if not ret:
				self._stash_user(user)
		return ret

	@classmethod
	def _stash_user(cls, user):
		global _stash
		ret = getattr(_stash, 'user', None)
		_stash.user = user
		return ret

	@classmethod
	def unstash_authenticated_user(cls):
		return cls._stash_user(None)
