import operator
from functools import reduce

from django.db.models import F, Value, IntegerField
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, \
    get_object_or_404, RetrieveAPIView, CreateAPIView
from rest_framework.response import Response

import mp.api.apps_serializers as serializers
from mp.api.utils import CustomObjectPermissions
from mp.apps.models import Apps
from mp.apps.models import ResourceGroup
from mp.users.models import MyUser
from mp.workflow.models import WorkFlow, WorkflowLog, WorkflowAuditLog


# ok v2
class AppGroupListDetailView(ListAPIView):
    """
    权限 查看业务组，查看业务，查看用户
    """
    serializer_class = serializers.SingleAppGroupListSerializer
    permission_classes = [CustomObjectPermissions]
    filter_backends = []
    search_param = 'search'
    search_terms = []

    def get_search_terms(self, request):
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # strip null characters
        params = params.replace(',', ' ')
        return params.split()

    def get_query_param(self, lookups):
        conditions = []
        for term in self.search_terms:
            queries = [
                Q(**{orm_lookup: term})
                for orm_lookup in lookups
            ]
            conditions.append(reduce(operator.or_, queries))
        return conditions


    def get_user_q(self, obj):
        orm_lookups = ['display__icontains']
        conditions = self.get_query_param(orm_lookups)
        if conditions:
            res = obj.member.filter(reduce(operator.and_, conditions))
        else:
            res = obj.member

        return res.annotate(object_id=F('id'), object_type=Value(0, output_field=IntegerField()), object_name=F('nickname'),
                            group_name=Value(obj.name)) \
            .values_list("object_id", "object_type", "object_name", "group_name")

    def get_app_q(self, obj):
        orm_lookups = ['name__icontains']
        conditions = self.get_query_param(orm_lookups)
        if conditions:
            res = obj.apps.filter(reduce(operator.and_, conditions))
        else:
            res = obj.apps
        print(res.annotate)

        return res.annotate(object_id=F('id'), object_type=Value(1, output_field=IntegerField()), object_name=F('name'),
                            group_name=Value(obj.name)) \
            .values_list("object_id", "object_type", "object_name", "group_name")

    def get_queryset(self):
        q = ResourceGroup.objects.filter(pk=self.kwargs['pk'])
        filter_kwargs = {'id': self.kwargs['pk']}
        obj = get_object_or_404(q, **filter_kwargs)
        self.search_terms = self.get_search_terms(self.request)
        print(self.search_terms)
        t = self.request.query_params.get('type', '')
        app_q = self.get_app_q(obj)
        use_q = self.get_user_q(obj)
        if t == "1":
            return app_q
        elif t == "0":
            return use_q
        else:
            entry_qs = app_q.union(use_q)
            entry_qs.model = ResourceGroup
        return entry_qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            print(page)
            serializer = self.get_serializer(page, many=True)
            print(serializer.data)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



class AppGroupUnassociatedView(RetrieveAPIView):
    """
    权限 查看业务组 查看业务，查看用户
    """
    serializer_class = serializers.SingleAppGroupUnassociatedSerializer
    filter_backends = []
    queryset = ResourceGroup.objects.all()

    @staticmethod
    def get_user_unassociated(obj):
        return MyUser.objects.exclude(resourcegroup=obj).annotate(
            object_id=F('pk'), object_name=F('nickname')).values('object_id', 'object_name')

    @staticmethod
    def get_app_unassociated(obj):
        return Apps.objects.exclude(resourcegroup=obj).annotate(
            object_id=F('pk'), object_name=F('name')).values('object_id', 'object_name')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        t = request.query_params.get('type', '')
        app_q = self.get_app_unassociated(instance)
        use_q = self.get_user_unassociated(instance)
        if t == "1":
            entry_qs =  app_q
        elif t == "0":
            entry_qs = use_q
        else:
            entry_qs = app_q.union(use_q)
        entry_qs.model = ResourceGroup
        serializer = self.get_serializer(list(entry_qs), many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()


class AddWorkFlow(CreateAPIView):
    serializer_class = serializers.AddWorkFlowSerializer
    permission_classes = [CustomObjectPermissions]
    queryset = WorkFlow.objects.all()
    # renderer_classes = [TemplateHTMLRenderer]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as f:
            print(f.detail)
            if f.detail.get('msg'):
                res = {'msg': f.detail.get('msg')}
            else:
                res = {'msg': '非法参数或者非法类型'}
            return Response(res, status=status.HTTP_201_CREATED, template_name="error.html")
        try:
            instance = serializer.save()
        except Exception as f:
            res = {'msg': str(f)}
            return Response(res, status=status.HTTP_201_CREATED, template_name="error.html")

        return HttpResponseRedirect(reverse("workflow-detail", kwargs={"pk": instance.pk}))


class AddWorkFlowList(ListAPIView):
    """
    工单列表
    """
    serializer_class = serializers.AddWorkFlowSerializer
    permission_classes = [CustomObjectPermissions]
    # queryset = WorkFlow.objects.all()
    ordering = ("-create_time",)  # 指定默认排序字段
    # renderer_classes = [JSONRenderer]

    def get_queryset(self):
        if self.request.user.is_superuser:
            q = WorkFlow.objects.all()
        else:
            q = WorkFlow.objects.filter(work_user=self.request.user.username)
        return q


class AddWorkFlowLog(ListAPIView):
    """
    list
    """
    serializer_class = serializers.WorkFlowLogListSerializer
    permission_classes = [CustomObjectPermissions]
    filter_backends = []
    lookup_field = 'pk'

    def get_queryset(self):
        workflow_id = self.request.query_params.get('workflow_id', '')
        workflow_type = self.request.query_params.get('workflow_type', '')
        try:
            audit_id = WorkflowAuditLog.objects.get(
                workflow_id=int(workflow_id), workflow_type=int(workflow_type)
            ).audit_id
            queryset = WorkflowLog.objects.filter(audit_id=audit_id)
        except Exception as f:
            queryset = WorkflowLog.objects.all()
        return queryset


class AppGroupUsersView(ListAPIView):
    queryset = MyUser.objects.all()
    serializer_class = serializers.UsersSerializer
    search_fields = ('username',)

    def get_queryset(self):
        q = super(AppGroupUsersView, self).get_queryset()
        group_id = self.kwargs[self.lookup_field]
        q = q.filter(resourcegroup__group_id=group_id)
        return q



