from datetime import datetime

from factory import Faker, LazyAttribute, Sequence, SubFactory
from factory.django import DjangoModelFactory

from backend.pms.tests.factories import HotelFactory

from ..models import (
    AvailabilityBasedTriggerRule,
    DynamicPricingSetting,
    HotelGroup,
    LeadDaysBasedRule,
    MonthBasedRule,
    SeasonBasedRule,
    WeekdayBasedRule,
)


class HotelGroupFactory(DjangoModelFactory):
    name = Faker("word")

    class Meta:
        model = HotelGroup
        django_get_or_create = ("name",)


class DynamicPricingSettingFactory(DjangoModelFactory):
    hotel_group = SubFactory(HotelGroupFactory)

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

    class Meta:
        model = AvailabilityBasedTriggerRule
        django_get_or_create = ("setting", "max_availability")
