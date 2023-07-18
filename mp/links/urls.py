# -*- coding: utf-8 -*
from django.urls import path
from . import views


urlpatterns = [
    path("list", views.LinksList.as_view(), name="nav-list"),
]