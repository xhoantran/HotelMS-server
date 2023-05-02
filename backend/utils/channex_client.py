import datetime
from collections.abc import Iterator

import requests
from django.conf import settings

CHANNEX_BASE_URL = getattr(
    settings,
    "CHANNEX_BASE_URL",
    "https://staging.channex.io/api/v1/",
)


class ChannexClientAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


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

    def _put(self, url, data=None, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {
                "Content-Type": "application/json",
            }
        headers["user-api-key"] = self.api_key
        return requests.put(
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

    def get_webhooks(self, params=None):
        return self._get("webhooks", params=params)

    def _find_webhooks_id(
        self,
        callback_url: str,
        event_mask: str,
    ):
        webhooks = (
            self.get_webhooks(
                params={
                    "filter[callback_url]": callback_url,
                    "filter[event_mask]": event_mask,
                }
            )
            .json()
            .get("data", [])
        )
        try:
            for webhook in webhooks:
                if (
                    webhook["attributes"]["callback_url"] == callback_url
                    and webhook["attributes"]["event_mask"] == event_mask
                ):
                    return webhook["id"]
        except KeyError:
            ChannexClientAPIError("Failed to parse webhooks list api response")
        return None

    def _create_webhook(
        self,
        property_id: str,
        callback_url: str,
        event_mask: str,
        request_params: dict = {},
        headers: dict = {},
        is_active: bool = True,
        send_data: bool = True,
    ):
        data = {
            "webhook": {
                "property_id": property_id,
                "callback_url": callback_url,
                "event_mask": event_mask,
                "request_params": request_params,
                "headers": headers,
                "is_active": is_active,
                "send_data": send_data,
            },
        }
        return self._post("webhooks", data=data)

    def update_or_create_webhook(
        self,
        property_id: str,
        callback_url: str,
        event_mask: str,
        request_params: dict = {},
        headers: dict = {},
        is_active: bool = True,
        send_data: bool = True,
    ):
        response = self._create_webhook(
            property_id,
            callback_url,
            event_mask,
            request_params,
            headers,
            is_active,
            send_data,
        )
        if response.status_code == 201:
            return response.json().get("data")

        try:
            error_message = response.json()["errors"]["details"]["property_id"][0]
            if (
                response.status_code == 422
                and error_message
                == "only one webhook for callback url and event mask allowed"
            ):
                webhook_id = self._find_webhooks_id(
                    callback_url,
                    event_mask,
                )
                if webhook_id:
                    response = self._update_webhook(
                        webhook_id,
                        property_id,
                        callback_url,
                        event_mask,
                        request_params,
                        headers,
                        is_active,
                        send_data,
                    )
                    if response.status_code == 200:
                        return
                    raise ChannexClientAPIError(
                        "Failed to update webhook", response.status_code
                    )
                raise ChannexClientAPIError(
                    "Webhook already exists but cannot be found"
                )
        except KeyError:
            error_message = "Unknown error"
        raise ChannexClientAPIError(error_message, response.status_code)

    # TODO: Deprecated
    def get_webhook(self, webhook_id):
        return self._get(f"webhooks/{webhook_id}")

    def _update_webhook(
        self,
        webhook_id: str,
        property_id: str,
        callback_url: str,
        event_mask: str,
        request_params: dict = {},
        headers: dict = {},
        is_active: bool = True,
        send_data: bool = True,
    ):
        return self._put(
            f"webhooks/{webhook_id}",
            data={
                "webhook": {
                    "property_id": property_id,
                    "callback_url": callback_url,
                    "event_mask": event_mask,
                    "request_params": request_params,
                    "headers": headers,
                    "is_active": is_active,
                    "send_data": send_data,
                },
            },
        )

    # TODO: Deprecated
    def delete_webhook(self, webhook_id):
        return self._delete(f"webhooks/{webhook_id}")

    # TODO: Deprecated
    def get_properties(self, options: bool = True):
        if options:
            return self._get("properties/options")
        return self._get("properties")

    # TODO: Deprecated
    def get_property(self, property_id):
        return self._get(f"properties/{property_id}")

    def _get_room_types(self, property_id, options: bool = True):
        if options:
            return self._get(f"room_types/options?filter[property_id]={property_id}")
        return self._get(f"room_types/?filter[property_id]={property_id}")

    def get_room_types(self, property_id, options: bool = True):
        response = self._get_room_types(property_id, options)
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    # TODO: Deprecated
    def get_room_type(self, room_type_id):
        return self._get(f"room_types/{room_type_id}")

    def _get_rate_plans(self, property_id, room_type_id=None, options: bool = True):
        params = {}
        params["filter[property_id]"] = property_id
        if room_type_id:
            params["filter[room_type_id]"] = room_type_id

        if options:
            return self._get("rate_plans/options", params=params)
        return self._get("rate_plans/", params=params)

    def get_rate_plans(self, property_id, room_type_id=None, options: bool = True):
        response = self._get_rate_plans(property_id, room_type_id, options)
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    # TODO: Deprecated
    def get_rate_plan(self, rate_plan_id):
        return self._get(f"rate_plans/{rate_plan_id}")

    # TODO: Deprecated
    def get_room_type_rate_plan_restrictions(
        self,
        property_pms_id: str,
        date: datetime.date | str = None,
        date_from: datetime.date | str = None,
        date_to: datetime.date | str = None,
        restrictions: list[str] = ["rate", "availability"],
    ):
        params = {}
        params["filter[property_id]"] = property_pms_id
        if restrictions:
            params["filter[restrictions]"] = ",".join(restrictions)
        if date:
            params["filter[date]"] = self._date_to_str(date)
        elif date_from and date_to:
            params["filter[date][gte]"] = self._date_to_str(date_from)
            params["filter[date][lte]"] = self._date_to_str(date_to)
        else:
            raise ValueError("Must provide date or date_from and date_to")
        return self._get("restrictions/", params=params)

    # TODO: Deprecated
    def update_room_type_rate_plan_restrictions(self, data: Iterator[dict]):
        return self._post("restrictions", data={"values": data})
