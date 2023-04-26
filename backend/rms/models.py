from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import PeriodicTask

from backend.pms.models import Hotel


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
    lead_day_window = models.SmallIntegerField(default=60)
    is_weekday_based = models.BooleanField(default=False)
    is_month_based = models.BooleanField(default=False)
    is_season_based = models.BooleanField(default=False)
    is_occupancy_based = models.BooleanField(default=False)
    is_time_based = models.BooleanField(default=False)
    is_up_to_date = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # It will be set non active and only DynamicPricingAdapter can set it True
        self.is_up_to_date = False
        super().save(*args, **kwargs)


class RuleFactor(models.Model):
    percentage_factor = models.SmallIntegerField(default=0)
    increment_factor = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # It will be set non active and only DynamicPricingAdapter can set it True
        # by calling method activate_rules()
        self.is_active = False

        if self.percentage_factor < -100:
            raise ValueError("Percentage factor cannot be less than -100")
        if self.percentage_factor != 0 and self.increment_factor != 0:
            raise ValueError("Percentage and increment cannot be used together")
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

    class DayAheadChoices(models.IntegerChoices):
        TODAY = 0, _("Today")
        TOMORROW = 1, _("Tomorrow")

    MAX_DAY_AHEAD = DayAheadChoices.TOMORROW

    day_ahead = models.SmallIntegerField(
        choices=DayAheadChoices.choices,
        default=0,
    )

    periodic_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.min_occupancy > self.max_occupancy:
            raise ValueError("Min occupancy cannot be greater than max occupancy")
        if self.day_ahead not in self.DayAheadChoices.values:
            raise ValueError("Invalid day ahead")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.periodic_task:
            self.periodic_task.delete()
        super().delete(*args, **kwargs)
