# -*- coding: utf-8 -*
from rest_framework.pagination import LimitOffsetPagination


class MyLimitOffsetPagination(LimitOffsetPagination):
	max_limit = 10
