# Generated by Django 4.2.1 on 2023-05-18 16:52

from django.conf import settings
import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.contrib.postgres.operations
from django.db import migrations, models
import django.db.models.deletion
import timezone_field.fields
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        django.contrib.postgres.operations.BtreeGistExtension(),
        migrations.CreateModel(
            name="Hotel",
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
                ("name", models.CharField(max_length=255)),
                ("inventory_days", models.SmallIntegerField(default=100)),
                ("address", models.CharField(blank=True, max_length=255, null=True)),
                ("city", models.CharField(blank=True, max_length=128, null=True)),
                ("country", models.CharField(blank=True, max_length=2, null=True)),
                ("currency", models.CharField(blank=True, max_length=3, null=True)),
                (
                    "timezone",
                    timezone_field.fields.TimeZoneField(default="UTC", use_pytz=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="RoomType",
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
                ("name", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "hotel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="room_types",
                        to="pms.hotel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Room",
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
                ("number", models.IntegerField()),
                (
                    "room_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rooms",
                        to="pms.roomtype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RatePlan",
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
                ("name", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "room_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rate_plans",
                        to="pms.roomtype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Booking",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("cancelled", "Cancelled"),
                            ("modified", "Modified"),
                        ],
                        default="new",
                        max_length=16,
                    ),
                ),
                ("raw_data", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "hotel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bookings",
                        to="pms.hotel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RatePlanRestrictions",
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
                ("date", models.DateField()),
                ("rate", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "rate_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="restrictions",
                        to="pms.rateplan",
                    ),
                ),
            ],
            options={
                "unique_together": {("rate_plan", "date")},
            },
        ),
        migrations.CreateModel(
            name="HotelEmployee",
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
                (
                    "hotel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="pms.hotel",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hotel_employee",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "hotel")},
            },
        ),
        migrations.CreateModel(
            name="BookingRoom",
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
                ("dates", django.contrib.postgres.fields.ranges.DateRangeField()),
                ("raw_data", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "booking",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="booking_rooms",
                        to="pms.booking",
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="booking_rooms",
                        to="pms.room",
                    ),
                ),
                (
                    "room_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="booking_rooms",
                        to="pms.roomtype",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["dates", "room_type"],
                        name="pms_booking_dates_e613c1_idx",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="bookingroom",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[("dates", "&&"), ("room", "=")],
                name="exclude_overlapping_dates_for_room",
            ),
        ),
    ]
