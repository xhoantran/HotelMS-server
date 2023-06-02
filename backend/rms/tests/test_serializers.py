from ..models import RMSRatePlan
from ..serializers import RMSRatePlanSerializer


def test_get_percentage_factor(db, rate_plan_factory):
    rate_plan = rate_plan_factory()  # default percentage_factor 0
    RMSRatePlan.objects.filter(rate_plan=rate_plan).update(percentage_factor=50)
    rate_plan.refresh_from_db()
    result = RMSRatePlanSerializer().get_percentage_factor(rate_plan)
    expected_result = 50
    assert result == expected_result
