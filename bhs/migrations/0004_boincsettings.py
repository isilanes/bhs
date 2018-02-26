# Generated by Django 2.0.1 on 2018-02-01 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bhs', '0003_boincproject_icon'),
    ]

    operations = [
        migrations.CreateModel(
            name='BOINCSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='none', max_length=50, verbose_name='Name')),
                ('bwlimit', models.IntegerField(default=100, verbose_name='Bandwidth limit')),
            ],
        ),
    ]