from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django_q.admin import TaskAdmin, FailAdmin, ScheduleAdmin
from django_q.models import Failure, Schedule, Success
from django import forms
from mp.users.models import MyUser, MyGroup
from mp.apps.models import AppPorts, Apps, ResourceGroup
from mp.workflow.models import WorkFlowAudit, WorkflowLog, WorkflowAuditLog
from mp.links.models import Links


class MyAdminSite(AdminSite):
    site_header = 'MP后台管理'
    site_title = "MP"
    index_title = "MP"


admin_site = MyAdminSite(name='myadmin')


class MembershipInline(admin.TabularInline):
    model = ResourceGroup.user
    verbose_name = "业务组"
    verbose_name_plural = "业务组列表"


class UsersAdmin(UserAdmin):
    list_display = ('id', 'username', 'nickname', 'email', 'is_superuser', 'is_staff', 'is_active')
    search_fields = ('id', 'username', 'nickname', 'email')
    list_display_links = ('id', 'username',)
    ordering = ('id',)
    # inlines = [
    #     MembershipInline,
    # ]
    # 编辑页显示内容
    fieldsets = (
        ('认证信息', {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('nickname', 'email')}),
        ('权限信息', {'fields': ('is_superuser', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
        # ('资源组', {'fields': ('resource_group',)}),
        ('其他信息', {'fields': ('created_at',)}),
    )
    # 添加页显示内容
    add_fieldsets = (
        ('认证信息', {'fields': ('username', 'password1', 'password2')}),
        ('个人信息', {'fields': ('nickname', 'email')}),
        ('权限信息', {'fields': ('is_superuser', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
        #  ('资源组', {'fields': ('myuser__resourcegroup',)}),

    )
    filter_horizontal = ('groups', 'user_permissions')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')


admin_site.register(MyUser, UsersAdmin)
# admin.site.register(MyUser, UsersAdmin)


class GroupAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs["queryset"] = qs.select_related("content_type")
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


admin_site.register(MyGroup, GroupAdmin)


class ResourceGroupForm(forms.ModelForm):
    class Meta:
        model = ResourceGroup
        fields = '__all__'
        # exclude = ('views', 'update_date', 'create_date')  # 添加时排除字段


# 应用组管理
class ResourceGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group_paths', 'user')
    filter_horizontal = ("member",)
    form = ResourceGroupForm
    fieldsets = (
        ('必填选项', {
            'fields': ('name',)
        }),
        ('其他信息', {'fields': ('desc', 'member')}),
        ('上级部门', {'fields': ('parent', )}),
        ('用户', {'fields': ('user',)})

    )

    def group_paths(self, obj):
        return obj.node_paths()

    group_paths.short_description = "部门关系"


class AppsPortsInline(admin.TabularInline):
    model = AppPorts
    extra = 1


class AppsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'env', 'develop_user', 'deploy_user', 'deploy_path', 'deploy_mode', 'comment')
    search_fields = ['name', 'env', 'deploy_mode', 'deploy_path']
    list_filter = ('env',)

    inlines = [
        AppsPortsInline,
    ]
    filter_horizontal = ('assets',)


admin_site.register(Apps, AppsAdmin)


class WorkFlowAuditAdmin(admin.ModelAdmin):
    list_display = ('audit_id', 'apps_group_id', 'apps_group_name', 'workflow_type', 'auth_groups_name')

    def auth_groups_name(self, obj):
        audit_auth_groups_name = ""
        try:
            group_ids = obj.audit_auth_groups
            if group_ids:
                audit_auth_groups_name = "->".join(
                    [
                        MyGroup.objects.get(id=auth_group_id).name
                        for auth_group_id in group_ids.split(",")
                    ]
                )
            print(obj)
        except Exception as f:
            pass

        return audit_auth_groups_name

    auth_groups_name.short_description = "审批权限组列表"


admin_site.register(WorkFlowAudit, WorkFlowAuditAdmin)


class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'audit_id', 'operation_type', 'operation_info', 'operation_type_desc', 'operator_display', 'created_at']


admin_site.register(WorkflowLog, WorkflowLogAdmin)


class WorkflowAuditLogAdmin(admin.ModelAdmin):
    list_display = ['audit_id']


admin_site.register(WorkflowAuditLog, WorkflowAuditLogAdmin)


class LinksAdmin(admin.ModelAdmin):
    pass


admin_site.register(Links, LinksAdmin)


# admin_site.register(MyGroup, GroupAdmin)
Success._meta.verbose_name = "成功的任务"
Success._meta.verbose_name_plural = "成功的任务列表"
admin_site.register(Success, TaskAdmin)
Failure._meta.verbose_name = "失败的任务"
Failure._meta.verbose_name_plural = "失败的任务列表"
admin_site.register(Failure, FailAdmin)
Schedule._meta.verbose_name_plural = "调度任务列表"
admin_site.register(Schedule, ScheduleAdmin)
admin_site.register(ResourceGroup, ResourceGroupAdmin)