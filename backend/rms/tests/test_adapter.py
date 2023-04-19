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
    adapter.invalidate_cache()
    assert not cache.get(adapter.get_cache_key())


def test_dynamic_pricing_adapter_default(hotel_factory):
    with pytest.raises(ValueError):
        DynamicPricingAdapter(hotel=None)
    hotel = hotel_factory()
    adapter = DynamicPricingAdapter(hotel=hotel.id)  # uuid
    assert adapter.get_lead_days_based_factor(date=timezone.now().date()) == 1
    assert adapter.is_enabled
    assert not adapter.is_lead_days_based
    assert not adapter.is_weekday_based
    assert not adapter.is_month_based
    assert not adapter.is_season_based
    assert not adapter.is_availability_based


def test_dynamic_pricing_adapter_availability_based(
    hotel_factory, availability_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    # 1st: max_availability = 1
    # 2nd: max_availability = 2
    rules = availability_based_rule_factory.create_batch(2, setting=setting)
    adapter = DynamicPricingAdapter(hotel=hotel)
    assert len(adapter.availability_based_trigger_rules) == 0

    # No effect because setting is not enabled and already cached
    assert adapter.get_availability_based_factor(1) == 1

    # Invalidate cache
    adapter.invalidate_cache()

    # Enable availability based
    setting.is_availability_based = True
    setting.save()

    # Load from db
    adapter.load_from_db()
    assert adapter.is_availability_based
    assert len(adapter.availability_based_trigger_rules) == 2
    assert adapter.get_availability_based_factor(1) == rules[0].multiplier_factor
    assert adapter.get_availability_based_factor(2) == rules[1].multiplier_factor


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
            date=timezone.now().date() + timezone.timedelta(days=lead_day_window + 1)
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
            date=timezone.now().date() + timezone.timedelta(days=lead_day_window + 1)
        )
        == 1.5
    )
    with pytest.raises(ValueError):
        adapter.get_lead_days_based_factor(
            date=timezone.now().date() - timezone.timedelta(days=1)
        )
    assert (
        adapter.get_lead_days_based_factor(
            date=timezone.now().date() + timezone.timedelta(days=lead_day_window - 1)
        )
        == 1
    )


def test_dynamic_pricing_adapter_weekday_based(
    hotel_factory, weekday_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    # today weekday
    rule = weekday_based_rule_factory(weekday=timezone.now().weekday(), setting=setting)
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
    print(adapter.weekday_based_rules)
    assert len(adapter.weekday_based_rules) == 7
    assert adapter.get_weekday_based_factor(timezone.now()) == Decimal("1.1")


def test_dynamic_pricing_adapter_month_based(hotel_factory, month_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting
    # today month
    rule = month_based_rule_factory(month=timezone.now().month, setting=setting)
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
    assert adapter.get_month_based_factor(timezone.now()) == Decimal("1.1")


def test_dynamic_pricing_adapter_season_based(hotel_factory, season_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.group.dynamic_pricing_setting

    # pick a random season
    start_date = timezone.now().date() - timezone.timedelta(days=1)
    end_date = timezone.now().date() + timezone.timedelta(days=1)
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
    assert adapter.get_season_based_factor(timezone.now()) == Decimal("1.1")

    # Out of season
    assert (
        adapter.get_season_based_factor(timezone.now() + timezone.timedelta(days=2))
        == 1
    )
