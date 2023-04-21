from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

from backend.pms.models import HotelGroup


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
    is_availability_based = models.BooleanField(default=False)
    is_time_based = models.BooleanField(default=False)


class LeadDaysBasedRule(models.Model):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="lead_days_based_rules",
    )
    lead_days = models.SmallIntegerField()
    multiplier_factor = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1,
    )

    class Meta:
        unique_together = ("setting", "lead_days")
        indexes = [
            models.Index(fields=["setting", "lead_days"]),
        ]


class WeekdayBasedRule(models.Model):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="weekday_based_rules",
    )
    multiplier_factor = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1,
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


class MonthBasedRule(models.Model):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="month_based_rules",
    )
    multiplier_factor = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1,
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


class SeasonBasedRule(models.Model):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="season_based_rules",
    )
    multiplier_factor = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1,
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


class AvailabilityBasedTriggerRule(models.Model):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="availability_based_trigger_rules",
    )
    max_availability = models.SmallIntegerField()
    increment_factor = models.IntegerField()

    class Meta:
        unique_together = ("setting", "max_availability")
        indexes = [
            models.Index(fields=["setting", "max_availability"]),
        ]


class TimeBasedTriggerRule(models.Model):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="time_based_trigger_rules",
    )
    trigger_time = models.TimeField()
    multiplier_factor = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1,
    )
    min_availability = models.SmallIntegerField()
    max_availability = models.SmallIntegerField()
    is_today = models.BooleanField()
    is_tomorrow = models.BooleanField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.max_availability < self.min_availability:
            raise ValueError("Max availability must be greater than min availability")

        # either today or tomorrow must be true
        if not bool(self.is_today ^ self.is_tomorrow):
            raise ValueError("Cannot be both today and tommorow")
        super().save(*args, **kwargs)
