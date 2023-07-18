from django.db import models
from django.contrib.auth import get_user_model
from mp.assets.models import ServerAssets
from mp.common.models import TimestampsWithAuto
from mptt.models import MPTTModel, TreeForeignKey


class Apps(MPTTModel, TimestampsWithAuto):
    ENV_CHOICES = (
        ('pro', '生产环境'),
        ('dev', '测试环境')
    )
    DEPLOY_MODE_CHOICES = (
        ("docker", "docker"),
        ("docker-compose", "docker compose"),
        ("k8s", "k8s"),
        ("local", "直接部署"),
        ("other", "其它方式")
    )
    name = models.CharField("应用名称", max_length=255, unique=True)
    env = models.CharField("环境", choices=ENV_CHOICES, max_length=10, default='pro')
    develop_user = models.CharField("开发负责人", max_length=20, blank=True)
    deploy_user = models.CharField("运维负责人", max_length=20, blank=True)
    deploy_path = models.CharField("部署路径", max_length=255)
    deploy_mode = models.CharField("部署方式", choices=DEPLOY_MODE_CHOICES, max_length=20, default='docker-compose')
    assets = models.ManyToManyField(ServerAssets, verbose_name="服务器", blank=True)
    up_date = models.DateField("上线时间", null=True, blank=True)
    down_date = models.DateField("到期时间", null=True, blank=True)
    comment = models.TextField("备注", blank=True, null=True)
    group = models.ForeignKey('ResourceGroup', verbose_name="所属部门", on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='apps')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, verbose_name='上级应用', null=True, blank=True, db_index=True,
                            related_name='children')
    is_deleted = models.BooleanField('是否删除', default=False)

    class Meta:
        db_table = 'mp_apps'
        default_permissions = ()
        permissions = (
            ("add_apps", "添加应用"),  # 添加业务资产权限
            ("change_apps", "修改应用"),
            ("delete_apps", "删除应用"),
            ("view_apps", "查看应用"),
        )
        verbose_name = '应用管理'
        verbose_name_plural = '业务管理'

    def __str__(self):
        return self.name


class AppPorts(TimestampsWithAuto):
    app = models.ForeignKey(Apps, on_delete=models.CASCADE, default=None)
    start_port = models.PositiveIntegerField("启动端口")
    map_port = models.PositiveIntegerField("映射端口")
    comment = models.TextField("备注", blank=True, null=True)

    class Meta:
        db_table = 'mp_apps_port'
        default_permissions = ()
        permissions = (
            ("add_app_ports", "添加映射端口"),
            ("change_app_ports", "修改映射端口"),
            ("delete_app_ports", "删除映射端口"),
            ("view_app_ports", "查看映射端口"),
        )
        verbose_name = '应用端口'
        verbose_name_plural = '应用端口'

    def __str__(self):
        return "%s -> %s" % (self.start_port, self.map_port)


class ResourceGroup(MPTTModel, TimestampsWithAuto):
    """
    业务组/部门
    """
    name = models.CharField('组名称', max_length=100, unique=True)
    desc = models.CharField(max_length=150, blank=True, null=True, verbose_name="描述")
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, verbose_name='上级', null=True, blank=True,
                            db_index=True, related_name='children')
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True,
                             verbose_name='负责人')
    member = models.ManyToManyField(get_user_model(), blank=True, related_name="apps_resourcegroup",
                                    verbose_name="成员")

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 'mp_apps_group'
        verbose_name = '业务组管理'
        verbose_name_plural = verbose_name
        default_permissions = ()
        permissions = (
            ("add_resource_group", "添加业务组"),
            ("change_resource_group", "修改业务组"),
            ("delete_resource_group", "删除业务组"),
            ("view_resource_group", "查看业务组"),
        )

    def node_paths(self):
        paths = ''
        if self.is_root_node():
            paths = '%s' % self.name
        else:
            "查找父节点"
            q = ResourceGroup.objects.raw(
                """select id,name as path from mp_apps_group where tree_id={tree_id} and lft < {lft} AND rght > {rght} 
                ORDER BY lft ASC""".format(tree_id=self.tree_id, lft=self.lft, rght=self.rght))
            for obj in q:
                paths += obj.path + '/'
            paths = paths + self.name
        return paths

    def root_node(self):
        return self.is_root_node()


