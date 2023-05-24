import json

from ..models import TimeBasedTriggerRule


def test_post_save_time_based_trigger_rule(
    hotel_factory,
    dynamic_pricing_setting_factory,
    time_based_rule_factory,
):
    hotel = hotel_factory()
    setting = dynamic_pricing_setting_factory(hotel=hotel)
    setting.is_time_based = True
    setting.save()
    rule = time_based_rule_factory(
        setting=setting,
        hour=10,
        increment_factor=10000,
    )
    assert rule.periodic_task is not None
    assert rule.periodic_task.crontab.hour == "10"
    assert rule.periodic_task.crontab.minute == "*"
    assert rule.periodic_task.crontab.day_of_week == "*"
    assert rule.periodic_task.crontab.day_of_month == "*"
    assert rule.periodic_task.crontab.month_of_year == "*"
    assert str(rule.periodic_task.crontab.timezone) == str(hotel.timezone)
    assert rule.periodic_task.kwargs == json.dumps(
        {
            "hotel_id": hotel.id,
            "day_ahead": rule.day_ahead,
            "zone_info": str(hotel.timezone),
        }
    )

    # Update trigger time
    rule.hour = 11
    rule.save()
    rule = TimeBasedTriggerRule.objects.get(setting=setting, id=rule.id)
    assert rule.periodic_task is not None
    assert rule.periodic_task.crontab.hour == "11"
    assert rule.periodic_task.crontab.minute == "*"
    assert rule.periodic_task.crontab.day_of_week == "*"
    assert rule.periodic_task.crontab.day_of_month == "*"
    assert rule.periodic_task.crontab.month_of_year == "*"
    assert str(rule.periodic_task.crontab.timezone) == str(hotel.timezone)


def test_post_save_dynamic_pricing_setting(
    hotel_factory,
    dynamic_pricing_setting_factory,
    time_based_rule_factory,
):
    hotel = hotel_factory()
    setting = dynamic_pricing_setting_factory(hotel=hotel)
    setting.is_time_based = True
    setting.save()
    rule = time_based_rule_factory(
        setting=setting,
        hour=10,
        increment_factor=100000,
    )
    rule = TimeBasedTriggerRule.objects.get(setting=setting)
    assert rule.periodic_task is not None
    assert rule.periodic_task.enabled is True

    # Disable setting
    setting.is_time_based = False
    setting.save()
    rule = TimeBasedTriggerRule.objects.get(setting=setting)
    assert rule.periodic_task is not None
    assert not rule.periodic_task.enabled

    # Enable setting
    setting.is_time_based = True
    setting.save()
    rule = TimeBasedTriggerRule.objects.get(setting=setting)
    assert rule.periodic_task is not None
    assert not rule.periodic_task.enabled

    setting.is_enabled = True
    setting.default_base_rate = 100000
    setting.save()
    rule = TimeBasedTriggerRule.objects.get(setting=setting)
    assert rule.periodic_task is not None
    assert rule.periodic_task.enabled
