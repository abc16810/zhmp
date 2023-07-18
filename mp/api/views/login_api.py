import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.compat import set_cookie_with_token
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import BaseJSONWebTokenAPIView
import datetime
from mp.api.login_serializers import JSONWebTokenSerializer, LoginLogsListSerializer
from mp.api.utils import CustomObjectPermissions
from mp.common.mixins import ApiAuthMixin
from mp.users.models import LoginLogs


class UserJwtLoginApi(BaseJSONWebTokenAPIView):
    """
    登陆
    """
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            token = serializer.validated_data.get('token')
            redirect = serializer.validated_data.get('redirect')
            response_data = JSONWebTokenAuthentication. \
                jwt_create_response_payload(token, None, redirect, None)

            response = Response(response_data, status=status.HTTP_201_CREATED)

            if api_settings.JWT_AUTH_COOKIE:
                set_cookie_with_token(response, api_settings.JWT_AUTH_COOKIE, token)
                response.data['token'] = '已设置'
            if response.status_code == status.HTTP_201_CREATED:
                response.status_code = status.HTTP_200_OK
            return response

        else:
            msg = '用户名或者密码错误'
            r = serializer.errors.get('non_field_errors')
            if r and isinstance(r[0], ErrorDetail):
                msg = str(r[0])

            error_data = {
                "msg": msg,
                "code": 'error'
            }
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


class UserJwtLogoutApi(ApiAuthMixin, APIView):
    """登出"""
    def post(self, request, *args, **kwargs):
        # 更新user uuid
        user = request.user
        user.jwt_key = uuid.uuid4()
        user.full_clean()
        user.save(update_fields=["jwt_key"])

        response = Response()
        if settings.JWT_AUTH["JWT_AUTH_COOKIE"] is not None:
            response.delete_cookie(settings.JWT_AUTH["JWT_AUTH_COOKIE"])
        return response


class LoginLogsApi(ListAPIView):
    """
    登陆日志
    """
    serializer_class = LoginLogsListSerializer
    permission_classes = [CustomObjectPermissions]
    filterset_fields = ['action']
    search_fields = ['user_name', 'user_display', 'extra_info']

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = LoginLogs.objects.all()
        else:
            queryset = LoginLogs.objects.filter(user_name=self.request.user.username)
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            queryset = queryset.filter(action_time__range=(start_date, end_date))
        return queryset

# class UserMeApi(APIView):
#     authentication_classes = [
#         # CsrfExemptedSessionAuthentication,
#         # SessionAsHeaderAuthentication,
#         JSONWebTokenAuthentication,
#     ]
#
#     def get(self, request):
#         user = request.user
#         data = {
#             "id": user.id,
#             "email": user.email,
#             "is_active": user.is_active,
#             "is_superuser": user.is_superuser,
#         }
#         return Response(data)



