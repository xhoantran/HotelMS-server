from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    DynamicPricingSetting,
    LeadDaysBasedRule,
    MonthBasedRule,
    WeekdayBasedRule,
)


@receiver(
    post_save,
    sender=DynamicPricingSetting,
    dispatch_uid="rms:post_save_dynamic_pricing_setting",
)
def post_save_dynamic_pricing_setting(
    sender, instance: DynamicPricingSetting, created, **kwargs
):
    if created:
        lead_days_based_rules = []
        for i in range(instance.lead_day_window + 1):
            lead_days_based_rules.append(
                LeadDaysBasedRule(setting=instance, lead_days=i + 1)
            )
        LeadDaysBasedRule.objects.bulk_create(lead_days_based_rules)

        weekday_based_rules = []
        for i in range(7):
            weekday_based_rules.append(
                WeekdayBasedRule(setting=instance, weekday=i + 1)
            )
        WeekdayBasedRule.objects.bulk_create(weekday_based_rules)

        month_based_rules = []
        for i in range(12):
            month_based_rules.append(MonthBasedRule(setting=instance, month=i + 1))
        MonthBasedRule.objects.bulk_create(month_based_rules)
