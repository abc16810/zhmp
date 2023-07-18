from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.generic import TemplateView, View
import logging

from .models import Idc, Cabinet, Assets, ServerAssets, SshUser


# Create your views here.


class Index(TemplateView):
    template_name = "index.html"


class IdcList(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "assets.view_idc"
    template_name = "assets/idc.html"

    @staticmethod
    def get_idc_zone():
        return set([x[0] for x in Idc.objects.values_list('idc_zone_name')])

    @staticmethod
    def get_idc_operator():
        return set([x[0] for x in Idc.objects.values_list('idc_operator')])

    def get_context_data(self, **kwargs):
        kwargs['idc_zone'] = list(self.get_idc_zone())
        kwargs['idc_operator'] = self.get_idc_operator()
        return super(IdcList, self).get_context_data(**kwargs)


class IdcDetail(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "assets.view_idc"
    template_name = "assets/idc-detail.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk')
        kwargs.update({
            'pk': pk
        })
        return super(IdcDetail, self).get_context_data(**kwargs)


class CabinetList(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = ["assets.view_cabinet", "assets.view_idc"]
    template_name = "assets/cabinet.html"

    @staticmethod
    def get_idc():
        return [x[0] for x in Idc.objects.values_list("idc_name")]

    def get_context_data(self, **kwargs):
        kwargs['idc'] = self.get_idc()
        return super(CabinetList, self).get_context_data(**kwargs)


class CabinetDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "assets/cabinet-detail.html"
    permission_required = "assets.view_cabinet"

    def get_context_data(self, *, object_list=None, **kwargs):
        pk = self.kwargs.get('pk')
        kwargs.update({
            'pk': pk
        })
        return super(CabinetDetailView, self).get_context_data(**kwargs)


class AssetList(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = ["assets.view_serverasset", "assets.view_assets"]
    template_name = "assets/asset.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = {
            'asset_type': dict(Assets.assets_type_choices),
            'asset_status': dict(Assets.assets_status),
            'asset_u': dict(Assets.assets_u),
            'asset_idc': Idc.objects.only('id', 'idc_name'),
            'asset_cabinet': Cabinet.objects.only('id', 'cabinet_name'),
            'platform': list(filter(lambda s: s['platform'], ServerAssets.objects.values('platform').distinct()))
        }
        kwargs.update(context)
        return super(AssetList, self).get_context_data(**kwargs)


class AssetDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "assets/asset_detail.html"
    permission_required = "assets.view_assets"

    def get_context_data(self, *, object_list=None, **kwargs):
        pk = self.kwargs.get('pk')
        kwargs.update({
            'pk': pk
        })
        return super(AssetDetailView, self).get_context_data(**kwargs)


# Ssh user
class AuthUserListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "assets/asset-user.html"
    permission_required = "assets.view_sshuser"


class AuthUserDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "assets/asset-user-detail.html"
    permission_required = "assets.view_sshuser"

    def get_context_data(self, *, object_list=None, **kwargs):
        pk = self.kwargs.get('pk')
        kwargs.update({
            'pk': pk
        })
        return super(AuthUserDetailView, self).get_context_data(**kwargs)


# 弃用 改为API
# 检索IDC api
# @method_decorator(csrf_exempt, name='dispatch')
# class IdcSearch(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "assets.view_idc"
#     http_method_names = ['get', 'post']
#
#     def get(self, request, *args, **kwargs):
#         return JsonResponse({"code": 200, 'data': []})
#
#     def query(self, **kwargs):
#         return Idc.objects.filter(**kwargs)
#
#     def post(self, request, *args, **kwargs):
#         zone_name = request.POST.get('zone_name')
#         operator = request.POST.get('operator')
#         limit = int(request.POST.get('limit', 0))
#         offset = int(request.POST.get('offset', 0))
#         search = request.POST.get('search')
#         res = dict()
#         if zone_name:
#             res['idc_zone_name'] = zone_name
#         if operator:
#             res['idc_operator'] = operator
#         idc = self.query(**res)
#         # 过滤搜索项，模糊检索项包括提交名称，区域
#         if search:
#             idc = idc.filter(Q(idc_zone_name__icontains=search) | Q(idc_name__icontains=search))
#         count = idc.count()
#         limit = offset + limit
#         limit = limit if limit else None
#         idc_list = idc.order_by('-created_at')[offset:limit].values("id", "idc_name", "idc_zone_name", "idc_operator",
#                                                                      "idc_contact",
#                                                                      "idc_phone", "idc_address", "idc_bandwidth", "idc_comment")
#         rows = [row for row in idc_list]
#         result = {"total": count, "rows": rows}
#         return JsonResponse(result)


# 弃用 改为API
# 检索机柜 api
# @method_decorator(csrf_exempt, name='dispatch')
# class CabinetSearch(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "assets.view_cabinet"
#     http_method_names = [ 'post']
#
#     def get(self, request, *args, **kwargs):
#         return JsonResponse({"code": 200, 'data': []})
#
#     def query(self, **kwargs):
#         return Cabinet.objects.filter(**kwargs)
#
#     def post(self, request, *args, **kwargs):
#         idc = request.POST.get('idc')
#         operator = request.POST.get('operator')
#         start_date = request.POST.get('start_date')
#         end_date = request.POST.get('end_date')
#         limit = int(request.POST.get('limit', 0))
#         offset = int(request.POST.get('offset', 0))
#         search = request.POST.get('search')
#         res = dict()
#         if idc:
#             res['idc__idc_name'] = idc
#         if operator:
#             res['idc_operator'] = operator
#
#         # 时间
#         if start_date and end_date:
#             end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
#             res['created_at__range'] = (start_date, end_date)
#         cabinet = self.query(**res)
#         # 过滤搜索项，模糊检索项包括提交名称，区域
#         if search:
#             cabinet = cabinet.filter(Q(cabinet_name__icontains=search) | Q(cabinet_comment__icontains=search))
#         count = cabinet.count()
#         limit = offset + limit
#         limit = limit if limit else None
#         idc_list = cabinet.order_by('-created_at')[offset:limit].values("id",
#                                                                          "idc__idc_name",
#                                                                          "cabinet_name",
#                                                                          "cabinet_band",
#                                                                          "cabinet_cost",
#                                                                          "expired_time",
#                                                                          "cabinet_comment")
#         rows = [row for row in idc_list]
#         result = {"total": count, "rows": rows}
#         return JsonResponse(result)





## api
# @method_decorator(csrf_exempt, name='dispatch')
# class AssetSearch(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = ["assets.view_serverasset", "assets.view_assets"]
#     http_method_names = ['post']
#
#     def query(self, **kwargs):
#         return Assets.objects.filter(**kwargs).select_related('serverassets')
#
#     def post(self, request, *args, **kwargs):
#         assets_type = request.POST.get('asset_type')
#         assets_idc = request.POST.get('asset_idc')
#         assets_status = request.POST.get('asset_status')
#
#         limit = int(request.POST.get('limit', 0))
#         offset = int(request.POST.get('offset', 0))
#         search = request.POST.get('search')
#         res = dict()
#         if assets_type and assets_type in dict(Assets.assets_type_choices).keys():
#             res['assets_type'] = assets_type
#         if assets_idc and assets_idc.isdigit():
#             res['jg__idc'] = assets_idc
#         if assets_status and assets_status in dict(Assets.assets_status).keys():
#             res['status'] = assets_status
#         asset = self.query(**res)
#         # 过滤搜索项，模糊检索项包括提交名称，区域
#         if search:
#             asset = asset.filter()
#         count = asset.count()
#         limit = offset + limit
#         limit = limit if limit else None
#         asset_list = asset.order_by('-created_at')[offset:limit].values("id",
#                                                                          "number",
#                                                                          "assets_type",
#                                                                          "serverassets__ip",
#                                                                          "serverassets__os",
#                                                                          "serverassets__os_version",
#                                                                          "serverassets__os_arch",
#                                                                          "serverassets__kernel",
#                                                                          "serverassets__cpu_number",
#                                                                          # "jg__cabinet_name",
#                                                                          "status",
#                                                                          "jg__idc__idc_name",
#                                                                          )
#         rows = [row for row in asset_list]
#         result = {"total": count, "rows": rows}
#         return JsonResponse(result)


## 资产detail api




