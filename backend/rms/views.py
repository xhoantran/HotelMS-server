from rest_framework import mixins, viewsets

from backend.users.permissions import IsAdmin

from .models import (
    DynamicPricingSetting,
    OccupancyBasedTriggerRule,
    TimeBasedTriggerRule,
)
from .serializers import (
    DynamicPricingSettingSerializer,
    OccupancyBasedTriggerRuleSerializer,
    TimeBasedTriggerRuleSerializer,
)


class DynamicPricingSettingModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAdmin]
    queryset = DynamicPricingSetting.objects.all()
    serializer_class = DynamicPricingSettingSerializer
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
