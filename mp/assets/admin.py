from django.contrib import admin
from django.utils.html import format_html

from mp.admin.manager import admin_site
from .forms import SshUserAdminForm
from .models import Idc, Cabinet, Assets, ServerAssets, SshUser, DISK, NIC, RAM


class IdcAdmin(admin.ModelAdmin):
    list_display = ('idc_name', 'idc_zone_name', 'idc_operator', 'idc_address', 'idc_contact', 'idc_phone', 'idc_bandwidth')
    search_fields = ('idc_name', 'idc_zone_name', 'idc_contact')
    list_display_links = ('idc_name',)
    ordering = ('id',)
    list_filter = ('idc_zone_name',)
    # 编辑页显示内容
    fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('idc_name', 'idc_zone_name', 'idc_operator', 'idc_contact', 'idc_address')
        }),
        ('其它信息', {
            'classes': ('collapse',),
            'fields': ('idc_phone', 'idc_bandwidth'),
        }),
        ('备注', {
            'classes': ('collapse',),
            'fields': ('idc_comment',),
        }),
    )


class CabinetAdmin(admin.ModelAdmin):
    list_display = ('idc', 'cabinet_name', 'cabinet_band', 'cabinet_cost', 'expired_time', 'cabinet_comment')
    search_fields = ('cabinet_name',)
    list_display_links = ('cabinet_name',)
    ordering = ('id',)
    list_filter = ('cabinet_name',)
    # 编辑页显示内容
    fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('idc', 'cabinet_name', 'expired_time')
        }),
        ('其它信息', {
            'classes': ('collapse',),
            'fields': ('cabinet_band', 'cabinet_cost'),
        }),
        ('备注', {
            'classes': ('collapse',),
            'fields': ('cabinet_comment',),
        }),
    )


class AssetsAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if not change and not form.cleaned_data.get("created_by"):
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)


class ServerAssetsAdmin(admin.ModelAdmin):
    pass


class DiskAdmin(admin.ModelAdmin):
    list_display = ('assets', 'name', 'wwn', 'host', 'device_size', 'device_vendor', 'device_model',
                    'comment')
    search_fields = ('name', 'wwn')
    # list_display_links = ('idc_name',)
    ordering = ('id',)
    list_filter = ('device_vendor',)


class NicAdmin(admin.ModelAdmin):
    list_display = ('assets', 'name', 'mac', 'ip', 'netmask', 'promisc', 'is_ipv4_default', 'gateway', 'speed', 'types',
                    'module', 'is_active', 'comment')
    search_fields = ('name', 'ip')
    # list_display_links = ('idc_name',)
    ordering = ('id',)

    def is_active(self, obj):
        if obj.active:
            img = "/static/admin/img/icon-yes.svg"
            alt = "True"
        else:
            img = "/static/admin/img/icon-no.svg"
            alt = "False"

        return format_html('<img src="{}" alt="{}">', img, alt)

    is_active.short_description = "激活"


class RamAdmin(admin.ModelAdmin):
    list_display = ('assets', 'sn', 'size', 'model', 'slot', 'manufactory', 'speed', 'ram_max_size', 'ram_max_slot',
                    'comment')
    search_fields = ('sn', 'comment')
    # list_display_links = ('idc_name',)
    ordering = ('id',)
    list_filter = ('size',)


class SshUserAdmin(admin.ModelAdmin):
    form = SshUserAdminForm
    list_display = ('sign', 'username', 'port', 'is_passwd', 'is_key', 'pkey_path',  'created_by', 'comment')

    def is_passwd(self, obj):
        if obj.password:
            img = "/static/admin/img/icon-yes.svg"
            alt = "True"
        else:
            img = "/static/admin/img/icon-no.svg"
            alt = "False"

        return format_html('<img src="{}" alt="{}">', img, alt)

    is_passwd.short_description = "密码"

    def is_key(self, obj):
        if obj.pkey:
            img = "/static/admin/img/icon-yes.svg"
            alt = "True"
        else:
            img = "/static/admin/img/icon-no.svg"
            alt = "False"

        return format_html('<img src="{}" alt="{}">', img, alt)

    is_key.short_description = "密钥"

    def save_model(self, request, obj, form, change):
        if not change and not form.cleaned_data.get("created_by"):
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)


admin_site.register(Idc, IdcAdmin)
admin_site.register(Cabinet, CabinetAdmin)
admin_site.register(Assets, AssetsAdmin)
admin_site.register(ServerAssets, ServerAssetsAdmin)
admin_site.register(SshUser, SshUserAdmin)
admin_site.register(DISK, DiskAdmin)
admin_site.register(NIC, NicAdmin)
admin_site.register(RAM, RamAdmin)
