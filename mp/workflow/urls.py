# -*- coding: utf-8 -*
from django.urls import path
from . import views



urlpatterns = [
    # 审批流程配置界面
    path("config/", views.WorkFlowConfigView.as_view(), name="workflow-config-view"),

    # path("auditor/", views.AppGroupAuditors.as_view(), name="workflow-auditor"),
    # path("auditor/change/", views.AppGroupAuditorsChange.as_view(), name="workflow-auditor-change"),

    # 工单申请界面
    path("add/", views.AddWorkFlowView.as_view(), name="workflow-add-view"),
    # 工单列表
    path("list/", views.WorkFlowListView.as_view(), name="workflow-list"),
    # 工单详情
    path("detail/<int:pk>/", views.WorkFlowDetailView.as_view(), name="workflow-detail")

]