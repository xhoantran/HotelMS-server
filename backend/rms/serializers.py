from rest_framework import serializers

from .models import (
    AvailabilityBasedTriggerRule,
    DynamicPricingSetting,
    LeadDaysBasedRule,
    MonthBasedRule,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


class DynamicPricingSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricingSetting
        fields = "__all__"


class LeadDaysBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadDaysBasedRule
        fields = "__all__"


class WeekdayBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekdayBasedRule
        fields = "__all__"


class MonthBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthBasedRule
        fields = "__all__"


class SeasonBasedRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonBasedRule
        fields = "__all__"


class AvailabilityBasedTriggerRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBasedTriggerRule
        fields = "__all__"


class TimeBasedTriggerRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeBasedTriggerRule
        fields = "__all__"
