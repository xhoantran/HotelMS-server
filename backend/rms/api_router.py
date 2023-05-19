from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import (
    DynamicPricingSettingModelViewSet,
    IntervalBaseRateModelViewSet,
    OccupancyBasedTriggerRuleModelViewSet,
    RatePlanPercentageFactorUpdateAPIView,
    RecalculateAllRateAPIView,
    TimeBasedTriggerRuleModelViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()


router.register(
    "dynamic-pricing-setting",
    DynamicPricingSettingModelViewSet,
    basename="dynamic-pricing-setting",
)
router.register(
    "interval-base-rate",
    IntervalBaseRateModelViewSet,
    basename="interval-base-rate",
)
router.register(
    "occupancy-based-trigger-rule",
    OccupancyBasedTriggerRuleModelViewSet,
    basename="occupancy-based-trigger-rule",
)
router.register(
    "time-based-trigger-rule",
    TimeBasedTriggerRuleModelViewSet,
    basename="time-based-trigger-rule",
)


app_name = "rms"
urlpatterns = router.urls
urlpatterns += [
    path(
        "rate-plan-percentage-factor/<uuid:rate_plan__uuid>/",
        RatePlanPercentageFactorUpdateAPIView.as_view(),
        name="rate-plan-percentage-factor",
    ),
    path(
        "recalculate-all-rate/<uuid:uuid>/",
        RecalculateAllRateAPIView.as_view(),
        name="recalculate-all-rate",
    ),
]
