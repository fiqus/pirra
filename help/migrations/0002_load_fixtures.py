# Generated by Django 2.2.6 on 2019-10-22 19:35
import os

from django.core.management import call_command
from django.db import migrations


def load_fixtures(apps, schema_editor):
    fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
    files = [
        'initial_data.json',
    ]
    for f in files:
        fixture_file = os.path.join(fixtures_dir, f)
        call_command('loaddata', fixture_file, app_label='empresa')


class Migration(migrations.Migration):

    dependencies = [
        ('help', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixtures)
    ]
