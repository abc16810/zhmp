# Generated by Django 4.2 on 2023-06-26 02:28

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apps', '0004_alter_apps_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcegroup',
            name='member',
            field=models.ManyToManyField(blank=True, related_name='apps_resourcegroup', to=settings.AUTH_USER_MODEL, verbose_name='成员'),
        ),
    ]
