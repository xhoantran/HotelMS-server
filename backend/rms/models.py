from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import PeriodicTask

from backend.pms.models import Hotel


class RuleNotEnabledError(Exception):
    pass


class FactorChoices:
    PERCENTAGE = 0
    INCREMENT = 1


class DynamicPricingSetting(models.Model):
    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="dynamic_pricing_setting",
    )
    is_enabled = models.BooleanField(default=True)
    is_lead_days_based = models.BooleanField(default=False)
    lead_day_window = models.PositiveSmallIntegerField(default=60)
    is_weekday_based = models.BooleanField(default=False)
    is_month_based = models.BooleanField(default=False)
    is_season_based = models.BooleanField(default=False)
    is_occupancy_based = models.BooleanField(default=False)
    is_time_based = models.BooleanField(default=False)


class RuleFactor(models.Model):
    percentage_factor = models.SmallIntegerField(default=0)
    increment_factor = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.percentage_factor < -100:
            raise ValueError("Percentage factor cannot be less than -100")

        if not (bool(self.percentage_factor) ^ bool(self.increment_factor)):
            raise ValueError("Either percentage factor or increment factor must be set")
        super().save(*args, **kwargs)


class LeadDaysBasedRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="lead_days_based_rules",
    )
    lead_days = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("setting", "lead_days")
        indexes = [
            models.Index(fields=["setting", "lead_days"]),
        ]

    def save(self, *args, **kwargs):
        if not self.setting.is_lead_days_based:
            raise RuleNotEnabledError("Lead days based rules are not enabled")
        super().save(*args, **kwargs)


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

    weekday = models.PositiveSmallIntegerField(choices=WeekdayChoices.choices)

    class Meta:
        unique_together = ("setting", "weekday")
        indexes = [
            models.Index(fields=["setting", "weekday"]),
        ]

    def save(self, *args, **kwargs):
        if self.weekday not in self.WeekdayChoices.values:
            raise ValueError("Invalid weekday")
        if not self.setting.is_weekday_based:
            raise RuleNotEnabledError("Weekday based rules are not enabled")
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

    month = models.PositiveSmallIntegerField(choices=MonthChoices.choices)

    class Meta:
        unique_together = ("setting", "month")
        indexes = [
            models.Index(fields=["setting", "month"]),
        ]

    def save(self, *args, **kwargs):
        if self.month not in self.MonthChoices.values:
            raise ValueError("Invalid month")
        if not self.setting.is_month_based:
            raise RuleNotEnabledError("Month based rules are not enabled")
        super().save(*args, **kwargs)


class SeasonBasedRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="season_based_rules",
    )
    name = models.CharField(max_length=64)
    start_month = models.PositiveSmallIntegerField()
    start_day = models.PositiveSmallIntegerField()
    end_month = models.PositiveSmallIntegerField()
    end_day = models.PositiveSmallIntegerField()

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
        if not self.setting.is_season_based:
            raise RuleNotEnabledError("Season based rules are not enabled")
        super().save(*args, **kwargs)


class OccupancyBasedTriggerRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="occupancy_based_trigger_rules",
    )
    min_occupancy = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("setting", "min_occupancy")
        indexes = [
            models.Index(fields=["setting", "min_occupancy"]),
        ]

    def save(self, *args, **kwargs):
        if not self.setting.is_occupancy_based:
            raise RuleNotEnabledError("Occupancy based rules are not enabled")
        super().save(*args, **kwargs)


class TimeBasedTriggerRule(RuleFactor):
    setting = models.ForeignKey(
        DynamicPricingSetting,
        on_delete=models.CASCADE,
        related_name="time_based_trigger_rules",
    )
    trigger_time = models.TimeField()
    min_occupancy = models.PositiveSmallIntegerField()
    max_occupancy = models.PositiveSmallIntegerField()

    class DayAheadChoices(models.IntegerChoices):
        TODAY = 0, _("Today")
        TOMORROW = 1, _("Tomorrow")

    MAX_DAY_AHEAD = DayAheadChoices.TOMORROW

    day_ahead = models.PositiveSmallIntegerField(
        choices=DayAheadChoices.choices,
        default=0,
    )

    periodic_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.SET_NULL,
        related_name="time_based_trigger_rule",
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.min_occupancy > self.max_occupancy:
            raise ValueError("Min occupancy cannot be greater than max occupancy")
        if self.day_ahead not in self.DayAheadChoices.values:
            raise ValueError("Invalid day ahead")
        if not self.setting.is_time_based:
            raise RuleNotEnabledError("Time based rules are not enabled")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.periodic_task:
            self.periodic_task.delete()
        return super().delete(*args, **kwargs)
