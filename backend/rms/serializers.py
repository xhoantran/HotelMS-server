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


class DynamicPricingSettingReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricingSetting
        fields = ("uuid", "is_enabled", "created_at", "updated_at")


class RuleFactorSerializer(serializers.ModelSerializer):
    setting = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DynamicPricingSetting.objects.all(),
    )

    class Meta:
        exclude = ("id",)
        extra_kwargs = {
            "increment_factor": {"required": True},
            "percentage_factor": {"required": True},
        }


class LeadDaysBasedRuleSerializer(RuleFactorSerializer):
    class Meta(RuleFactorSerializer.Meta):
        model = LeadDaysBasedRule


class WeekdayBasedRuleSerializer(RuleFactorSerializer):
    class Meta(RuleFactorSerializer.Meta):
        model = WeekdayBasedRule


class MonthBasedRuleSerializer(RuleFactorSerializer):
    class Meta(RuleFactorSerializer.Meta):
        model = MonthBasedRule


class SeasonBasedRuleSerializer(RuleFactorSerializer):
    class Meta(RuleFactorSerializer.Meta):
        model = SeasonBasedRule


class OccupancyBasedTriggerRuleSerializer(RuleFactorSerializer):
    class Meta(RuleFactorSerializer.Meta):
        model = OccupancyBasedTriggerRule


class TimeBasedTriggerRuleSerializer(RuleFactorSerializer):
    class Meta(RuleFactorSerializer.Meta):
        model = TimeBasedTriggerRule


class DynamicPricingSettingSerializer(serializers.ModelSerializer):
    occupancy_based_trigger_rules = OccupancyBasedTriggerRuleSerializer(
        required=False, read_only=True, many=True
    )
    time_based_trigger_rules = TimeBasedTriggerRuleSerializer(
        required=False, read_only=True, many=True
    )

    class Meta:
        model = DynamicPricingSetting
        exclude = ("id", "hotel")
