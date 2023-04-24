from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.pms.models import HotelGroup

# from django_celery_beat.models import PeriodicTask


class FactorChoices:
    MULTIPLIER = 0
    INCREMENT = 1


class DynamicPricingSetting(models.Model):
    hotel_group = models.OneToOneField(
        HotelGroup,
        on_delete=models.CASCADE,
        related_name="dynamic_pricing_setting",
    )
    is_enabled = models.BooleanField(default=True)
    is_lead_days_based = models.BooleanField(default=False)
    lead_day_window = models.SmallIntegerField(default=60)
    is_weekday_based = models.BooleanField(default=False)
    is_month_based = models.BooleanField(default=False)
    is_season_based = models.BooleanField(default=False)
    is_occupancy_based = models.BooleanField(default=False)
    is_time_based = models.BooleanField(default=False)


class RuleFactor(models.Model):
    multiplier_factor = models.DecimalField(max_digits=3, decimal_places=2, default=1)
    increment_factor = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.multiplier_factor < 0:
            raise ValueError("Multiplier factor must be positive")
        if self.increment_factor < 0:
            raise ValueError("Increment factor must be positive")
        if self.multiplier_factor != 1 and self.increment_factor != 0:
            raise ValueError("Multiplier and increment cannot be used together")
        super().save(*args, **kwargs)


class LeadDaysBasedRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="lead_days_based_rules",
    )
    lead_days = models.SmallIntegerField()

    class Meta:
        unique_together = ("setting", "lead_days")
        indexes = [
            models.Index(fields=["setting", "lead_days"]),
        ]


class WeekdayBasedRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="weekday_based_rules",
    )

    class WeekdayChoices(models.IntegerChoices):
        MONDAY = 1, _("Monday")
        TUESDAY = 2, _("Tuesday")
        WEDNESDAY = 3, _("Wednesday")
        THURSDAY = 4, _("Thursday")
        FRIDAY = 5, _("Friday")
        SATURDAY = 6, _("Saturday")
        SUNDAY = 7, _("Sunday")

    weekday = models.SmallIntegerField(choices=WeekdayChoices.choices)

    class Meta:
        unique_together = ("setting", "weekday")
        indexes = [
            models.Index(fields=["setting", "weekday"]),
        ]

    def save(self, *args, **kwargs):
        if self.weekday not in self.WeekdayChoices.values:
            raise ValueError("Invalid weekday")
        super().save(*args, **kwargs)


class MonthBasedRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="month_based_rules",
    )

    class MonthChoices(models.IntegerChoices):
        JANUARY = 1, _("January")
        FEBRUARY = 2, _("February")
        MARCH = 3, _("March")
        APRIL = 4, _("April")
        MAY = 5, _("May")
        JUNE = 6, _("June")
        JULY = 7, _("July")
        AUGUST = 8, _("August")
        SEPTEMBER = 9, _("September")
        OCTOBER = 10, _("October")
        NOVEMBER = 11, _("November")
        DECEMBER = 12, _("December")

    month = models.SmallIntegerField(choices=MonthChoices.choices)

    class Meta:
        unique_together = ("setting", "month")
        indexes = [
            models.Index(fields=["setting", "month"]),
        ]

    def save(self, *args, **kwargs):
        if self.month not in self.MonthChoices.values:
            raise ValueError("Invalid month")
        super().save(*args, **kwargs)


class SeasonBasedRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="season_based_rules",
    )
    name = models.CharField(max_length=64)
    start_month = models.SmallIntegerField()
    start_day = models.SmallIntegerField()
    end_month = models.SmallIntegerField()
    end_day = models.SmallIntegerField()

    class Meta:
        unique_together = ("setting", "name")
        indexes = [
            models.Index(fields=["setting", "name"]),
        ]

    def save(self, *args, **kwargs):
        try:
            datetime.strptime(f"{self.start_month}/{self.start_day}", "%m/%d")
            datetime.strptime(f"{self.end_month}/{self.end_day}", "%m/%d")
        except ValueError:
            raise ValueError("Invalid start or end date")
        super().save(*args, **kwargs)


class OccupancyBasedTriggerRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="occupancy_based_trigger_rules",
    )
    min_occupancy = models.SmallIntegerField()

    class Meta:
        unique_together = ("setting", "min_occupancy")
        indexes = [
            models.Index(fields=["setting", "min_occupancy"]),
        ]


class TimeBasedTriggerRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="time_based_trigger_rules",
    )
    trigger_time = models.TimeField()
    min_occupancy = models.SmallIntegerField()
    max_occupancy = models.SmallIntegerField()
    is_today = models.BooleanField()
    is_tomorrow = models.BooleanField()
    is_active = models.BooleanField(default=True)

    # periodic_task = models.OneToOneField(
    #     PeriodicTask,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    # )

    def save(self, *args, **kwargs):
        if self.min_occupancy > self.max_occupancy:
            raise ValueError("Min occupancy cannot be greater than max occupancy")

        # either today or tomorrow must be true
        if not bool(self.is_today ^ self.is_tomorrow):
            raise ValueError("Cannot be both today and tommorow")
        super().save(*args, **kwargs)
