from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import (
    DynamicPricingSettingModelViewSet,
    OccupancyBasedTriggerRuleModelViewSet,
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
