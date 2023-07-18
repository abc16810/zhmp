from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import TemplateView, View, ListView
from mp.links.models import Links
from mp.apps.models import Apps
from django.db.models import Q, Count
from django.http import JsonResponse
import datetime


class LinksList(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "links.view_links"
    template_name = "nav/list.html"


    @staticmethod
    def get_list_links():
        return Links.objects.values("id", 'nav_name', 'nav_type', 'nav_url', 'nav_desc', 'nav_img')

    @staticmethod
    def get_link_type():
        return set([x[0] for x in Links.objects.distinct().values_list('nav_type')])

    def get_context_data(self, **kwargs):
        res = {
            'link_type': dict(Links.links_type_choices).values(),
            'links_list': self.get_list_links()
        }
        kwargs.update(res)
        aa = super(LinksList, self).get_context_data(**kwargs)
        print(aa)
        return aa