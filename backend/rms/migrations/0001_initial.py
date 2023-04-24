# Generated by Django 4.2 on 2023-04-24 19:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("pms", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DynamicPricingSetting",
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
                ("is_enabled", models.BooleanField(default=True)),
                ("is_lead_days_based", models.BooleanField(default=False)),
                ("lead_day_window", models.SmallIntegerField(default=60)),
                ("is_weekday_based", models.BooleanField(default=False)),
                ("is_month_based", models.BooleanField(default=False)),
                ("is_season_based", models.BooleanField(default=False)),
                ("is_occupancy_based", models.BooleanField(default=False)),
                ("is_time_based", models.BooleanField(default=False)),
                (
                    "hotel",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dynamic_pricing_setting",
                        to="pms.hotel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WeekdayBasedRule",
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
                (
                    "multiplier_factor",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                ("increment_factor", models.IntegerField(default=0)),
                (
                    "weekday",
                    models.SmallIntegerField(
                        choices=[
                            (1, "Monday"),
                            (2, "Tuesday"),
                            (3, "Wednesday"),
                            (4, "Thursday"),
                            (5, "Friday"),
                            (6, "Saturday"),
                            (7, "Sunday"),
                        ]
                    ),
                ),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weekday_based_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TimeBasedTriggerRule",
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
                (
                    "multiplier_factor",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                ("increment_factor", models.IntegerField(default=0)),
                ("trigger_time", models.TimeField()),
                ("min_occupancy", models.SmallIntegerField()),
                ("max_occupancy", models.SmallIntegerField()),
                ("is_today", models.BooleanField()),
                ("is_tomorrow", models.BooleanField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="time_based_trigger_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SeasonBasedRule",
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
                (
                    "multiplier_factor",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                ("increment_factor", models.IntegerField(default=0)),
                ("name", models.CharField(max_length=64)),
                ("start_month", models.SmallIntegerField()),
                ("start_day", models.SmallIntegerField()),
                ("end_month", models.SmallIntegerField()),
                ("end_day", models.SmallIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="season_based_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OccupancyBasedTriggerRule",
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
                (
                    "multiplier_factor",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                ("increment_factor", models.IntegerField(default=0)),
                ("min_occupancy", models.SmallIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="occupancy_based_trigger_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MonthBasedRule",
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
                (
                    "multiplier_factor",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                ("increment_factor", models.IntegerField(default=0)),
                (
                    "month",
                    models.SmallIntegerField(
                        choices=[
                            (1, "January"),
                            (2, "February"),
                            (3, "March"),
                            (4, "April"),
                            (5, "May"),
                            (6, "June"),
                            (7, "July"),
                            (8, "August"),
                            (9, "September"),
                            (10, "October"),
                            (11, "November"),
                            (12, "December"),
                        ]
                    ),
                ),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="month_based_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LeadDaysBasedRule",
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
                (
                    "multiplier_factor",
                    models.DecimalField(decimal_places=2, default=1, max_digits=3),
                ),
                ("increment_factor", models.IntegerField(default=0)),
                ("lead_days", models.SmallIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lead_days_based_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="weekdaybasedrule",
            index=models.Index(
                fields=["setting", "weekday"], name="rms_weekday_setting_ff9845_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="weekdaybasedrule",
            unique_together={("setting", "weekday")},
        ),
        migrations.AddIndex(
            model_name="seasonbasedrule",
            index=models.Index(
                fields=["setting", "name"], name="rms_seasonb_setting_f90047_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="seasonbasedrule",
            unique_together={("setting", "name")},
        ),
        migrations.AddIndex(
            model_name="occupancybasedtriggerrule",
            index=models.Index(
                fields=["setting", "min_occupancy"],
                name="rms_occupan_setting_c6d25e_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="occupancybasedtriggerrule",
            unique_together={("setting", "min_occupancy")},
        ),
        migrations.AddIndex(
            model_name="monthbasedrule",
            index=models.Index(
                fields=["setting", "month"], name="rms_monthba_setting_2b1936_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="monthbasedrule",
            unique_together={("setting", "month")},
        ),
        migrations.AddIndex(
            model_name="leaddaysbasedrule",
            index=models.Index(
                fields=["setting", "lead_days"], name="rms_leadday_setting_b09fb4_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="leaddaysbasedrule",
            unique_together={("setting", "lead_days")},
        ),
    ]
