import uuid

from django.core.cache import cache
from django.utils import timezone

from backend.pms.models import Hotel, RoomType

from .models import TimeBasedTriggerRule  # noqa F401
from .models import (
    AvailabilityBasedTriggerRule,
    DynamicPricingSetting,
    LeadDaysBasedRule,
    MonthBasedRule,
    SeasonBasedRule,
    WeekdayBasedRule,
    HotelGroup,
)
from .utils import is_within_period


class DynamicPricingAdapter:
    def __init__(self, hotel: Hotel | str | int):
        """
        Initialize the dynamic pricing adapter.

        Args:
            hotel (Hotel): The hotel to initialize the dynamic pricing adapter for.
        """
        # if isinstance(hotel, Hotel):
        #     self.hotel = hotel
        # elif isinstance(hotel, str):

        self.load_from_cache()

    def load_from_db(self: str):
        """
        Load the dynamic pricing adapter from the database.

        Returns:
            DynamicPricingAdapter: The dynamic pricing adapter.
        """
        self.is_enabled = self.setting.is_enabled
        # Lead days based rules
        self.is_lead_days_based = self.setting.is_lead_days_based
        if self.is_lead_days_based:
            self.lead_days_based_rules = list(
                LeadDaysBasedRule.objects.filter(setting=self.setting)
                .order_by("lead_days")
                .values_list("multiplier_factor", flat=True)
            )
        else:
            self.lead_days_based_rules = []
        # Weekday based rules
        self.is_weekday_based = self.setting.is_weekday_based
        if self.is_weekday_based:
            self.weekday_based_rules = list(
                WeekdayBasedRule.objects.filter(setting=self.setting)
                .order_by("weekday")
                .values_list("multiplier_factor", flat=True)
            )
        else:
            self.weekday_based_rules = []
        # Month based rules
        self.is_month_based = self.setting.is_month_based
        if self.is_month_based:
            self.month_based_rules = list(
                MonthBasedRule.objects.filter(setting=self.setting)
                .order_by("month")
                .values_list("multiplier_factor", flat=True)
            )
        else:
            self.month_based_rules = []
        # Season based rules
        self.is_season_based = self.setting.is_season_based
        if self.is_season_based:
            season_based_rules = (
                SeasonBasedRule.objects.filter(setting=self.setting)
                .order_by("name")
                .values(
                    "start_month",
                    "start_day",
                    "end_month",
                    "end_day",
                    "multiplier_factor",
                )
            )
            self.season_based_rules = list(
                {
                    "start_date": f"{rule['start_month']}/{rule['start_day']}",
                    "end_date": f"{rule['end_month']}/{rule['end_day']}",
                    "multiplier_factor": rule["multiplier_factor"],
                }
                for rule in season_based_rules
            )
        else:
            self.season_based_rules = []
        # Availability based trigger rules
        self.is_availability_based = self.setting.is_availability_based
        if self.is_availability_based:
            self.availability_based_trigger_rules = list(
                AvailabilityBasedTriggerRule.objects.filter(
                    setting=self.setting
                ).values("max_availability", "multiplier_factor")
            )
        else:
            self.availability_based_trigger_rules = []
        # Room type base rates
        self.room_type_base_rates = self.ari_adapter.get_room_type_base_rates(self)
        return self

    def get_cache_key(self: str) -> str:
        """
        Get the cache key for the dynamic pricing adapter.

        Returns:
            str: The cache key for the dynamic pricing adapter.
        """
        return f"rms:adapter:{self.setting.id}"

    def invalidate_cache(self: str):
        """
        Invalidate the cache for the dynamic pricing adapter.
        """
        cache.delete(self.get_cache_key())

    def save_to_cache(self):
        """
        Save the dynamic pricing adapter to the cache.
        """
        cache.set(
            self.get_cache_key(),
            {
                "is_enabled": self.setting.is_enabled,
                # Lead days based rules
                "is_lead_days_based": self.setting.is_lead_days_based,
                "lead_days_based_rules": self.lead_days_based_rules,
                # Weekday based rules
                "is_weekday_based": self.setting.is_weekday_based,
                "weekday_based_rules": self.weekday_based_rules,
                # Month based rules
                "is_month_based": self.setting.is_month_based,
                "month_based_rules": self.month_based_rules,
                # Season based rules
                "is_season_based": self.setting.is_season_based,
                "season_based_rules": self.season_based_rules,
                # Availability based trigger rules
                "is_availability_based": self.setting.is_availability_based,
                "availability_based_trigger_rules": self.availability_based_trigger_rules,
                # Room type base rates
                "room_type_base_rates": self.room_type_base_rates,
            },
            timeout=None if self.setting.is_lead_days_based else None,
        )

    def load_from_cache(self):
        """
        Load the dynamic pricing adapter from the cache.

        Returns:
            DynamicPricingAdapter: The dynamic pricing adapter.
        """

        ret = cache.get(self.get_cache_key())
        if ret is None:
            ret = self.load_from_db()
            self.save_to_cache()
        else:
            self.is_enabled = ret["is_enabled"]
            # Lead days based rules
            self.is_lead_days_based = ret["is_lead_days_based"]
            self.lead_days_based_rules = ret["lead_days_based_rules"]
            # Weekday based rules
            self.is_weekday_based = ret["is_weekday_based"]
            self.weekday_based_rules = ret["weekday_based_rules"]
            # Month based rules
            self.is_month_based = ret["is_month_based"]
            self.month_based_rules = ret["month_based_rules"]
            # Season based rules
            self.is_season_based = ret["is_season_based"]
            self.season_based_rules = ret["season_based_rules"]
            # Availability based trigger rules
            self.is_availability_based = ret["is_availability_based"]
            self.availability_based_trigger_rules = ret[
                "availability_based_trigger_rules"
            ]
            # Room type base rates
            self.room_type_base_rates = ret["room_type_base_rates"]

    def _get_availability_based_factor(self, availability):
        """
        Get the availability based multiplier factor for a given availability.

        Args:
            availability (int): The availability to get the availability based multiplier factor for.

        Returns:
            float: The availability based multiplier factor for the given availability.
        """
        for i in range(len(self.availability_based_trigger_rules)):
            if (
                availability
                <= self.availability_based_trigger_rules[i]["max_availability"]
            ):
                return self.availability_based_trigger_rules[i]["multiplier_factor"]
        return 1

    def get_room_type_availability_based_factor(
        self, room_type: RoomType | str | uuid.UUID, date
    ):
        """
        Get the availability based multiplier factor for a given room type and date.

        Args:
            room_type (RoomType | str | uuid.UUID): The room type to get the availability based multiplier factor for.
            date (date): The date to get the availability based multiplier factor for.

        Returns:
            float: The availability based multiplier factor for the given room type and date.
        """
        if not self.is_availability_based:
            return 1
        availability = self.ari_adapter.get_number_of_available_rooms(room_type, date)
        return self._get_availability_based_factor(availability)

    def get_lead_days_based_factor(self, date):
        """
        Get the lead time based multiplier factor for a given room type and date.

        Args:
            room_type (RoomType): The room type to get the lead time based multiplier factor for.
            date (date): The date to get the lead time based multiplier factor for.

        Returns:
            float: The lead time based multiplier factor for the given room type and date.
        """
        if not self.is_lead_days_based:
            return 1
        lead_days = (date - timezone.now().date()).days
        if lead_days < 0:
            raise ValueError("Lead time must be positive.")
        if lead_days >= len(self.lead_days_based_rules):
            return self.lead_days_based_rules[-1]
        return self.lead_days_based_rules[lead_days]

    def get_weekday_based_factor(self, date):
        """
        Get the weekday based multiplier factor for a given date.

        Args:
            date (date): The date to get the weekday based multiplier factor for.

        Returns:
            float: The weekday based multiplier factor for the given date.
        """
        if not self.is_weekday_based:
            return 1
        return self.weekday_based_rules[date.weekday()]

    def get_month_based_factor(self, date):
        """
        Get the month based multiplier factor for a given date.

        Args:
            date (date): The date to get the month based multiplier factor for.

        Returns:
            float: The month based multiplier factor for the given date.
        """
        if not self.is_month_based:
            return 1
        return self.month_based_rules[date.month - 1]

    def get_season_based_factor(self, date):
        """
        Get the season based multiplier factor for a given date.

        Args:
            date (date): The date to get the season based multiplier factor for.

        Returns:
            float: The season based multiplier factor for the given date.
        """
        if not self.is_season_based:
            return 1
        ret = 1
        for rule in self.season_based_rules:
            if is_within_period(rule["start_date"], rule["end_date"], date):
                ret = ret * rule["multiplier_factor"]
        return ret

    # This method is used for our own pms only.
    def get_room_type_base_rate(self, room_type):
        """
        Get the base rate for a given room type.

        Args:
            room_type (RoomType or uuid): The room type to get the base rate for.

        Returns:
            float: The base rate for the given room type.
        """
        if isinstance(room_type, RoomType):
            room_type = room_type.id
        return next(
            item["base_rate"]
            for item in self.room_type_base_rates
            if item["id"] == room_type
        )

    # This method is used for our own pms only.
    def calculate_rate(self, room_type, date):
        """
        Calculate the rate of a room for a given date.

        Args:
            room_type (RoomType): The room type to calculate the rate for.
            date (date): The date to calculate the rate for.

        Returns:
            float: The rate of the room for the given date.
        """
        base_rate = self.get_room_type_base_rate(room_type)
        lead_days_based_factor = self.get_lead_days_based_factor(date)
        week_day_based_factor = self.get_weekday_based_factor(date)
        month_based_factor = self.get_month_based_factor(date)
        season_based_factor = self.get_season_based_factor(date)
        availability_based_factor = self.get_room_type_availability_based_factor(
            room_type, date
        )
        val = (
            base_rate
            * lead_days_based_factor
            * week_day_based_factor
            * month_based_factor
            * season_based_factor
            * availability_based_factor
        )
        return val

    def calculate_rate_on_availability_trigger(
        self, room_type, date, availability
    ) -> tuple[list, bool]:
        """
        Calculate the rate of a room for a given date when the availability trigger is hit.

        Args:
            room_type (RoomType): The room type to calculate the rate for.
            date (date): The date to calculate the rate for.

        Returns:
            list[{"rate_plan_id": str, "rate": int}]: The rate plans to update.
            bool: Whether the rate plans need to be updated.
        """
        # TODO: Should check if the availability is changed or not.
        previous_factor = self._get_availability_based_factor(availability + 1)
        current_factor = self._get_availability_based_factor(availability)
        if previous_factor == current_factor:
            return [], False

        # If the factor has changed, we need to update the rate plans.
        current_rate_plans = self.ari_adapter.get_room_type_rate_plans_on_date(
            room_type, date
        )
        new_rate_plans = []
        for rate_plan in current_rate_plans:
            new_rate = int(
                float(rate_plan.get("rate"))
                * float(current_factor)
                / float(previous_factor)
                * 100
            )
            new_rate_plans.append(
                {"rate_plan_id": rate_plan.get("rate_plan_id"), "rate": new_rate}
            )
        return new_rate_plans, True