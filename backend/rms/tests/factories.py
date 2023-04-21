from datetime import datetime

from factory import Faker, LazyAttribute, Sequence, SubFactory, Trait
from factory.django import DjangoModelFactory

from backend.pms.tests.factories import HotelGroupFactory

from ..models import (
    AvailabilityBasedTriggerRule,
    DynamicPricingSetting,
    LeadDaysBasedRule,
    MonthBasedRule,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


class DynamicPricingSettingFactory(DjangoModelFactory):
    hotel_group = SubFactory(HotelGroupFactory)
    lead_day_window = Faker("pyint", min_value=35, max_value=365)

    class Meta:
        model = DynamicPricingSetting
        django_get_or_create = ("hotel_group",)


class WeekdayBasedRuleFactory(DjangoModelFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Meta:
        model = WeekdayBasedRule
        django_get_or_create = ("setting", "weekday")


class MonthBasedRuleFactory(DjangoModelFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Meta:
        model = MonthBasedRule
        django_get_or_create = ("setting", "month")


class SeasonBasedRuleFactory(DjangoModelFactory):
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


class LeadDaysBasedRuleFactory(DjangoModelFactory):
    setting = SubFactory(DynamicPricingSettingFactory)

    class Meta:
        model = LeadDaysBasedRule
        django_get_or_create = ("setting", "lead_days")


class AvailabilityBasedTriggerRuleFactory(DjangoModelFactory):
    setting = SubFactory(DynamicPricingSettingFactory)
    max_availability = Sequence(lambda n: n + 1)
    increment_factor = Faker("pyint", min_value=50, max_value=500)

    class Meta:
        model = AvailabilityBasedTriggerRule
        django_get_or_create = ("setting", "max_availability")


class TimeBasedTriggerRuleFactory(DjangoModelFactory):
    setting = SubFactory(DynamicPricingSettingFactory)
    trigger_time = Faker("time", pattern="%H:%M:%S")
    multiplier_factor = Faker("pydecimal", left_digits=1, right_digits=1, positive=True)
    min_availability = Faker("pyint", min_value=1, max_value=10)
    max_availability = LazyAttribute(lambda o: o.min_availability + o.availability_gap)
    is_today = True
    is_tomorrow = False
    is_active = True

    class Meta:
        model = TimeBasedTriggerRule

    class Params:
        availability_gap = Faker("pyint", min_value=1, max_value=10)
        tomorrow = Trait(
            is_today=False,
            is_tomorrow=True,
        )
