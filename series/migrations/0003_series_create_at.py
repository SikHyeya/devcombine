# Generated by Django 4.2 on 2023-05-06 12:32

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("series", "0002_series_is_main_alter_series_subtitle"),
    ]

    operations = [
        migrations.AddField(
            model_name="series",
            name="create_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]