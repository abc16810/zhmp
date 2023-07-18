# from django.contrib import admin
# from django.contrib.admin import AdminSite
# from django.contrib.auth.admin import UserAdmin
# from account.models import MyUser, MyGroup
# from django_q.models import Failure, OrmQ, Schedule, Success
# from django_q.admin import TaskAdmin, FailAdmin, ScheduleAdmin
# from apps.models import AppPorts, Apps, ResourceGroup
# from links.models import Links
#
#
# class MyAdminSite(AdminSite):
#     site_header = 'MP后台管理'
#     site_title = "MP"
#     index_title = "MP"
#
# admin_site = MyAdminSite(name='myadmin')
#
# class MembershipInline(admin.TabularInline):
#     model = ResourceGroup.user.through
#     verbose_name = "业务组"
#     verbose_name_plural = "业务组列表"
#
#
#
# class UsersAdmin(UserAdmin):
#     list_display = ('id', 'username', 'display', 'email', 'is_superuser', 'is_staff', 'is_active')
#     search_fields = ('id', 'username', 'display', 'email')
#     list_display_links = ('id', 'username',)
#     ordering = ('id',)
#     inlines = [
#         MembershipInline,
#     ]
#     # 编辑页显示内容
#     fieldsets = (
#         ('认证信息', {'fields': ('username', 'password')}),
#         ('个人信息', {'fields': ('display', 'email', 'ding_user_id', 'wx_user_id', 'feishu_open_id')}),
#         ('权限信息', {'fields': ('is_superuser', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
#         # ('资源组', {'fields': ('resource_group',)}),
#         ('其他信息', {'fields': ('date_joined',)}),
#     )
#     # 添加页显示内容
#     add_fieldsets = (
#         ('认证信息', {'fields': ('username', 'password1', 'password2')}),
#         ('个人信息', {'fields': ('display', 'email', 'ding_user_id', 'wx_user_id', 'feishu_open_id')}),
#         ('权限信息', {'fields': ('is_superuser', 'is_active', 'is_staff', 'groups', 'user_permissions')}),
#       #  ('资源组', {'fields': ('myuser__resourcegroup',)}),
#
#     )
#     filter_horizontal = ('groups', 'user_permissions')
#     list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
#
# admin_site.register(MyUser, UsersAdmin)
# #admin.site.register(MyUser, UsersAdmin)
#
#
# class GroupAdmin(admin.ModelAdmin):
#     search_fields = ("name",)
#     ordering = ("name",)
#     filter_horizontal = ("permissions",)
#
#     def formfield_for_manytomany(self, db_field, request=None, **kwargs):
#         if db_field.name == "permissions":
#             qs = kwargs.get("queryset", db_field.remote_field.model.objects)
#             # Avoid a major performance hit resolving permission names which
#             # triggers a content_type load:
#             kwargs["queryset"] = qs.select_related("content_type")
#         return super().formfield_for_manytomany(db_field, request=request, **kwargs)
#
#
#
# # 应用组管理
# class ResourceGroupAdmin(admin.ModelAdmin):
#     list_display = ('group_id', 'group_name', 'is_deleted')
#     filter_horizontal = ("user", "app")
#     fieldsets = (
#         ('必填选项', {
#             'fields': ('group_name', 'is_deleted')
#         }),
#         ('用户', { 'fields': ('user',)}),
#         ('业务', {'fields': ('app',)}),
#
#     )
#
#
# class AppsPortsInline(admin.TabularInline):
#     model = AppPorts
#     extra = 1
#
#
# class AppsAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'env', 'develop_user', 'deploy_user', 'deploy_path', 'deploy_mode', 'comment')
#     search_fields = ['name', 'env', 'deploy_mode', 'deploy_path']
#     list_filter = ('env',)
#
#     inlines = [
#         AppsPortsInline,
#     ]
#     filter_horizontal = ('assets',)
#
# admin_site.register(Apps, AppsAdmin)
#
#
# class LinksAdmin(admin.ModelAdmin):
#     pass
#
# admin_site.register(Links, LinksAdmin)
#
# admin_site.register(MyGroup, GroupAdmin)
# Success._meta.verbose_name = "成功的任务"
# Success._meta.verbose_name_plural = "成功的任务列表"
# admin_site.register(Success, TaskAdmin)
# Failure._meta.verbose_name = "失败的任务"
# Failure._meta.verbose_name_plural = "失败的任务列表"
# admin_site.register(Failure, FailAdmin)
# Schedule._meta.verbose_name_plural = "调度任务列表"
# admin_site.register(Schedule, ScheduleAdmin)
# admin_site.register(ResourceGroup, ResourceGroupAdmin)