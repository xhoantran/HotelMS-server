from rest_framework import serializers

from backend.pms.models import RatePlan, RoomType
from backend.utils.serializers import DateRangeField

from .models import (
    DynamicPricingSetting,
    IntervalBaseRate,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    RMSRatePlan,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)


class RatePlanPercentageFactorWriteOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = RMSRatePlan
        fields = ("percentage_factor", "increment_factor")


class RMSRatePlanSerializer(serializers.ModelSerializer):
    percentage_factor = serializers.SerializerMethodField()
    increment_factor = serializers.SerializerMethodField()

    class Meta:
        model = RatePlan
        fields = ("uuid", "name", "percentage_factor", "increment_factor")

    def get_percentage_factor(self, obj):
        return obj.rms.percentage_factor

    def get_increment_factor(self, obj):
        return obj.rms.increment_factor


class RMSRoomTypeSerializer(serializers.ModelSerializer):
    rate_plans = RMSRatePlanSerializer(many=True, read_only=True)

    class Meta:
        model = RoomType
        fields = ("uuid", "name", "rate_plans")


class DynamicPricingSettingReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricingSetting
        fields = ("uuid", "is_enabled", "created_at", "updated_at")


class IntervalBaseRateSerializer(serializers.ModelSerializer):
    setting = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DynamicPricingSetting.objects.all(),
    )
    dates = DateRangeField()

    class Meta:
        model = IntervalBaseRate
        exclude = ("id",)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if hasattr(self.instance, "pk"):
            setting_id = self.instance.setting.pk
            query = IntervalBaseRate.objects.filter(
                setting_id=setting_id,
                dates__overlap=attrs["dates"],
            ).exclude(pk=self.instance.pk)
        else:
            query = IntervalBaseRate.objects.filter(
                setting=attrs["setting"], dates__overlap=attrs["dates"]
            )
        if query.exists():
            raise serializers.ValidationError(
                "Date range overlaps with existing interval base rate"
            )
        return attrs


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
    interval_base_rates = IntervalBaseRateSerializer(
        required=False, read_only=True, many=True
    )
    room_types = serializers.SerializerMethodField()

    class Meta:
        model = DynamicPricingSetting
        exclude = ("id", "hotel")

    def get_room_types(self, obj):
        queryset = RoomType.objects.filter(hotel=obj.hotel).prefetch_related(
            "rate_plans"
        )
        return RMSRoomTypeSerializer(queryset, many=True).data
