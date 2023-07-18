from config.env import env

from .base import *  # noqa


DEBUG = env.bool("DJANGO_DEBUG", default=False)


SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])


# SESSION_COOKIE_SECURE = False
# CSRF_COOKIE_SECURE = False
# CSRF_COOKIE_SAMESITE = None

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

