import json

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .models import (
    DynamicPricingSetting,
    Hotel,
    LeadDaysBasedRule,
    MonthBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


@receiver(
    post_save,
    sender=Hotel,
    dispatch_uid="rms:post_save_hotel",
)
def post_save_hotel(sender, instance: Hotel, created, **kwargs):
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


@receiver(
    post_save,
    sender=TimeBasedTriggerRule,
    dispatch_uid="rms:post_save_time_based_trigger_rule",
)
def post_save_time_based_trigger_rule(
    sender, instance: TimeBasedTriggerRule, created, **kwargs
):
    if created:
        periodic_task = PeriodicTask(
            name=instance.id,
            task="rms.tasks.handle_time_based_trigger_rule",
            start_time=timezone.now(),
        )
    else:
        periodic_task = instance.periodic_task

    if isinstance(instance.trigger_time, str):
        instance.trigger_time = timezone.datetime.strptime(
            instance.trigger_time, "%H:%M:%S"
        ).time()

    # When the trigger time is changed, update
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=instance.trigger_time.minute,
        hour=instance.trigger_time.hour,
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    periodic_task.crontab = crontab
    periodic_task.kwargs = json.dumps(
        {
            "hotel_id": instance.setting.hotel.id,
            "day_ahead": instance.day_ahead,
        }
    )
    periodic_task.enabled = instance.is_active
    periodic_task.save()
