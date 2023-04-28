import datetime
from zoneinfo import ZoneInfo

import pytest
from django.core.cache import cache
from django.utils import timezone

from ..adapter import DynamicPricingAdapter
from ..models import FactorChoices, LeadDaysBasedRule


def test_dynamic_pricing_adapter_cache(
    hotel_factory,
    room_type_factory,
    django_assert_num_queries,
):
    hotel = hotel_factory()
    room_type_factory.create_batch(10, hotel=hotel)
    hotel_id = str(hotel.id)
    adapter = DynamicPricingAdapter(hotel=hotel)
    db_weekday_based_rules = adapter.weekday_based_rules
    db_month_based_rules = adapter.month_based_rules
    db_season_based_rules = adapter.season_based_rules
    db_occupancy_based_trigger_rules = adapter.occupancy_based_trigger_rules
    db_lead_days_based_rules = adapter.lead_days_based_rules
    db_time_based_trigger_rules = adapter.time_based_trigger_rules
    with django_assert_num_queries(1):
        adapter = DynamicPricingAdapter(hotel=hotel_id)
        assert adapter.weekday_based_rules == db_weekday_based_rules
        assert adapter.month_based_rules == db_month_based_rules
        assert adapter.season_based_rules == db_season_based_rules
        assert adapter.occupancy_based_trigger_rules == db_occupancy_based_trigger_rules
        assert adapter.lead_days_based_rules == db_lead_days_based_rules
        assert adapter.time_based_trigger_rules == db_time_based_trigger_rules
    adapter.invalidate_cache(setting_id=hotel.dynamic_pricing_setting.id)
    assert not cache.get(
        adapter.get_cache_key(setting_id=hotel.dynamic_pricing_setting.id)
    )


def test_dynamic_pricing_adapter_default():
    with pytest.raises(ValueError):
        DynamicPricingAdapter(hotel=None)


def test_dynamic_pricing_adapter_occupancy_based(
    hotel_factory, occupancy_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting

    # Occupancy based rules are not enabled by default
    assert not setting.is_occupancy_based
    adapter = DynamicPricingAdapter(hotel=hotel)
    assert adapter.get_occupancy_based_factor(10) == (0, FactorChoices.PERCENTAGE)

    setting.is_occupancy_based = True
    setting.save()

    occupancy_based_rule_factory(
        setting=setting,
        min_occupancy=10,
        increment_factor=100000,
    )
    occupancy_based_rule_factory(
        setting=setting,
        min_occupancy=20,
        percentage_factor=2,
    )
    adapter = DynamicPricingAdapter(hotel=hotel)

    assert len(adapter.occupancy_based_trigger_rules) == 2
    assert adapter.get_occupancy_based_factor(9) == (0, FactorChoices.PERCENTAGE)
    assert adapter.get_occupancy_based_factor(10) == (100000, FactorChoices.INCREMENT)
    assert adapter.get_occupancy_based_factor(11) == (100000, FactorChoices.INCREMENT)
    assert adapter.get_occupancy_based_factor(19) == (100000, FactorChoices.INCREMENT)
    assert adapter.get_occupancy_based_factor(20) == (2, FactorChoices.PERCENTAGE)
    assert adapter.get_occupancy_based_factor(21) == (2, FactorChoices.PERCENTAGE)


def test_dynamic_pricing_adapter_lead_days_based(hotel_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting
    setting.is_lead_days_based = True
    setting.save()

    last_rule = (
        LeadDaysBasedRule.objects.filter(setting=setting).order_by("-lead_days").first()
    )
    last_rule.percentage_factor = -2
    last_rule.save()

    lead_day_window = setting.lead_day_window
    current_datetime = timezone.now()

    adapter = DynamicPricingAdapter(hotel=hotel)

    assert adapter.get_lead_days_based_factor(
        date=current_datetime.date() + timezone.timedelta(days=lead_day_window + 1),
        current_datetime=current_datetime,
    ) == (-2, FactorChoices.PERCENTAGE)
    with pytest.raises(ValueError):
        adapter.get_lead_days_based_factor(
            date=current_datetime.date() - timezone.timedelta(days=1),
            current_datetime=current_datetime,
        )
    assert adapter.get_lead_days_based_factor(
        date=current_datetime.date() + timezone.timedelta(days=lead_day_window - 1),
        current_datetime=current_datetime,
    ) == (0, FactorChoices.PERCENTAGE)


def test_dynamic_pricing_adapter_weekday_based(
    hotel_factory, weekday_based_rule_factory
):
    hotel = hotel_factory(timezone="Asia/Kolkata")
    setting = hotel.dynamic_pricing_setting
    setting.is_weekday_based = True
    setting.save()

    local_datetime = timezone.localtime(timezone.now(), ZoneInfo("Asia/Kolkata"))

    # today weekday
    rule = weekday_based_rule_factory(
        setting=setting,
        weekday=local_datetime.weekday() + 1,  # weekday starts from 1
    )
    rule.percentage_factor = 10
    rule.save()

    adapter = DynamicPricingAdapter(hotel=hotel)

    assert len(adapter.weekday_based_rules) == 7
    assert adapter.get_weekday_based_factor(local_datetime.date()) == (
        10,
        FactorChoices.PERCENTAGE,
    )


def test_dynamic_pricing_adapter_month_based(hotel_factory, month_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting
    setting.is_month_based = True
    setting.save()

    rule = month_based_rule_factory(month=timezone.now().month, setting=setting)
    adapter = DynamicPricingAdapter(hotel=hotel)
    rule.percentage_factor = 20
    rule.save()

    adapter = DynamicPricingAdapter(hotel=hotel)

    assert len(adapter.month_based_rules) == 12
    assert adapter.get_month_based_factor(timezone.now()) == (
        20,
        FactorChoices.PERCENTAGE,
    )


def test_dynamic_pricing_adapter_season_based(hotel_factory, season_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting
    setting.is_season_based = True
    setting.save()

    # pick a random season
    start_date = timezone.now().date() - timezone.timedelta(days=1)
    end_date = timezone.now().date() + timezone.timedelta(days=1)
    season_based_rule_factory(
        setting=setting,
        start_day=start_date.day,
        start_month=start_date.month,
        end_day=end_date.day,
        end_month=end_date.month,
        percentage_factor=10,
    )

    adapter = DynamicPricingAdapter(hotel=hotel)

    assert len(adapter.season_based_rules) == 1
    assert adapter.get_season_based_factor(timezone.now()) == (
        10,
        FactorChoices.PERCENTAGE,
    )

    # Out of season
    assert adapter.get_season_based_factor(
        timezone.now() + timezone.timedelta(days=2)
    ) == (0, FactorChoices.PERCENTAGE)


def test_dynamic_pricing_adapter_time_based(hotel_factory, time_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting
    setting.is_time_based = True
    setting.save()

    # Define a rule for 10:00 AM
    current_datetime = timezone.now().replace(hour=10, minute=0)
    time_based_rule_factory(
        setting=setting,
        hour=current_datetime.hour,
        minute=current_datetime.minute,
        percentage_factor=10,
        min_occupancy=5,
        max_occupancy=10,
        day_ahead=0,
    )

    adapter = DynamicPricingAdapter(hotel=hotel)

    assert len(adapter.time_based_trigger_rules) == 1
    # It should trigger
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime, 5
    ) == (10, FactorChoices.PERCENTAGE)

    # It should also work with UTC time
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime.astimezone(datetime.timezone.utc), 5
    ) == (10, FactorChoices.PERCENTAGE)

    # It should not trigger
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime.replace(hour=9), 5
    ) == (0, FactorChoices.PERCENTAGE)

    # Availability out of range
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime, 11
    ) == (0, FactorChoices.PERCENTAGE)

    time_based_rule_factory(
        setting=setting,
        hour=current_datetime.hour,
        minute=current_datetime.minute,
        percentage_factor=20,
        min_occupancy=5,
        max_occupancy=10,
        day_ahead=0,
    )

    adapter = DynamicPricingAdapter(hotel=hotel)

    # It should pick the one with the latest trigger time
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime, 5
    ) == (10, FactorChoices.PERCENTAGE)
    with pytest.raises(ValueError):
        adapter.get_time_based_factor(
            current_datetime.date() - timezone.timedelta(days=1), current_datetime, 5
        )

    time_based_rule_factory(
        setting=setting,
        hour=9,
        minute=0,
        percentage_factor=50,
        min_occupancy=5,
        max_occupancy=10,
        day_ahead=1,
    )

    adapter = DynamicPricingAdapter(hotel=hotel)

    # The only rule that matches is the one with day_ahead=1
    assert adapter.get_time_based_factor(
        current_datetime.date() + timezone.timedelta(days=1),
        current_datetime,
        5,
    ) == (50, FactorChoices.PERCENTAGE)


def test_dynamic_pricing_adapter_calculate_rate(
    hotel_factory,
    occupancy_based_rule_factory,
    lead_days_based_rule_factory,
):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting

    # Enable availability based and lead days based
    setting.is_occupancy_based = True
    setting.is_lead_days_based = True
    setting.save()

    # Calculate rate with no rules
    adapter = DynamicPricingAdapter(hotel=hotel)
    assert (
        adapter.calculate_rate(
            date=timezone.now().date(),
            current_datetime=timezone.now(),
            occupancy=10,
            rate=100,
        )
        == 100
    )

    # Create rules
    occupancy_based_rule_factory(setting=setting, min_occupancy=1, increment_factor=150)
    lead_days_based_rule_factory(setting=setting, lead_days=0, percentage_factor=50)

    current_datetime = timezone.now()
    adapter = DynamicPricingAdapter(hotel=hotel)

    assert (
        adapter.calculate_rate(
            date=current_datetime.date(),
            current_datetime=current_datetime,
            occupancy=0,
            rate=100,
        )
        == 150
    )
    assert (
        adapter.calculate_rate(
            date=current_datetime.date(),
            current_datetime=current_datetime,
            occupancy=1,
            rate=100,
        )
        == 300
    )

    # Not enabled
    setting.is_enabled = False
    setting.save()

    adapter = DynamicPricingAdapter(hotel=hotel)
    assert (
        adapter.calculate_rate(
            date=current_datetime.date(),
            current_datetime=current_datetime,
            occupancy=1,
            rate=100,
        )
        == 100
    )
