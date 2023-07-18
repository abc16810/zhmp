# Generated by Django 4.2 on 2023-06-21 03:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcegroup',
            name='is_deleted',
        ),
        migrations.AddField(
            model_name='apps',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='是否删除'),
        ),
    ]