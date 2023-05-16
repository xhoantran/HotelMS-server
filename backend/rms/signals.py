import json

from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from backend.pms.models import RatePlan

from .adapter import DynamicPricingAdapter
from .models import (
    DynamicPricingSetting,
    Hotel,
    IntervalBaseRate,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    RatePlanPercentageFactor,
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

    # TODO: Update celery task schedule if time zone is changed


@receiver(post_save, sender=RatePlan, dispatch_uid="rms:post_save_rate_plan")
def post_save_rate_plan(sender, instance: RatePlan, created, **kwargs):
    if created:
        RatePlanPercentageFactor.objects.create(rate_plan=instance, percentage_factor=0)
    DynamicPricingAdapter.invalidate_cache(instance.room_type.hotel.id)


@receiver(pre_save, sender=DynamicPricingSetting, dispatch_uid="rms:pre_save_dps")
def pre_save_dynamic_pricing_setting(sender, instance: DynamicPricingSetting, **kwargs):
    if instance.is_enabled and instance.default_base_rate == 0:
        raise ValidationError(
            "Default base rate must be greater than 0 if dynamic pricing is enabled."
        )


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


@receiver(post_save, sender=IntervalBaseRate, dispatch_uid="rms:rm_cache")
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
    original_periodic_task = instance.periodic_task

    crontab, _ = CrontabSchedule.objects.get_or_create(
        hour=str(instance.hour),
        minute="*",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone=instance.setting.hotel.timezone,
    )
    periodic_task, _ = PeriodicTask.objects.get_or_create(
        name=f"TimeBasedTriggerRule at {instance.hour} for {instance.setting.hotel}",
        task="backend.rms.tasks.handle_time_based_trigger",
        crontab=crontab,
        kwargs=json.dumps(
            {
                "hotel_id": instance.setting.hotel.id,
                "day_ahead": instance.day_ahead,
                "zone_info": str(instance.setting.hotel.timezone),
            }
        ),
        defaults={
            "start_time": timezone.now(),
        },
    )

    # Update directly to avoid calling save() method of instance
    TimeBasedTriggerRule.objects.filter(id=instance.id).update(
        periodic_task=periodic_task.id
    )

    # Inject the updated periodic task to instance
    instance.periodic_task = periodic_task

    # If the periodic task is updated, delete the original one if it is not used by other rules
    if not created and original_periodic_task.time_based_trigger_rules.count() == 0:
        original_periodic_task.delete()


@receiver(
    post_delete,
    sender=TimeBasedTriggerRule,
    dispatch_uid="rms:post_delete_time_based_trigger_rule",
)
def post_delete_time_based_trigger_rule(
    sender, instance: TimeBasedTriggerRule, **kwargs
):
    if instance.periodic_task.time_based_trigger_rules.count() == 0:
        instance.periodic_task.delete()
