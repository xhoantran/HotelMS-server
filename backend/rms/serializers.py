from rest_framework import serializers

from .models import (
    DynamicPricingSetting,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


class DynamicPricingSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricingSetting
        exclude = ("id", "hotel")


class LeadDaysBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadDaysBasedRule
        exclude = ("id",)


class WeekdayBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekdayBasedRule
        exclude = ("id",)


class MonthBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthBasedRule
        exclude = ("id",)


class SeasonBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonBasedRule
        exclude = ("id",)


class OccupancyBasedTriggerRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccupancyBasedTriggerRule
        exclude = ("id",)


class TimeBasedTriggerRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeBasedTriggerRule
        exclude = ("id",)
