from datetime import datetime

from factory import Faker, LazyAttribute, Sequence, SubFactory, Trait
from factory.django import DjangoModelFactory

from backend.pms.tests.factories import HotelFactory

from ..models import (
    DynamicPricingSetting,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    RuleFactor,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


class DynamicPricingSettingFactory(DjangoModelFactory):
    hotel = SubFactory(HotelFactory)
    lead_day_window = Faker("pyint", min_value=35, max_value=365)
    default_base_rate = Faker("pyint", min_value=100, max_value=500)

    class Meta:
        model = DynamicPricingSetting
        django_get_or_create = ("hotel",)


class RuleFactoryFactory(DjangoModelFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Params:
        multiplier = Trait(
            increment_factor=0,
            percentage_factor=Faker("pyint", min_value=-50, max_value=50, step=5),
        )
        increment = Trait(
            increment_factor=Faker("pyint", min_value=50, max_value=500),
            percentage_factor=0,
        )

    class Meta:
        model = RuleFactor


class WeekdayBasedRuleFactory(RuleFactoryFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Meta:
        model = WeekdayBasedRule
        django_get_or_create = ("setting", "weekday")


class MonthBasedRuleFactory(RuleFactoryFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Meta:
        model = MonthBasedRule
        django_get_or_create = ("setting", "month")


class SeasonBasedRuleFactory(RuleFactoryFactory):
    setting = SubFactory(DynamicPricingSettingFactory)
    name = Faker("word")
    start_day = LazyAttribute(lambda o: datetime.strptime(o.d1, "%m/%d").day)
    start_month = LazyAttribute(lambda o: datetime.strptime(o.d1, "%m/%d").month)
    end_day = LazyAttribute(lambda o: datetime.strptime(o.d2, "%m/%d").day)
    end_month = LazyAttribute(lambda o: datetime.strptime(o.d2, "%m/%d").month)

    class Params:
        d1 = Faker("date", pattern="%m/%d")
        d2 = Faker("date", pattern="%m/%d")

    class Meta:
        model = SeasonBasedRule


class LeadDaysBasedRuleFactory(RuleFactoryFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Meta:
        model = LeadDaysBasedRule
        django_get_or_create = ("setting", "lead_days")


class OccupancyBasedTriggerRuleFactory(RuleFactoryFactory):
    setting = SubFactory(DynamicPricingSettingFactory)
    min_occupancy = Sequence(lambda n: n + 1)

    class Meta:
        model = OccupancyBasedTriggerRule
        django_get_or_create = ("setting", "min_occupancy")


class TimeBasedTriggerRuleFactory(RuleFactoryFactory):
    setting = SubFactory(DynamicPricingSettingFactory)
    hour = Faker("pyint", min_value=0, max_value=23)
    min_occupancy = Sequence(lambda n: n + 1)
    day_ahead = Faker(
        "pyint", min_value=0, max_value=TimeBasedTriggerRule.MAX_DAY_AHEAD
    )

    class Meta:
        model = TimeBasedTriggerRule
