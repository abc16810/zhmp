# -*- coding: utf-8 -*
from rest_framework_jwt.views import obtain_jwt_token
from django.urls import path
from .views import LoginView


urlpatterns = [
    path("login/", LoginView.as_view(), name="login-html"),
]
