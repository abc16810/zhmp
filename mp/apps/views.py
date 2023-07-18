from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import TemplateView, View, DetailView
from mp.apps.models import Apps, ResourceGroup
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import datetime


class AppsList(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "apps.view_apps"
    template_name = "apps/apps-list.html"

    @staticmethod
    def get_develop_users():
        return set([x[0] for x in Apps.objects.distinct().values_list('develop_user')])

    @staticmethod
    def get_apps_group():
        return [(group.id, group.node_paths()) for group in ResourceGroup.objects.filter(parent__isnull=False)]
        # return set([x[0] for x in ResourceGroup.objects.values_list('name')])

    def get_context_data(self, **kwargs):
        res = {
            'apps_env': dict(Apps.ENV_CHOICES),
            'deploy_mode': dict(Apps.DEPLOY_MODE_CHOICES),
            'develop_users': self.get_develop_users(),
            'apps_group': self.get_apps_group()

        }
        kwargs.update(res)
        return super(AppsList, self).get_context_data(**kwargs)


class AppsSearch(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = ["apps.view_apps"]
    http_method_names = ['post']

    def query(self, **kwargs):
        return Apps.objects.filter(**kwargs)

    def post(self, request, *args, **kwargs):
        apps_env = request.POST.get('apps_env')
        deploy_mode = request.POST.get('deploy_mode')
        develop_user = request.POST.get('develop_user')
        app_group = request.POST.get('app_group')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        limit = int(request.POST.get('limit', 0))
        offset = int(request.POST.get('offset', 0))
        search = request.POST.get('search')
        res = {}
        if apps_env:
            res['env'] = apps_env
        if deploy_mode:
            res['deploy_mode'] = deploy_mode
        if develop_user:
            res['develop_user'] = develop_user
        if app_group:
            res["resourcegroup__name"] = app_group
        # 时间
        if start_date and end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            res['action_time__range'] = (start_date, end_date)
        app = self.query(**res)
        # 过滤搜索项，模糊检索项包括提交名称，区域
        if search:
            app = app.filter(Q(user_name__icontains=search) | Q(user_display__icontains=search))
        count = app.count()
        limit = offset + limit
        limit = limit if limit else None
        audit_list = app.order_by('-create_date')[offset:limit].values("id", "name", "env", "develop_user",
                                                                       "deploy_user","resourcegroup__group_name",
                                                                       "deploy_path", "deploy_mode", "assets__ip",
                                                                       "up_date", "down_date"

                                                                        )
        rows = [row for row in audit_list]
        result = {"total": count, "rows": rows}
        print(result)
        return JsonResponse(result)


## ok
class AppGroupList(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "apps.view_resourcegroup"
    template_name = "apps/app_group.html"

    def get_context_data(self, **kwargs):
        context = {

            'users': get_user_model().objects.only('id', 'username', 'nickname')

        }
        kwargs.update(context)
        return super(AppGroupList, self).get_context_data(**kwargs)


## ok
class AppGroupDetail(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ResourceGroup
    template_name = "apps/app_group_detail.html"
    permission_required = ("apps.view_resourcegroup", "apps.delete_resourcegroup")

    def get_context_data(self, **kwargs):
        return super(AppGroupDetail, self).get_context_data(**kwargs)







