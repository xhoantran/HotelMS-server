from rest_framework import generics, mixins, viewsets

from backend.users.permissions import IsAdmin

from .models import (
    DynamicPricingSetting,
    IntervalBaseRate,
    OccupancyBasedTriggerRule,
    RatePlanPercentageFactor,
    TimeBasedTriggerRule,
)
from .serializers import (
    DynamicPricingSettingSerializer,
    IntervalBaseRateSerializer,
    OccupancyBasedTriggerRuleSerializer,
    RatePlanPercentageFactorWriteOnlySerializer,
    TimeBasedTriggerRuleSerializer,
)


class RatePlanPercentageFactorUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = RatePlanPercentageFactor.objects.all()
    serializer_class = RatePlanPercentageFactorWriteOnlySerializer
    lookup_field = "rate_plan__uuid"


class DynamicPricingSettingModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAdmin]
    queryset = DynamicPricingSetting.objects.all()
    serializer_class = DynamicPricingSettingSerializer
    lookup_field = "uuid"


class IntervalBaseRateModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = IntervalBaseRate.objects.all()
    serializer_class = IntervalBaseRateSerializer
    lookup_field = "uuid"


class OccupancyBasedTriggerRuleModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = OccupancyBasedTriggerRule.objects.all()
    serializer_class = OccupancyBasedTriggerRuleSerializer
    lookup_field = "uuid"


class TimeBasedTriggerRuleModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = TimeBasedTriggerRule.objects.all()
    serializer_class = TimeBasedTriggerRuleSerializer
    lookup_field = "uuid"
