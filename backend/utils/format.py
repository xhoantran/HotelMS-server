import uuid
from typing import Any, Union


def convert_to_id(
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


def convert_to_obj(
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
