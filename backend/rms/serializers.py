from rest_framework import serializers

from .models import (
    DynamicPricingSetting,
    IntervalBaseRate,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    RatePlanPercentageFactor,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


class RatePlanPercentageFactorSerializer(serializers.ModelSerializer):
    rate_plan = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = RatePlanPercentageFactor
        fields = ("rate_plan", "percentage_factor")


class DynamicPricingSettingReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricingSetting
        fields = ("uuid", "is_enabled", "created_at", "updated_at")


class IntervalBaseRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntervalBaseRate
        exclude = ("id",)


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
    rate_plan_percentage_factors = serializers.SerializerMethodField()

    class Meta:
        model = DynamicPricingSetting
        exclude = ("id", "hotel")

    def get_rate_plan_percentage_factors(self, obj):
        rate_plan_percentage_factors = RatePlanPercentageFactor.objects.filter(
            rate_plan__room_type__hotel=obj.hotel
        )
        return RatePlanPercentageFactorSerializer(
            rate_plan_percentage_factors, many=True
        ).data
