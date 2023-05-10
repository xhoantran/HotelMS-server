from django_filters import rest_framework as filters

from backend.pms.models import RoomType


class RoomTypeFilter(filters.FilterSet):
    hotel = filters.CharFilter(field_name="hotel__uuid")

    class Meta:
        model = RoomType
        fields = ["hotel"]
