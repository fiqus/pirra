# Generated by Django 2.2.6 on 2019-11-05 15:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('empresa', '0003_auto_20191101_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='producto',
            name='fecha_baja',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='producto',
            name='usuario_baja',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
