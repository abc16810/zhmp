from django.db import models
from mp.common.utils import localtime
from mp.common.models import TimestampsWithAuto


class Links(TimestampsWithAuto):
    links_type_choices = (
        (1, '运维导航'),
        (2, '办公导航'),
        (3, '常用导航'),
        (4, '其它导航'),
    )

    nav_type = models.SmallIntegerField("类型", choices=links_type_choices, default=1)
    nav_name = models.CharField("连接名称", max_length=100)
    nav_desc = models.CharField("描述信息", max_length=200)
    nav_url = models.URLField("连接地址", max_length=255)
    width = models.CharField("宽度", max_length=50, blank=True, null=True)
    height = models.CharField('高度', max_length=50, blank=True, null=True)
    nav_img = models.FileField(upload_to='./nav/', verbose_name='图片路径', blank=True, null=True)
    icon = models.CharField("图标", max_length=50, default="fa-tags")

    class Meta:
        db_table = 'mp_links'
        default_permissions = ()
        permissions = (
            ("read_links", "读取站内导航"),
            ("change_links", "修改站内导航"),
            ("add_links", "添加站内导航"),
            ("delete_links", "删除站内导航"),
        )
        unique_together = ("nav_type", "nav_name")
        verbose_name = '站内导航管理'
        verbose_name_plural = '站内导航详情表'

    def __str__(self):
        return '%s-%s' % (self.nav_type, self.nav_name)
