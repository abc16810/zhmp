
# api
REST_FRAMEWORK = {
    # 默认django的权限
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',  # search_fields 关键字search
        'rest_framework.filters.OrderingFilter',  # ordering_fields 关键字ordering  如果没有设置 ORDERING_PARAM
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # 'ORDERING_PARAM': 'order',
    'DEFAULT_PAGINATION_CLASS': 'mp.api.pagination.MyLimitOffsetPagination',
    'PAGE_SIZE': 10,
}