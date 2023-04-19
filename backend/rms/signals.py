from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    DynamicPricingSetting,
    HotelGroup,
    LeadDaysBasedRule,
    MonthBasedRule,
    WeekdayBasedRule,
)


@receiver(
    post_save,
    sender=HotelGroup,
    dispatch_uid="rms:post_save_hotel_group",
)
def post_save_hotel_group(sender, instance: HotelGroup, created, **kwargs):
    if created:
        setting = DynamicPricingSetting.objects.create(hotel_group=instance)
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
