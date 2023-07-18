import datetime
import logging

from django.db.models import Prefetch
from django_q.models import Schedule
from django_q.tasks import schedule, async_task
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

import mp.api.asset_serializers as serializers
from mp.api.utils import CustomObjectPermissions
from mp.assets.models import Idc, Cabinet, Assets, DISK, RAM, NIC, SshUser

logger = logging.getLogger('root')


class IdcList(ListAPIView):
    serializer_class = serializers.IdcSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = Idc.objects.all()
    search_fields = ['idc_name', 'idc_operator', 'idc_comment']
    filterset_fields = ['idc_zone_name', 'idc_operator']


class IdcDetail(RetrieveAPIView):
    serializer_class = serializers.IdcSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = Idc.objects.all()


class CabinetList(ListAPIView):
    serializer_class = serializers.CabinetSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = Cabinet.objects.prefetch_related(
        Prefetch('asset', queryset=Assets.objects.only('id', 'jg'), to_attr='to_assets'),
    ).select_related('idc')
    search_fields = ['cabinet_name', 'cabinet_comment']
    filterset_fields = ['idc__idc_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            queryset = queryset.filter(created_at__range=(start_date, end_date))
        return queryset


class CabinetDetail(RetrieveAPIView):
    serializer_class = serializers.CabinetSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = Cabinet.objects.prefetch_related(
        Prefetch('asset', queryset=Assets.objects.only('id', 'jg'), to_attr='to_assets'),
    ).select_related('idc')


class Base:
    queryset = Assets.objects.all().select_related('serverassets').prefetch_related(
        Prefetch('jg', queryset=Cabinet.objects.only('id', 'cabinet_name'), to_attr='to_jg'),
        Prefetch('ram', queryset=RAM.objects.all(), to_attr='to_ram'),
        Prefetch('nic', queryset=NIC.objects.all(), to_attr='to_nic'),
        Prefetch('disk', queryset=DISK.objects.all(), to_attr='to_disk'),
    )


class AssetsList(Base, ListAPIView):
    serializer_class = serializers.AssetsSerializer
    permission_classes = [CustomObjectPermissions]

    filterset_fields = ['assets_type', 'status', 'jg']
    search_fields = ['number', 'sn', 'comment']


class AssetsDetail(Base, RetrieveAPIView):
    serializer_class = serializers.AssetsSerializer
    permission_classes = [CustomObjectPermissions]


class AssetAnsibleUpdate(APIView):
    permission_classes = [CustomObjectPermissions]
    queryset = Assets.objects.all().select_related('serverassets')

    def post(self, request, format=None):
        ids = request.POST.getlist('ids[]')
        time = request.POST.get('time')  # '06/13/2023 4:42 PM'
        msg = '任务提交成功'
        code = 200
        try:
            time_struct = datetime.datetime.strptime(time, "%m/%d/%Y %H:%M %p")
            if time.split(' ')[-1].lower() == 'pm' and time_struct.hour < 12:
                time_struct = time_struct + datetime.timedelta(hours=12)
            if time_struct <= datetime.datetime.now():
                msg = "任务时间不正确"
                code = 400
            else:
                # 调度任务
                async_task('mp.assets.tasks.ansible_batch_update_memory', ids,
                           group="Ansible_Batch_Get_Mem",
                           hook='mp.assets.hooks.get_mem_result')
                schedule('mp.assets.tasks.ansible_batch_update',
                         ids,
                         hook='mp.assets.hooks.get_result',
                         schedule_type=Schedule.ONCE,
                         next_run=time_struct,
                         name="Ansible_Batch_Setup"
                         )

        except Exception as err:
            logger.error('内部错误 %s' % str(err))
            msg = "错误"
            code = 400
        data = {'detail': msg, 'code': code}
        return Response(data, status=200)


class SshuserList(ListAPIView):
    serializer_class = serializers.SshuserSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = SshUser.objects.all()
    search_fields = ['sign', 'username', 'comment']
    # filterset_fields = ['idc_zone_name', 'idc_operator']


class SshuserDetail(RetrieveAPIView):
    serializer_class = serializers.SshuserSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = SshUser.objects.all()
