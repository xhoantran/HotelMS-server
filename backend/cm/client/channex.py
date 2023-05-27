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

    def list_webhooks(
        self,
        property_id: str,
        params: dict = {},
        page: int = 1,
        limit: int = 100,
    ):
        params = {
            "filter[property_id]": property_id,
            "pagination[page]": page,
            "pagination[limit]": limit,
            **params,
        }
        response = self._get("webhooks", params=params)
        if response.status_code != 200:
            raise ChannexClientAPIError("Failed to list webhooks", response.status_code)

        return response.json().get("data")

    def list_all_webhooks(
        self,
        property_id: str,
        params: dict = {},
        limit: int = 100,
    ):
        def _list_all_webhooks():
            page = 1
            while True:
                data = self.list_webhooks(
                    property_id=property_id,
                    params=params,
                    page=page,
                    limit=limit,
                )
                yield from data
                if len(data) < limit:
                    break
                page += 1

        return list(_list_all_webhooks())

    def find_webhook_id(
        self,
        property_id: str,
        callback_url: str,
        event_mask: str,
    ):
        webhooks = self.list_all_webhooks(
            property_id=property_id,
            params={
                "filter[callback_url]": callback_url,
            },
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

    def create_webhook(
        self,
        property_id: str,
        callback_url: str,
        event_mask: str,
        request_params: dict = {},
        headers: dict = {},
        is_active: bool = True,
        send_data: bool = True,
    ):
        response = self._post(
            "webhooks",
            data={
                "webhook": {
                    "property_id": property_id,
                    "callback_url": callback_url,
                    "event_mask": event_mask,
                    "request_params": request_params,
                    "headers": headers,
                    "is_active": is_active,
                    "send_data": send_data,
                }
            },
        )
        if response.status_code != 201:
            raise ChannexClientAPIError(
                "Failed to create webhook", response.status_code
            )
        return response.json().get("data")

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
        response = self._post(
            "webhooks",
            data={
                "webhook": {
                    "property_id": property_id,
                    "callback_url": callback_url,
                    "event_mask": event_mask,
                    "request_params": request_params,
                    "headers": headers,
                    "is_active": is_active,
                    "send_data": send_data,
                }
            },
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
                webhook_id = self.find_webhook_id(
                    property_id,
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

    def get_webhook(self, webhook_id):
        return self._get(f"webhooks/{webhook_id}")

    # TODO: Add check response
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

    # TODO: Add check response
    def delete_webhook(self, webhook_id):
        return self._delete(f"webhooks/{webhook_id}")

    def list_properties(self, options: bool = True):
        if options:
            response = self._get("properties/options")
        else:
            response = self._get("properties")
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    def get_property(self, property_id):
        response = self._get(f"properties/{property_id}")
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    def list_room_types(self, property_id, options: bool = True):
        if options:
            response = self._get(
                f"room_types/options?filter[property_id]={property_id}"
            )
        else:
            response = self._get(f"room_types/?filter[property_id]={property_id}")
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    def get_room_type(self, room_type_id):
        response = self._get(f"room_types/{room_type_id}")
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    def list_rate_plans(self, property_id, room_type_id=None, options: bool = True):
        params = {}
        params["filter[property_id]"] = property_id
        if room_type_id:
            params["filter[room_type_id]"] = room_type_id

        if options:
            response = self._get("rate_plans/options", params=params)
        else:
            response = self._get("rate_plans/", params=params)

        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)

        return response.json().get("data")

    def get_rate_plan(self, rate_plan_id):
        response = self._get(f"rate_plans/{rate_plan_id}")
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    def update_rate_plan_restrictions(self, data: Iterator[dict]):
        response = self._post("restrictions", data={"values": data})
        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)
        return response.json().get("data")

    def list_bookings(
        self,
        property_id,
        params: dict = {},
        page: int = 1,
        limit: int = 100,
    ):
        params = {
            "filter[property_id]": property_id,
            "pagination[page]": page,
            "pagination[limit]": limit,
            **params,
        }
        response = self._get("bookings", params=params)

        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)

        return response.json().get("data")

    def list_booking_revisions_feed(
        self, property_id, params: dict = {}, page: int = 1, limit: int = 100
    ):
        params = {
            "filter[property_id]": property_id,
            "order[inserted_at]": "desc",
            "pagination[page]": page,
            "pagination[limit]": limit,
            **params,
        }
        response = self._get("booking_revisions/feed", params=params)

        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)

        return response.json().get("data")

    def get_booking_revision(self, booking_revision_id):
        response = self._get(f"booking_revisions/{booking_revision_id}")

        if response.status_code != 200:
            raise ChannexClientAPIError(response.json(), response.status_code)

        return response.json().get("data")
