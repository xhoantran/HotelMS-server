import datetime
from collections.abc import Iterator

import requests
from django.conf import settings

CHANNEX_BASE_URL = getattr(
    settings,
    "CHANNEX_BASE_URL",
    "https://staging.channex.io/api/v1/",
)


class ChannexClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = CHANNEX_BASE_URL

    def _get(self, url, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {
                "Content-Type": "application/json",
            }
        headers["user-api-key"] = self.api_key
        return requests.get(
            self.base_url + url,
            params=params,
            headers=headers,
        )

    def _post(self, url, data=None, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {
                "Content-Type": "application/json",
            }
        headers["user-api-key"] = self.api_key
        return requests.post(
            self.base_url + url,
            params=params,
            headers=headers,
            json=data,
        )

    def _delete(self, url, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {
                "Content-Type": "application/json",
            }
        headers["user-api-key"] = self.api_key
        return requests.delete(
            self.base_url + url,
            params=params,
            headers=headers,
        )

    def _date_to_str(self, date: datetime.date | str):
        if isinstance(date, str):
            return date
        return date.strftime("%Y-%m-%d")

    def get_webhooks(self):
        return self._get("webhooks")

    def create_webhook(self, data: dict):
        data = {
            "webhook": {
                "property_id": data.get("property_id"),
                "callback_url": data.get("callback_url"),
                "event_mask": data.get("event_mask"),
                "request_params": data.get("request_params", {}),
                "headers": data.get("headers", {}),
                "is_active": data.get("is_active", True),
                "send_data": data.get("send_data", True),
            },
        }
        return self._post("webhooks", data=data)

    def get_webhook(self, webhook_id):
        return self._get(f"webhooks/{webhook_id}")

    def delete_webhook(self, webhook_id):
        return self._delete(f"webhooks/{webhook_id}")

    def get_properties(self, options: bool = True):
        if options:
            return self._get("properties/options")
        return self._get("properties")

    def get_property(self, property_id):
        return self._get(f"properties/{property_id}")

    def get_room_types(self, property_id, options: bool = True):
        if options:
            return self._get(f"room_types/options?filter[property_id]={property_id}")
        return self._get(f"room_types/?filter[property_id]={property_id}")

    def get_room_type(self, room_type_id):
        return self._get(f"room_types/{room_type_id}")

    def get_rate_plans(self, property_id, room_type_id=None, options: bool = True):
        if options:
            return self._get(
                f"rate_plans/options?filter[property_id]={property_id}&filter[room_type_id]={room_type_id}"
            )
        return self._get(
            f"rate_plans/?filter[property_id]={property_id}&filter[room_type_id]={room_type_id}"
        )

    def get_rate_plan(self, rate_plan_id):
        return self._get(f"rate_plans/{rate_plan_id}")

    def get_room_type_rate_plan_restrictions(
        self,
        property_id: str,
        room_type_id: str = None,
        date: datetime.date | str = None,
        date_from: datetime.date | str = None,
        date_to: datetime.date | str = None,
        restrictions: list[str] = ["rate"],
    ):
        params = {}
        params["filter[property_id]"] = property_id
        if room_type_id:
            params["filter[room_type_id]"] = room_type_id
        if restrictions:
            params["filter[restriction]"] = ",".join(restrictions)
        if date:
            params["filter[date]"] = self._date_to_str(date)
        elif date_from and date_to:
            params["filter[date][gte]"] = self._date_to_str(date_from)
            params["filter[date][lte]"] = self._date_to_str(date_to)
        else:
            raise ValueError("Must provide date or date_from and date_to")
        return self._get("restrictions/", params=params)

    def update_room_type_rate_plan_restrictions(self, data: Iterator[dict]):
        return self._post("restrictions", data={"values": data})
