# Generated by Django 4.2 on 2023-06-01 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_myuser_nickname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='nickname',
            field=models.CharField(max_length=50, null=True, unique=True, verbose_name='昵称'),
        ),
    ]