from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required


@login_required
def response_403_error_handler(request, exception=None):
    if request.method == 'GET':
        return render(request, '403.html', {"user": request.user})
    else:
        return JsonResponse({'msg': "你没有权限操作此项", "code": 403, 'data': []})


def response_404_error_handler(request, exception=None):
    if request.method == 'GET':
        return render(request, '404.html', {"user": request.user})
    else:
        return JsonResponse({'msg': "你访问的地址不存在", "code": 404, 'data': []})


def response_500_error_handler(request, exception=None):
    if request.method == 'GET':
        return render(request, '500.html', {"user": request.user})
    else:
        return JsonResponse({'msg': "系统错误", "code": 404, 'data': []})
