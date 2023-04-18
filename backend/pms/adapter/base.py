import datetime
import uuid
from typing import Any, Union

from django.db.models import Q

from ..models import Hotel, RatePlan, RatePlanRestrictions, RoomType


class PMSBaseAdapter:
    def __init__(self, hotel: Hotel | uuid.UUID | str):
        self.hotel = self._covert_to_obj(hotel, Hotel)

    def _convert_to_id(
        self,
        obj: Union[Any, uuid.UUID, str, int],
        obj_type: type,
        field_name: str = "id",
    ) -> Union[uuid.UUID, str, int]:
        if isinstance(obj, obj_type):
            return getattr(obj, field_name)
        elif isinstance(obj, uuid.UUID) or isinstance(obj, str) or isinstance(obj, int):
            return obj
        else:
            raise TypeError(f"{obj_type} must be a {obj_type}, UUID, string or integer")

    def _covert_to_obj(
        self,
        obj: Union[Any, uuid.UUID, str, int],
        obj_type: type,
        field_name: str = "id",
    ) -> Union[uuid.UUID, str, int]:
        if isinstance(obj, obj_type):
            return obj
        elif isinstance(obj, uuid.UUID) or isinstance(obj, str) or isinstance(obj, int):
            return obj_type.objects.get(**{field_name: obj})
        else:
            raise TypeError(f"{obj_type} must be a {obj_type}, UUID, string or integer")

    def get_room_types(self, *args, **kwargs):
        raise NotImplementedError

    def get_rate_plans(self, *args, **kwargs):
        raise NotImplementedError

    def get_room_type_rate_plan_restrictions(self, *args, **kwargs):
        raise NotImplementedError


class DefaultPMSAdapter(PMSBaseAdapter):
    def get_room_types(self, *args, **kwargs):
        return self.hotel.room_types.all()

    def get_rate_plans(
        self,
        room_type: RoomType | uuid.UUID | str = None,
        *args,
        **kwargs,
    ):
        query = Q(room_type__hotel=self.hotel)
        if room_type:
            # Validate room type
            room_type = self._convert_to_id(room_type, RoomType)
            query &= Q(room_type_id=room_type)

        return RatePlan.objects.filter(query)

    def get_room_type_rate_plan_restrictions(
        self,
        room_type: RoomType | uuid.UUID | str = None,
        date: datetime.date | str = None,
        date_from: datetime.date | str = None,
        date_to: datetime.date | str = None,
        *args,
        **kwargs,
    ):
        query = Q(rate_plan__room_type__hotel=self.hotel)
        if room_type:
            # Validate room type
            room_type = self._convert_to_id(room_type, RoomType)
            query &= Q(rate_plan__room_type_id=room_type)

        if date:
            query &= Q(date=date)
        elif date_from and date_to:
            query &= Q(date__gte=date_from) & Q(date__lte=date_to)
        else:
            raise ValueError("Must specify date or date_from and date_to")

        return RatePlanRestrictions.objects.filter(query)
