# -*- coding: utf-8 -*
from django.urls import path
from .views import Index, IdcList, CabinetList, \
	CabinetDetailView, AssetList, AuthUserListView, AssetDetailView, IdcDetail, AuthUserDetailView


urlpatterns = [
	path("", Index.as_view(), name="index"),
	path("bashboard", Index.as_view(), name="bashboard"),

	path("assets/idc/", IdcList.as_view(), name="idc"),
	path("assets/idc/<int:pk>/", IdcDetail.as_view(), name="idc-detail"),

	path("assets/cabinet/", CabinetList.as_view(), name="cabinet"),
	path("assets/cabinet/<pk>/", CabinetDetailView.as_view(), name="cabinet-detail"),

	path("assets/asset/", AssetList.as_view(), name="asset"),
	path("assets/asset/<int:pk>/", AssetDetailView.as_view(), name="asset-detail"),

	path("assets/user/", AuthUserListView.as_view(), name="asset-user"),
	path("assets/user/<int:pk>/", AuthUserDetailView.as_view(), name="asset-user-detail"),
]