import pytest

from ..models import SeasonBasedRule


def test_weekday_based_rule_save(db, weekday_based_rule_factory):
    rule = weekday_based_rule_factory(weekday=1)
    assert rule.weekday == 1
    assert rule.multiplier_factor == 1

    rule.weekday = 8
    with pytest.raises(ValueError):
        rule.save()

    rule.weekday = 1
    rule.multiplier_factor = 1.1
    rule.save()
    assert rule.multiplier_factor == 1.1


def test_month_based_rule_save(db, month_based_rule_factory):
    rule = month_based_rule_factory(month=1)
    assert rule.month == 1
    assert rule.multiplier_factor == 1

    rule.month = 13
    with pytest.raises(ValueError):
        rule.save()

    rule.month = 1
    rule.multiplier_factor = 1.1
    rule.save()
    assert rule.multiplier_factor == 1.1


def test_season_based_rule_save(
    db,
    season_based_rule_factory,
    dynamic_pricing_setting_factory,
):
    season_based_rule_factory()
    with pytest.raises(ValueError):
        setting = dynamic_pricing_setting_factory()
        SeasonBasedRule.objects.create(
            setting=setting,
            name="Christmas but invalid...",
            start_month=12,
            start_day=25,
            end_month=12,
            end_day=32,
        )
