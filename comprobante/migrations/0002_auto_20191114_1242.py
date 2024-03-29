# Generated by Django 2.2.6 on 2019-11-14 15:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comprobante', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordencompra',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='ordencompra',
            name='fecha_baja',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ordencompra',
            name='usuario_baja',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
