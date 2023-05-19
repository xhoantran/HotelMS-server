# Generated by Django 4.2.1 on 2023-05-19 17:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("pms", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CMHotelConnector",
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
                    "channel_manager",
                    models.CharField(
                        choices=[("Channex", "Channex")],
                        default="Channex",
                        max_length=16,
                    ),
                ),
                ("cm_name", models.CharField(blank=True, max_length=255, null=True)),
                ("cm_id", models.UUIDField()),
                ("cm_api_key", models.CharField(max_length=255)),
                (
                    "pms",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel_manager_connector",
                        to="pms.hotel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CMRoomTypeConnector",
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
                ("cm_name", models.CharField(max_length=255)),
                ("cm_id", models.UUIDField(blank=True, null=True)),
                (
                    "cm_hotel_connector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="room_type_connectors",
                        to="cm.cmhotelconnector",
                    ),
                ),
                (
                    "pms",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel_manager_connector",
                        to="pms.roomtype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CMRatePlanConnector",
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
                ("cm_name", models.CharField(max_length=255)),
                ("cm_id", models.UUIDField(blank=True, null=True)),
                (
                    "cm_room_type_connector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rate_plan_connectors",
                        to="cm.cmroomtypeconnector",
                    ),
                ),
                (
                    "pms",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel_manager_connector",
                        to="pms.rateplan",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CMHotelConnectorAPIKey",
            fields=[
                (
                    "id",
                    models.CharField(
                        editable=False,
                        max_length=150,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("prefix", models.CharField(editable=False, max_length=8, unique=True)),
                ("hashed_key", models.CharField(editable=False, max_length=150)),
                ("created", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "name",
                    models.CharField(
                        default=None,
                        help_text="A free-form name for the API key. Need not be unique. 50 characters max.",
                        max_length=50,
                    ),
                ),
                (
                    "revoked",
                    models.BooleanField(
                        blank=True,
                        default=False,
                        help_text="If the API key is revoked, clients cannot use it anymore. (This cannot be undone.)",
                    ),
                ),
                (
                    "expiry_date",
                    models.DateTimeField(
                        blank=True,
                        help_text="Once API key expires, clients cannot use it anymore.",
                        null=True,
                        verbose_name="Expires",
                    ),
                ),
                (
                    "cm_hotel_connector",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_key",
                        to="cm.cmhotelconnector",
                    ),
                ),
            ],
            options={
                "verbose_name": "API key",
                "verbose_name_plural": "API keys",
                "ordering": ("-created",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CMBookingConnector",
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
                ("cm_id", models.UUIDField(blank=True, null=True)),
                (
                    "cm_hotel_connector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="booking_connectors",
                        to="cm.cmhotelconnector",
                    ),
                ),
                (
                    "pms",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel_manager_connector",
                        to="pms.booking",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="cmroomtypeconnector",
            constraint=models.UniqueConstraint(
                fields=("cm_hotel_connector", "cm_id"),
                name="unique_room_type_cm_id_per_hotel_connector",
                violation_error_message="Room type with this external ID already associated with this property",
            ),
        ),
        migrations.AddConstraint(
            model_name="cmrateplanconnector",
            constraint=models.UniqueConstraint(
                fields=("cm_room_type_connector", "cm_id"),
                name="unique_rate_plan_cm_id_per_room_type_connector",
                violation_error_message="Rate plan with this external ID already associated with this room type",
            ),
        ),
        migrations.AddConstraint(
            model_name="cmhotelconnector",
            constraint=models.UniqueConstraint(
                fields=("channel_manager", "cm_id"),
                name="unique_cm_id_per_channel_manager",
                violation_error_message="Property with this external ID already exists",
            ),
        ),
        migrations.AddConstraint(
            model_name="cmbookingconnector",
            constraint=models.UniqueConstraint(
                fields=("cm_hotel_connector", "cm_id"),
                name="unique_booking_cm_id_per_hotel_connector",
                violation_error_message="Booking with this external ID already associated with this property",
            ),
        ),
    ]
