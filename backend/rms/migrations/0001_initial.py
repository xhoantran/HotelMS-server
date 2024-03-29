# Generated by Django 4.2.1 on 2023-05-31 16:52

import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.contrib.postgres.operations
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("django_celery_beat", "0018_improve_crontab_helptext"),
        ("pms", "0001_initial"),
    ]

    operations = [
        django.contrib.postgres.operations.BtreeGistExtension(),
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
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("is_enabled", models.BooleanField(default=False)),
                ("is_lead_days_based", models.BooleanField(default=False)),
                ("lead_day_window", models.PositiveSmallIntegerField(default=60)),
                ("is_weekday_based", models.BooleanField(default=False)),
                ("is_month_based", models.BooleanField(default=False)),
                ("is_season_based", models.BooleanField(default=False)),
                ("is_occupancy_based", models.BooleanField(default=False)),
                ("is_time_based", models.BooleanField(default=False)),
                ("default_base_rate", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
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
            name="RMSRatePlanRestrictions",
            fields=[
                (
                    "restriction",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="rms",
                        serialize=False,
                        to="pms.rateplanrestrictions",
                    ),
                ),
                ("base_rate", models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="RMSRatePlan",
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
                ("percentage_factor", models.SmallIntegerField()),
                ("increment_factor", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "rate_plan",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rms",
                        to="pms.rateplan",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IntervalBaseRate",
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("dates", django.contrib.postgres.fields.ranges.DateRangeField()),
                ("base_rate", models.PositiveIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interval_base_rates",
                        to="rms.dynamicpricingsetting",
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("percentage_factor", models.SmallIntegerField(default=0)),
                ("increment_factor", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "weekday",
                    models.PositiveSmallIntegerField(
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
            options={
                "indexes": [
                    models.Index(
                        fields=["setting", "weekday"],
                        name="rms_weekday_setting_ff9845_idx",
                    )
                ],
                "unique_together": {("setting", "weekday")},
            },
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("percentage_factor", models.SmallIntegerField(default=0)),
                ("increment_factor", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("hour", models.PositiveSmallIntegerField()),
                ("min_occupancy", models.PositiveSmallIntegerField()),
                (
                    "day_ahead",
                    models.PositiveSmallIntegerField(
                        choices=[(0, "Today"), (1, "Tomorrow")], default=0
                    ),
                ),
                (
                    "periodic_task",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="time_based_trigger_rules",
                        to="django_celery_beat.periodictask",
                    ),
                ),
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
                "unique_together": {("setting", "hour", "day_ahead", "min_occupancy")},
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("percentage_factor", models.SmallIntegerField(default=0)),
                ("increment_factor", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=64)),
                ("start_month", models.PositiveSmallIntegerField()),
                ("start_day", models.PositiveSmallIntegerField()),
                ("end_month", models.PositiveSmallIntegerField()),
                ("end_day", models.PositiveSmallIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="season_based_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["setting", "name"],
                        name="rms_seasonb_setting_f90047_idx",
                    )
                ],
                "unique_together": {("setting", "name")},
            },
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("percentage_factor", models.SmallIntegerField(default=0)),
                ("increment_factor", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("min_occupancy", models.PositiveSmallIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="occupancy_based_trigger_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["setting", "min_occupancy"],
                        name="rms_occupan_setting_c6d25e_idx",
                    )
                ],
                "unique_together": {("setting", "min_occupancy")},
            },
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("percentage_factor", models.SmallIntegerField(default=0)),
                ("increment_factor", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "month",
                    models.PositiveSmallIntegerField(
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
            options={
                "indexes": [
                    models.Index(
                        fields=["setting", "month"],
                        name="rms_monthba_setting_2b1936_idx",
                    )
                ],
                "unique_together": {("setting", "month")},
            },
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("percentage_factor", models.SmallIntegerField(default=0)),
                ("increment_factor", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("lead_days", models.PositiveSmallIntegerField()),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lead_days_based_rules",
                        to="rms.dynamicpricingsetting",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["setting", "lead_days"],
                        name="rms_leadday_setting_b09fb4_idx",
                    )
                ],
                "unique_together": {("setting", "lead_days")},
            },
        ),
        migrations.AddConstraint(
            model_name="intervalbaserate",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[("dates", "&&"), ("setting", "=")],
                name="exclude_overlapping_interval_base_rates",
            ),
        ),
    ]
