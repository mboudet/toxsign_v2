# Generated by Django 2.0.13 on 2019-10-09 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signatures', '0005_auto_20191008_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='signature',
            name='expression_values_file',
            field=models.FileField(blank=True, upload_to='files/'),
        ),
    ]
