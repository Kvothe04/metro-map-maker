# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2018-12-16 19:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0005_savedmap_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedmap',
            name='thumbnail',
            field=models.TextField(blank=True, default=''),
        ),
    ]