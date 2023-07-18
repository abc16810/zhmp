from django.db.models import Prefetch
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.contrib.auth import get_user_model
import mp.api.apps_serializers as serializers
from mp.api.utils import CustomObjectPermissions
from mp.apps.models import Apps, ServerAssets
from mp.apps.models import ResourceGroup


class AppGroupListView(ListAPIView):
    serializer_class = serializers.AppGroupSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = ResourceGroup.objects.all().select_related('user').prefetch_related(
        Prefetch('apps', queryset=Apps.objects.only('id', 'name')),
        Prefetch('member', queryset=get_user_model().objects.only('id', 'username',
                                                                  'email', 'is_superuser', 'is_active', 'nickname'),
                 to_attr='to_member')
    )

    filterset_fields = ['user']
    # 搜索字段
    search_fields = ('name',)


class AppGroupDetailView(RetrieveAPIView):
    serializer_class = serializers.AppGroupSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = ResourceGroup.objects.all().select_related('user').prefetch_related(
        Prefetch('apps', queryset=Apps.objects.only('id', 'name')),
        Prefetch('member', queryset=get_user_model().objects.only('id', 'username',
                                                                  'email', 'is_superuser', 'is_active', 'nickname'),
                 to_attr='to_member')
    )


class AppsListView(ListAPIView):
    serializer_class = serializers.AppsSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = Apps.objects.all().select_related('group').prefetch_related(
        Prefetch('assets', queryset=ServerAssets.objects.all(), to_attr='to_assets'),
    )

    filterset_fields = ['group', 'deploy_mode', 'env', 'develop_user']
    # # 搜索字段
    search_fields = ('name', 'comment')












