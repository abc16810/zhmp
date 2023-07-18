"""mp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from mp.admin.manager import admin_site
from django.conf.urls.static import static
from django.views.static import serve
from .error import response_403_error_handler, response_404_error_handler, response_500_error_handler


urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/', include('mp.api.urls')),
    # html
    path('user/', include('mp.users.urls')),
    path('audit/', include('mp.audit.urls')),
    path('apps/', include('mp.apps.urls')),
    path('nav/', include('mp.links.urls')),
    path('workflow/', include('mp.workflow.urls')),
    path('', include('mp.assets.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),

    ]


handler403 = response_403_error_handler
handler404 = response_404_error_handler
handler500 = response_500_error_handler
