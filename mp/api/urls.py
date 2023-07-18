from django.urls import path, include

from mp.api.views import login_api, asset_api, apps_api, workflow_api

urlpatterns = [
    # 登陆登出
    path("auth/jwt/", include(
        (
            [
                path("login/", login_api.UserJwtLoginApi.as_view(), name="login"),
                path("logout/", login_api.UserJwtLogoutApi.as_view(), name="logout"),
                path("logs/", login_api.LoginLogsApi.as_view(), name="logs")
            ],
            "jwt",
        )
    )),
    # path("me/", login_api.UserMeApi.as_view(), name="me"),
    # 用户url
    # path("users/", include(("mp.users.urls", "users"))),
    path("asset/", include(
        (
            [
                path("idc/search/", asset_api.IdcList.as_view(), name="idc"),
                path("idc/<int:pk>/", asset_api.IdcDetail.as_view(), name="idc-detail"),
                path("cabinet/search/", asset_api.CabinetList.as_view(), name="cabinet"),
                path("cabinet/<int:pk>/", asset_api.CabinetDetail.as_view(), name="cabinet-detail"),
                path("assets/search/", asset_api.AssetsList.as_view(), name="assets"),
                path("assets/<int:pk>/", asset_api.AssetsDetail.as_view(), name="assets-detail"),
                path("update/",  asset_api.AssetAnsibleUpdate.as_view(), name='update'),  # 批量更新资产
                path("sshuser/search/", asset_api.SshuserList.as_view(), name="sshuser"),
                path("sshuser/<int:pk>/", asset_api.SshuserDetail.as_view(), name="sshuser-detail"),
            ],
            "api-asset",
        )
    )),

    # 业务组
    path("apps/", include(
        (
            [
                path("group/search/", apps_api.AppGroupListView.as_view(), name="group-list"),
                path("group/<int:pk>/", apps_api.AppGroupDetailView.as_view(), name="group-detail"),
                path("search/", apps_api.AppsListView.as_view(), name="list")
            ],
            "api-apps",
        )
    )),

    # 工单申请API
    path("workflow/", include(
        (
            [
                path("auditor/", workflow_api.AppsGroupAuditors.as_view(), name="auditor"),
                path("approve/", workflow_api.AppGroupAuditorsChangeOrCreate.as_view(), name="approve"),
                path('add/', workflow_api.AddWorkFlow.as_view(), name='add'),
                path('list/', workflow_api.WorkFlowList.as_view(), name='list'),
                path('logs/', workflow_api.WorkFlowLog.as_view(), name='logs'),
                path('passed/', workflow_api.WorkFlowPassed.as_view(), name='passed'),   # 审核通过
                path('cancel/', workflow_api.WorkFlowCancel.as_view(), name='cancel'),
                path('timing/', workflow_api.WorkFlowTiming.as_view(), name='timing'),   # 定时执行
                path('execute/', workflow_api.WorkFlowExec.as_view(), name='execute'),   # 立即执行
                path('handler/', workflow_api.WorkFlowhandler.as_view(), name='handler'),  # 处理工单
                path('finish/', workflow_api.WorkFlowFinish.as_view(), name='finish'),
            ],
            "api-workflow",
        )
    )),

    # # 业务组下关联的用户和业务
    # path('app/group/<int:pk>/', app_api.AppGroupListDetailView.as_view(), name='api-app-group-detail'),
    # # 业务组下未关联的用户和业务
    # path('app/group/unassociated/<int:pk>/', app_api.AppGroupUnassociatedView.as_view(), name='api-app-group-un'),
    # # path('workflow/add/', app_api.AddWorkFlow.as_view(), name='api-workflow-add'),
    # path('workflow/list/', app_api.AddWorkFlowList.as_view(), name='api-workflow-list'),
    # # path('workflow/logs/', app_api.AddWorkFlowLog.as_view(), name='api-workflow-logs'),
    # # 业务下的用户
    # # path('app/group/user/<int:pk>/', app_api.AppGroupUsersView.as_view(), name='api-app-group-userlist'),

]

