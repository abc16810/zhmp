# Generated by Django 4.2 on 2023-06-20 08:07

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_sshuser_become_sshuser_become_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sshuser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='创建时间'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sshuser',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='cabinet',
            name='cabinet_band',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='机柜带宽 MB'),
        ),
        migrations.AlterField(
            model_name='ram',
            name='size',
            field=models.IntegerField(verbose_name='内存大小（MB）'),
        ),
    ]
