# Generated by Django 4.2 on 2023-04-19 00:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("rms", "0001_initial"),
        ("pms", "0003_alter_roomtype_number_of_beds"),
    ]

    operations = [
        migrations.AddField(
            model_name="hotel",
            name="hotel_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="hotels",
                to="rms.hotelgroup",
            ),
        ),
    ]
