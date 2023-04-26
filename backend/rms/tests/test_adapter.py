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
    assert len(adapter.occupancy_based_trigger_rules) == 0

    # No effect because is not enabled and rules are not active yet
    assert adapter.get_occupancy_based_factor(9) == (0, FactorChoices.PERCENTAGE)

    # Enable availability based
    setting.is_occupancy_based = True
    setting.save()

    # Load from db
    adapter.activate_rules()
    adapter.load_from_db()

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
    adapter = DynamicPricingAdapter(hotel=hotel, load_setting=False)
    last_rule = (
        LeadDaysBasedRule.objects.filter(setting=setting).order_by("-lead_days").first()
    )
    last_rule.percentage_factor = -2
    last_rule.save()
    lead_day_window = setting.lead_day_window

    # No effect because is not enabled and rules are not active yet
    assert adapter.get_lead_days_based_factor(
        date=timezone.localtime().date() + timezone.timedelta(days=lead_day_window + 1)
    ) == (0, FactorChoices.PERCENTAGE)

    # Enable lead days based
    setting.is_lead_days_based = True
    setting.save()

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

    assert adapter.get_lead_days_based_factor(
        date=timezone.localtime().date() + timezone.timedelta(days=lead_day_window + 1)
    ) == (-2, FactorChoices.PERCENTAGE)
    with pytest.raises(ValueError):
        adapter.get_lead_days_based_factor(
            date=timezone.localtime().date() - timezone.timedelta(days=1)
        )
    assert adapter.get_lead_days_based_factor(
        date=timezone.localtime().date() + timezone.timedelta(days=lead_day_window - 1)
    ) == (0, FactorChoices.PERCENTAGE)


def test_dynamic_pricing_adapter_weekday_based(
    hotel_factory, weekday_based_rule_factory
):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting
    # today weekday
    rule = weekday_based_rule_factory(
        weekday=timezone.localtime().weekday() + 1, setting=setting
    )
    adapter = DynamicPricingAdapter(hotel=hotel, load_setting=False)
    rule.percentage_factor = 10
    rule.save()

    # No effect because is not enabled and rules are not active yet
    assert adapter.get_weekday_based_factor(1) == (0, FactorChoices.PERCENTAGE)

    # Enable weekday based
    setting.is_weekday_based = True
    setting.save()

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

    assert len(adapter.weekday_based_rules) == 7
    assert adapter.get_weekday_based_factor(timezone.localtime()) == (
        10,
        FactorChoices.PERCENTAGE,
    )


def test_dynamic_pricing_adapter_month_based(hotel_factory, month_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting
    # today month
    rule = month_based_rule_factory(month=timezone.localtime().month, setting=setting)
    adapter = DynamicPricingAdapter(hotel=hotel, load_setting=False)
    rule.percentage_factor = 20
    rule.save()

    # No effect because is not enabled and rules are not active yet
    assert adapter.get_month_based_factor(1) == (0, FactorChoices.PERCENTAGE)

    # Enable month based
    setting.is_month_based = True
    setting.save()

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

    assert len(adapter.month_based_rules) == 12
    assert adapter.get_month_based_factor(timezone.localtime()) == (
        20,
        FactorChoices.PERCENTAGE,
    )


def test_dynamic_pricing_adapter_season_based(hotel_factory, season_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting

    # pick a random season
    start_date = timezone.localtime().date() - timezone.timedelta(days=1)
    end_date = timezone.localtime().date() + timezone.timedelta(days=1)
    season_based_rule_factory(
        setting=setting,
        start_day=start_date.day,
        start_month=start_date.month,
        end_day=end_date.day,
        end_month=end_date.month,
        percentage_factor=10,
    )
    adapter = DynamicPricingAdapter(hotel=hotel, load_setting=False)

    # No effect because is not enabled and rules are not active yet
    assert adapter.get_season_based_factor(1) == (0, FactorChoices.PERCENTAGE)

    # Enable season based
    setting.is_season_based = True
    setting.save()

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

    assert len(adapter.season_based_rules) == 1
    assert adapter.get_season_based_factor(timezone.localtime()) == (
        10,
        FactorChoices.PERCENTAGE,
    )

    # Out of season
    assert adapter.get_season_based_factor(
        timezone.localtime() + timezone.timedelta(days=2)
    ) == (0, FactorChoices.PERCENTAGE)


def test_dynamic_pricing_adapter_time_based(hotel_factory, time_based_rule_factory):
    hotel = hotel_factory()
    setting = hotel.dynamic_pricing_setting

    current_datetime = timezone.localtime()
    time_based_rule_factory(
        setting=setting,
        trigger_time=current_datetime.time(),
        percentage_factor=10,
        min_occupancy=5,
        max_occupancy=10,
        day_ahead=0,
    )
    adapter = DynamicPricingAdapter(hotel=hotel, load_setting=False)

    # No effect because is not enabled and rules are not active yet
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime, 5
    ) == (0, FactorChoices.PERCENTAGE)

    # Enable season based
    setting.is_time_based = True
    setting.save()

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

    assert len(adapter.time_based_trigger_rules) == 1
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime, 5
    ) == (10, FactorChoices.PERCENTAGE)

    # Availability out of range
    assert adapter.get_time_based_factor(
        current_datetime.date(), current_datetime, 11
    ) == (0, FactorChoices.PERCENTAGE)

    time_based_rule_factory(
        setting=setting,
        trigger_time=(current_datetime - timezone.timedelta(hours=1)).time(),
        percentage_factor=20,
        min_occupancy=5,
        max_occupancy=10,
        day_ahead=0,
    )

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

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
        trigger_time=(current_datetime - timezone.timedelta(hours=1)).time(),
        percentage_factor=50,
        min_occupancy=5,
        max_occupancy=10,
        day_ahead=1,
    )

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()
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

    # Create rules
    occupancy_based_rule_factory(setting=setting, min_occupancy=1, increment_factor=150)
    lead_days_based_rule_factory(setting=setting, lead_days=0, percentage_factor=50)

    current_datetime = timezone.localtime()
    adapter = DynamicPricingAdapter(hotel=hotel, load_setting=False)

    # Activate rules
    adapter.activate_rules()
    adapter.load_from_db()

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
