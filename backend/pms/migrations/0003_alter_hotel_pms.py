# Generated by Django 4.2 on 2023-04-28 18:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pms", "0002_hotel_address_hotel_city_hotel_country_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hotel",
            name="pms",
            field=models.CharField(
                blank=True,
                choices=[(None, "default"), ("CHANNEX", "Channex")],
                max_length=16,
            ),
        ),
    ]
