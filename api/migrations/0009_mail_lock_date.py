# Generated by Django 3.0.5 on 2022-08-31 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20220126_0040'),
    ]

    operations = [
        migrations.AddField(
            model_name='mail',
            name='lock_date',
            field=models.DateTimeField(null=True),
        ),
    ]
