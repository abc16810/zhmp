# -*- coding: utf-8 -*
from django.urls import path
from . import views


urlpatterns = [
    path("list/", views.AppsList.as_view(), name="apps-list"),
    path("search/", views.AppsSearch.as_view(), name="apps-search"),

    path("group/", views.AppGroupList.as_view(), name="apps-group"),
    path("group/<int:pk>/", views.AppGroupDetail.as_view(), name="apps-group-detail")
]