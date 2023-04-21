# Generated by Django 4.2 on 2023-04-19 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("pms", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rateplanrestrictions",
            name="availability",
        ),
        migrations.AddField(
            model_name="rateplanrestrictions",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name="RoomTypeAvailability",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                ("availability", models.SmallIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "room_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="availability",
                        to="pms.roomtype",
                    ),
                ),
            ],
            options={
                "unique_together": {("room_type", "date")},
            },
        ),
    ]
