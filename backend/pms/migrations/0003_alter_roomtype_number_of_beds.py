# Generated by Django 4.2 on 2023-04-18 15:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pms", "0002_alter_roomtype_base_rate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="roomtype",
            name="number_of_beds",
            field=models.SmallIntegerField(default=0),
        ),
    ]