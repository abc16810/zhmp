
from django.db import models

from .utils import localtime


class TimestampsWithAuto(models.Model):
    """提供在模型上创建和更新的时间戳"""
    class Meta:
        abstract = True

    created_at = models.DateTimeField("创建时间", auto_now_add=True, editable=False)
    updated_at = models.DateTimeField("更新时间", auto_now=True, editable=False)


class TimestampsWithAutoAndDefault(models.Model):
    class Meta:
        abstract = True
    created_at = models.DateTimeField(db_index=True, default=localtime)
    updated_at = models.DateTimeField(auto_now=True)


class TimestampsWithDefault(models.Model):
    class Meta:
        abstract = True
    created_at = models.DateTimeField(default=localtime)
    updated_at = models.DateTimeField(default=localtime)


class TimestampsOpinionated(models.Model):
    """
    We want to have the following behavior:

    1. created_at is set by default, but can be overridden.
    2. updated_at is not set on initial creation (stays None).
    3. The service layer (check `model_update`) takes care of providing value to `updated_at`,
        if there's no value provided by the caller.
    """

    created_at = models.DateTimeField(default=localtime)
    updated_at = models.DateTimeField(blank=True, null=True)


