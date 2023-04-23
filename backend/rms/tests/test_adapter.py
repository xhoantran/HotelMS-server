from decimal import Decimal

import pytest
from django.core.cache import cache
from django.utils import timezone

from ..adapter import DynamicPricingAdapter
from ..models import LeadDaysBasedRule


def test_dynamic_pricing_adapter_cache(
    hotel_factory,
    room_type_factory,
    hotel_group_factory,
    django_assert_num_queries,
):
    group = hotel_group_factory()
    hotel = hotel_factory(group=group)
    room_type_factory.create_batch(10, hotel=hotel)
    hotel_id = str(hotel.id)
    adapter = DynamicPricingAdapter(hotel=hotel)
    db_weekday_based_rules = adapter.weekday_based_rules
    db_month_based_rules = adapter.month_based_rules
    db_season_based_rules = adapter.season_based_rules
    db_availability_based_trigger_rules = adapter.availability_based_trigger_rules
    db_lead_days_based_rules = adapter.lead_days_based_rules
    db_time_based_trigger_rules = adapter.time_based_trigger_rules
    with django_assert_num_queries(1):
        adapter = DynamicPricingAdapter(hotel=hotel_id)
        assert adapter.weekday_based_rules == db_weekday_based_rules
        assert adapter.month_based_rules == db_month_based_rules
        assert adapter.season_based_rules == db_season_based_rules
        assert (
            adapter.availability_based_trigger_rules
            == db_availability_based_trigger_rules
        )
        assert adapter.lead_days_based_rules == db_lead_days_based_rules
        assert adapter.time_based_trigger_rules == db_time_based_trigger_rules
    adapter.invalidate_cache()
    assert not cache.get(adapter.get_cache_key())


def test_dynamic_pricing_adapter_default(hotel_factory):
    with pytest.raises(ValueError):
        DynamicPricingAdapter(hotel=None)
    hotel = hotel_factory()
    adapter = DynamicPricingAdapter(hotel=hotel.id)  # uuid
    assert adapter.get_lead_days_based_factor(date=timezone.localtime().date()) == 1
    assert adapter.is_enabled
    assert not adapter.is_lead_days_based
    assert not adapter.is_weekday_based
    assert not adapter.is_month_based
    assert not adapter.is_season_based
    assert not adapter.is_availability_based
    assert not adapter.is_time_based


def test_dynamic_pricing_adapter_availability_based(
    hotel_factory, availability_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    availability_based_rule_factory(
        setting=setting,
        max_availability=20,
        increment_factor=100000,
    )
    availability_based_rule_factory(
        setting=setting,
        max_availability=10,
        increment_factor=200000,
    )
    adapter = DynamicPricingAdapter(hotel=hotel)
    assert len(adapter.availability_based_trigger_rules) == 0

    # No effect because setting is not enabled and already cached
    assert adapter.get_availability_based_factor(1) == 0

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable availability based
    setting.is_availability_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_availability_based
    assert len(adapter.availability_based_trigger_rules) == 2
    assert adapter.get_availability_based_factor(9) == 200000
    assert adapter.get_availability_based_factor(10) == 200000
    assert adapter.get_availability_based_factor(11) == 100000


def test_dynamic_pricing_adapter_lead_days_based(hotel_factory):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    adapter = DynamicPricingAdapter(hotel=hotel)
    last_rule = (
        LeadDaysBasedRule.objects.filter(setting=setting).order_by("-lead_days").first()
    )
    last_rule.multiplier_factor = 1.5
    last_rule.save()
    lead_day_window = setting.lead_day_window

    # No effect because setting is not enabled and already cached
    assert (
        adapter.get_lead_days_based_factor(
            date=timezone.localtime().date()
            + timezone.timedelta(days=lead_day_window + 1)
        )
        == 1
    )

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable lead days based
    setting.is_lead_days_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_lead_days_based
    assert (
        adapter.get_lead_days_based_factor(
            date=timezone.localtime().date()
            + timezone.timedelta(days=lead_day_window + 1)
        )
        == 1.5
    )
    with pytest.raises(ValueError):
        adapter.get_lead_days_based_factor(
            date=timezone.localtime().date() - timezone.timedelta(days=1)
        )
    assert (
        adapter.get_lead_days_based_factor(
            date=timezone.localtime().date()
            + timezone.timedelta(days=lead_day_window - 1)
        )
        == 1
    )


def test_dynamic_pricing_adapter_weekday_based(
    hotel_factory, weekday_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    # today weekday
    rule = weekday_based_rule_factory(
        weekday=timezone.localtime().weekday() + 1, setting=setting
    )
    adapter = DynamicPricingAdapter(hotel=hotel)
    rule.multiplier_factor = 1.1
    rule.save()

    # No effect because setting is not enabled and already cached
    assert adapter.get_weekday_based_factor(1) == 1

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable weekday based
    setting.is_weekday_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_weekday_based
    assert len(adapter.weekday_based_rules) == 7
    assert adapter.get_weekday_based_factor(timezone.localtime()) == Decimal("1.1")


def test_dynamic_pricing_adapter_month_based(hotel_factory, month_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    # today month
    rule = month_based_rule_factory(month=timezone.localtime().month, setting=setting)
    adapter = DynamicPricingAdapter(hotel=hotel)
    rule.multiplier_factor = 1.1
    rule.save()

    # No effect because setting is not enabled and already cached
    assert adapter.get_month_based_factor(1) == 1

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable month based
    setting.is_month_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_month_based
    assert len(adapter.month_based_rules) == 12
    assert adapter.get_month_based_factor(timezone.localtime()) == Decimal("1.1")


def test_dynamic_pricing_adapter_season_based(hotel_factory, season_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting

    # pick a random season
    start_date = timezone.localtime().date() - timezone.timedelta(days=1)
    end_date = timezone.localtime().date() + timezone.timedelta(days=1)
    rule = season_based_rule_factory(
        setting=setting,
        start_day=start_date.day,
        start_month=start_date.month,
        end_day=end_date.day,
        end_month=end_date.month,
    )
    adapter = DynamicPricingAdapter(hotel=hotel)
    rule.multiplier_factor = 1.1
    rule.save()

    # No effect because setting is not enabled and already cached
    assert adapter.get_season_based_factor(1) == 1

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable season based
    setting.is_season_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_season_based
    assert len(adapter.season_based_rules) == 1
    assert adapter.get_season_based_factor(timezone.localtime()) == Decimal("1.1")

    # Out of season
    assert (
        adapter.get_season_based_factor(
            timezone.localtime() + timezone.timedelta(days=2)
        )
        == 1
    )


def test_dynamic_pricing_adapter_calculate_rate(
    hotel_factory, availability_based_rule_factory, lead_days_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting

    # Enable availability based and lead days based
    setting.is_availability_based = True
    setting.is_lead_days_based = True
    setting.save()

    # Create rules
    availability_based_rule_factory(
        setting=setting,
        increment_factor=100,
        max_availability=10,
    )
    lead_day_rule = lead_days_based_rule_factory(
        setting=setting,
        lead_days=1,
    )
    lead_day_rule.multiplier_factor = 1.5
    lead_day_rule.save()

    adapter = DynamicPricingAdapter(hotel=hotel)
    assert (
        adapter.calculate_rate(
            date=timezone.localtime().date(),
            availability=11,
            rate=100,
        )
        == 150
    )
    assert (
        adapter.calculate_rate(
            date=timezone.localtime().date(),
            availability=10,
            rate=100,
        )
        == 300
    )


def test_dynamic_pricing_adapter_time_based(hotel_factory, time_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting

    current_time = timezone.localtime().time()
    rule = time_based_rule_factory(
        setting=setting,
        trigger_time=current_time,
        multiplier_factor=1.1,
        min_availability=1,
        max_availability=10,
        is_today=True,
        is_tomorrow=False,
        is_active=True,
    )
    adapter = DynamicPricingAdapter(hotel=hotel)
    rule.multiplier_factor = 1.1
    rule.save()

    # No effect because setting is not enabled and already cached
    assert adapter.get_time_based_factor(current_time, 5) == 1

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable season based
    setting.is_time_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_time_based
    assert len(adapter.time_based_trigger_rules) == 1
    assert adapter.get_time_based_factor(current_time, 5) == Decimal("1.1")

    # Availability out of range
    assert adapter.get_time_based_factor(current_time, 11) == 1
