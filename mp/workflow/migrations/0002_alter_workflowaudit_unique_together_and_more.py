# Generated by Django 4.2 on 2023-06-25 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='workflowaudit',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='workflowaudit',
            name='apps_group_id',
            field=models.IntegerField(default=1, verbose_name='业务组ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workflowaudit',
            name='apps_group_name',
            field=models.CharField(default=1, max_length=100, verbose_name='业务组名称'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='workflowaudit',
            unique_together={('apps_group_id', 'workflow_type')},
        ),
        migrations.RemoveField(
            model_name='workflowaudit',
            name='group_id',
        ),
        migrations.RemoveField(
            model_name='workflowaudit',
            name='group_name',
        ),
    ]
