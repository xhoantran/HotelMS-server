# Generated by Django 4.2 on 2023-04-24 16:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rms", "0003_occupancybasedtriggerrule_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="dynamicpricingsetting",
            old_name="is_availability_based",
            new_name="is_occupancy_based",
        ),
        migrations.AlterField(
            model_name="occupancybasedtriggerrule",
            name="increment_factor",
            field=models.SmallIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name="occupancybasedtriggerrule",
            name="multiplier_factor",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=1, max_digits=3, null=True
            ),
        ),
    ]
