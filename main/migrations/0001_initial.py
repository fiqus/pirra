# Generated by Django 2.2.4 on 2019-08-14 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AgenteEDI',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nro_doc', models.CharField(max_length=128)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
        ),
    ]
