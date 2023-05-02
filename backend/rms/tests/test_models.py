import pytest
from django.core.exceptions import ValidationError

from ..models import (
    PeriodicTask,
    RuleNotEnabledError,
    SeasonBasedRule,
    TimeBasedTriggerRule,
)


def test_rule_factor_save(
    db,
    dynamic_pricing_setting_factory,
    occupancy_based_rule_factory,
):
    setting = dynamic_pricing_setting_factory()

    with pytest.raises(RuleNotEnabledError):
        occupancy_based_rule_factory(
            percentage_factor=20,
            setting=setting,
        )

    setting.is_occupancy_based = True
    setting.save()

    with pytest.raises(ValidationError):
        occupancy_based_rule_factory(
            percentage_factor=-101,
            setting=setting,
        )

    with pytest.raises(ValidationError):
        occupancy_based_rule_factory(
            percentage_factor=2,
            increment_factor=1,
            setting=setting,
        )

    with pytest.raises(ValidationError):
        occupancy_based_rule_factory(
            percentage_factor=0,
            increment_factor=0,
            setting=setting,
        )


def test_lead_days_based_rule_save(
    db,
    dynamic_pricing_setting_factory,
    lead_days_based_rule_factory,
):
    setting = dynamic_pricing_setting_factory()

    with pytest.raises(RuleNotEnabledError):
        rule = lead_days_based_rule_factory(
            setting=setting,
            lead_days=1,
        )
        rule.save()

    setting.is_lead_days_based = True
    setting.save()

    rule = lead_days_based_rule_factory(
        setting=setting,
        lead_days=1,
    )


def test_weekday_based_rule_save(
    db,
    dynamic_pricing_setting_factory,
    weekday_based_rule_factory,
):
    setting = dynamic_pricing_setting_factory()

    with pytest.raises(RuleNotEnabledError):
        rule = weekday_based_rule_factory(weekday=1, setting=setting)
        rule.save()

    setting.is_weekday_based = True
    setting.save()

    rule = weekday_based_rule_factory(weekday=1, setting=setting)
    assert rule.setting == setting
    assert rule.weekday == 1

    rule.increment_factor = 100000
    rule.weekday = 8
    with pytest.raises(ValidationError):
        rule.save()

    rule.weekday = 1
    rule.save()
    assert rule.weekday == 1


def test_month_based_rule_save(
    db,
    dynamic_pricing_setting_factory,
    month_based_rule_factory,
):
    setting = dynamic_pricing_setting_factory()

    with pytest.raises(RuleNotEnabledError):
        rule = month_based_rule_factory(month=1, setting=setting)
        rule.save()

    setting.is_month_based = True
    setting.save()

    rule = month_based_rule_factory(month=1, setting=setting)
    assert rule.month == 1
    rule.increment_factor = 100000

    rule.month = 13
    with pytest.raises(ValidationError):
        rule.save()

    rule.month = 1
    rule.save()
    assert rule.month == 1


def test_season_based_rule_save(
    db,
    dynamic_pricing_setting_factory,
    season_based_rule_factory,
):
    setting = dynamic_pricing_setting_factory()

    with pytest.raises(RuleNotEnabledError):
        season_based_rule_factory(
            setting=setting,
            name="Christmas",
            percentage_factor=20,
            start_month=12,
            start_day=25,
            end_month=12,
            end_day=31,
        )

    setting.is_season_based = True
    setting.save()

    season_based_rule_factory(percentage_factor=20, setting=setting)
    with pytest.raises(ValidationError):
        SeasonBasedRule.objects.create(
            setting=setting,
            name="Christmas but invalid...",
            percentage_factor=20,
            start_month=12,
            start_day=25,
            end_month=12,
            end_day=32,
        )


def test_time_based_rule_save(
    db,
    dynamic_pricing_setting_factory,
    time_based_rule_factory,
):
    setting = dynamic_pricing_setting_factory()

    with pytest.raises(RuleNotEnabledError):
        time_based_rule_factory(setting=setting)

    setting.is_time_based = True
    setting.save()

    with pytest.raises(ValidationError):
        time_based_rule_factory(
            setting=setting,
            hour=24,
            minute=0,
            increment_factor=200000,
        )
    with pytest.raises(ValidationError):
        time_based_rule_factory(
            setting=setting,
            hour=4,
            minute=60,
            increment_factor=200000,
        )
    with pytest.raises(ValidationError):
        time_based_rule_factory(
            setting=setting,
            hour=23,
            minute=59,
            increment_factor=200000,
            min_occupancy=1,
            max_occupancy=0,
        )
    with pytest.raises(ValidationError):
        time_based_rule_factory(
            setting=setting,
            hour=23,
            minute=59,
            increment_factor=200000,
            min_occupancy=0,
            max_occupancy=1,
            day_ahead=TimeBasedTriggerRule.MAX_DAY_AHEAD + 1,
        )

    rule = time_based_rule_factory(
        setting=setting,
        hour=23,
        minute=59,
        increment_factor=200000,
    )
    assert TimeBasedTriggerRule.objects.count() == 1
    assert PeriodicTask.objects.count() == 1
    rule.delete()
    assert TimeBasedTriggerRule.objects.count() == 0
    assert PeriodicTask.objects.count() == 0
