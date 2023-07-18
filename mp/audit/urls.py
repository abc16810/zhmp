# -*- coding: utf-8 -*
from django.urls import path
from .logs import LoginLogView
from . import views


urlpatterns = [
    path("log", LoginLogView.as_view(), name="audit-log")
]
