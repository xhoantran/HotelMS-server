# Generated by Django 4.2 on 2023-04-20 02:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rms", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="availabilitybasedtriggerrule",
            name="multiplier_factor",
        ),
        migrations.AddField(
            model_name="availabilitybasedtriggerrule",
            name="increment_factor",
            field=models.IntegerField(default=100),
            preserve_default=False,
        ),
    ]
