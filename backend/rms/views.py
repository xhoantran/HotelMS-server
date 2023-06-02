from rest_framework import generics, mixins, response, status, viewsets

from backend.users.permissions import IsAdmin

from .models import (
    DynamicPricingSetting,
    IntervalBaseRate,
    OccupancyBasedTriggerRule,
    RMSRatePlan,
    TimeBasedTriggerRule,
)
from .serializers import (
    DynamicPricingSettingSerializer,
    IntervalBaseRateSerializer,
    OccupancyBasedTriggerRuleSerializer,
    RatePlanPercentageFactorWriteOnlySerializer,
    TimeBasedTriggerRuleSerializer,
)
from .tasks import recalculate_all_rate


class RatePlanPercentageFactorUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = RMSRatePlan.objects.all()
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


class RecalculateAllRateAPIView(generics.GenericAPIView):
    permission_classes = [IsAdmin]
    queryset = DynamicPricingSetting.objects.all()
    lookup_field = "uuid"

    def post(self, request, *args, **kwargs):
        dynamic_pricing_setting = self.get_object()
        recalculate_all_rate.delay(dynamic_pricing_setting.id)
        return response.Response(status=status.HTTP_200_OK)
