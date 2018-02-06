# Generated by Django 2.0.1 on 2018-02-06 19:55

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bhs', '0006_boincsettings_ref_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Timestamp')),
                ('nwindows', models.IntegerField(default=0, verbose_name='Windows hosts')),
                ('nlinux', models.IntegerField(default=0, verbose_name='Linux hosts')),
                ('nmacos', models.IntegerField(default=0, verbose_name='MacOS hosts')),
                ('nother', models.IntegerField(default=0, verbose_name='Other hosts')),
                ('cwindows', models.FloatField(default=0.0, verbose_name='Windows credits')),
                ('clinux', models.FloatField(default=0.0, verbose_name='Linux credits')),
                ('cmacos', models.FloatField(default=0.0, verbose_name='MacOS credits')),
                ('cother', models.FloatField(default=0.0, verbose_name='Other credits')),
            ],
        ),
    ]