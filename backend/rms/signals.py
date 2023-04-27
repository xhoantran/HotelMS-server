import json

from django.db.models import CharField, F, Value
from django.db.models.functions import Concat
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .adapter import DynamicPricingAdapter
from .models import (
    DynamicPricingSetting,
    Hotel,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


@receiver(post_save, sender=Hotel, dispatch_uid="rms:post_save_hotel")
def post_save_hotel(sender, instance: Hotel, created, **kwargs):
    # By using bulk_create, we can avoid calling save() method for each instance
    # which will trigger validation and save() method of each instance.
    if created:
        setting = DynamicPricingSetting.objects.create(hotel=instance)
        lead_days_based_rules = []
        for i in range(setting.lead_day_window + 1):
            lead_days_based_rules.append(
                LeadDaysBasedRule(setting=setting, lead_days=i + 1)
            )
        LeadDaysBasedRule.objects.bulk_create(lead_days_based_rules)

        weekday_based_rules = []
        for i in range(7):
            weekday_based_rules.append(WeekdayBasedRule(setting=setting, weekday=i + 1))
        WeekdayBasedRule.objects.bulk_create(weekday_based_rules)

        month_based_rules = []
        for i in range(12):
            month_based_rules.append(MonthBasedRule(setting=setting, month=i + 1))
        MonthBasedRule.objects.bulk_create(month_based_rules)


@receiver(post_save, sender=DynamicPricingSetting, dispatch_uid="rms:post_save_dps")
def post_save_dynamic_pricing_setting(sender, instance, created, **kwargs):
    if created:
        return

    periodic_tasks = []
    rules = TimeBasedTriggerRule.objects.filter(setting=instance).select_related(
        "periodic_task"
    )
    for rule in rules:
        rule.periodic_task.enabled = instance.is_time_based
        periodic_tasks.append(rule.periodic_task)
    PeriodicTask.objects.bulk_update(periodic_tasks, ["enabled"])
    DynamicPricingAdapter.invalidate_cache(instance.id)


@receiver(post_save, sender=LeadDaysBasedRule, dispatch_uid="rms:rm_cache")
@receiver(post_save, sender=WeekdayBasedRule, dispatch_uid="rms:rm_cache")
@receiver(post_save, sender=MonthBasedRule, dispatch_uid="rms:rm_cache")
@receiver(post_save, sender=SeasonBasedRule, dispatch_uid="rms:rm_cache")
@receiver(post_save, sender=OccupancyBasedTriggerRule, dispatch_uid="rms:rm_cache")
@receiver(post_save, sender=TimeBasedTriggerRule, dispatch_uid="rms:rm_cache")
def invalidate_dynamic_pricing_cache(sender, instance, created, **kwargs):
    DynamicPricingAdapter.invalidate_cache(instance.setting.id)


@receiver(
    post_save,
    sender=TimeBasedTriggerRule,
    dispatch_uid="rms:post_save_time_based_trigger_rule",
)
def post_save_time_based_trigger_rule(
    sender, instance: TimeBasedTriggerRule, created, **kwargs
):
    if isinstance(instance.trigger_time, str):
        # Convert string to time object
        instance.trigger_time = timezone.datetime.strptime(
            instance.trigger_time, "%H:%M:%S"
        ).time()

    if created:
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=instance.trigger_time.minute,
            hour=instance.trigger_time.hour,
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        instance.periodic_task = PeriodicTask.objects.create(
            name=f"TimeBasedTriggerRule {instance.id} {instance.trigger_time}",
            task="rms.tasks.handle_time_based_trigger_rule",
            start_time=timezone.now(),
            crontab=crontab,
            kwargs=json.dumps(
                {
                    "hotel_id": instance.setting.hotel.id,
                    "day_ahead": instance.day_ahead,
                }
            ),
        )
        instance.save()
        return

    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=instance.trigger_time.minute,
        hour=instance.trigger_time.hour,
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )
    instance.periodic_task.crontab = crontab
    instance.periodic_task.kwargs = json.dumps(
        {
            "hotel_id": instance.setting.hotel.id,
            "day_ahead": instance.day_ahead,
        }
    )
    instance.periodic_task.save()
