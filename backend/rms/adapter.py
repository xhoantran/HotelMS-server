import math
from datetime import date as date_class

from django.core.cache import cache
from django.utils import timezone

from backend.pms.models import Hotel

from .models import (
    DynamicPricingSetting,
    FactorChoices,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    SeasonBasedRule,
    TimeBasedTriggerRule,
    WeekdayBasedRule,
)
from .utils import is_within_period


class DynamicPricingAdapter:
    def __init__(
        self, hotel: Hotel | str | int = None, setting: DynamicPricingSetting = None
    ):
        """
        Initialize the dynamic pricing adapter.

        Args:
            hotel (Hotel): The hotel to initialize the dynamic pricing adapter for.
        """
        if isinstance(setting, DynamicPricingSetting):
            self.setting = setting

        elif (
            isinstance(hotel, Hotel) or isinstance(hotel, str) or isinstance(hotel, int)
        ):
            try:
                self.setting: DynamicPricingSetting = DynamicPricingSetting.objects.get(
                    hotel_group__hotels=hotel
                )
            except DynamicPricingSetting.DoesNotExist:
                raise ValueError("Hotel does not belong to a hotel group")
        else:
            raise ValueError("Must provide either a hotel or a setting")
        self.load_from_cache()

    def load_from_db(self: str):
        """
        Load the dynamic pricing adapter from the database.

        Returns:
            DynamicPricingAdapter: The dynamic pricing adapter.
        """
        self.setting = DynamicPricingSetting.objects.get(pk=self.setting.id)
        self.is_enabled = self.setting.is_enabled
        # Lead days based rules
        self.is_lead_days_based = self.setting.is_lead_days_based
        if self.is_lead_days_based:
            self.lead_days_based_rules = list(
                LeadDaysBasedRule.objects.filter(setting=self.setting)
                .order_by("lead_days")
                .values("multiplier_factor", "increment_factor")
            )
        else:
            self.lead_days_based_rules = []
        # Weekday based rules
        self.is_weekday_based = self.setting.is_weekday_based
        if self.is_weekday_based:
            self.weekday_based_rules = list(
                WeekdayBasedRule.objects.filter(setting=self.setting)
                .order_by("weekday")
                .values("multiplier_factor", "increment_factor")
            )
        else:
            self.weekday_based_rules = []
        # Month based rules
        self.is_month_based = self.setting.is_month_based
        if self.is_month_based:
            self.month_based_rules = list(
                MonthBasedRule.objects.filter(setting=self.setting)
                .order_by("month")
                .values("multiplier_factor", "increment_factor")
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
                    "increment_factor",
                )
            )
            self.season_based_rules = list(
                {
                    "start_date": f"{rule['start_month']}/{rule['start_day']}",
                    "end_date": f"{rule['end_month']}/{rule['end_day']}",
                    "multiplier_factor": rule["multiplier_factor"],
                    "increment_factor": rule["increment_factor"],
                }
                for rule in season_based_rules
            )
        else:
            self.season_based_rules = []
        # Availability based trigger rules
        self.is_occupancy_based = self.setting.is_occupancy_based
        if self.is_occupancy_based:
            # order_by is used to make sure that the rules are applied
            # will be applied in the correct order, max -> min
            self.occupancy_based_trigger_rules = list(
                OccupancyBasedTriggerRule.objects.filter(setting=self.setting)
                .order_by("-min_occupancy")
                .values("min_occupancy", "increment_factor", "multiplier_factor")
            )
        else:
            self.occupancy_based_trigger_rules = []
        # Time based trigger rules
        self.is_time_based = self.setting.is_time_based
        if self.is_time_based:
            self.time_based_trigger_rules = list(
                TimeBasedTriggerRule.objects.filter(
                    setting=self.setting, is_active=True
                ).values(
                    "trigger_time",
                    "multiplier_factor",
                    "increment_factor",
                    "min_occupancy",
                    "max_occupancy",
                    "is_today",
                    "is_tomorrow",
                )
            )
        else:
            self.time_based_trigger_rules = []

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
                "is_occupancy_based": self.setting.is_occupancy_based,
                "occupancy_based_trigger_rules": self.occupancy_based_trigger_rules,
                # Time based trigger rules
                "is_time_based": self.setting.is_time_based,
                "time_based_trigger_rules": self.time_based_trigger_rules,
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
            self.load_from_db()
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
            self.is_occupancy_based = ret["is_occupancy_based"]
            self.occupancy_based_trigger_rules = ret["occupancy_based_trigger_rules"]
            # Time based trigger rules
            self.is_time_based = ret["is_time_based"]
            self.time_based_trigger_rules = ret["time_based_trigger_rules"]

    @staticmethod
    def _factor_to_repr(factor: dict()) -> tuple[float | int, int]:
        """
        Convert a factor to its representation.

        Args:
            factor (dict): The factor to convert.

        Returns:
            tuple[float|int, int]: The converted factor.
        """
        if factor["increment_factor"] == 0:
            return (factor["multiplier_factor"], FactorChoices.MULTIPLIER)
        return (factor["increment_factor"], FactorChoices.INCREMENT)

    def get_lead_days_based_factor(self, date: timezone.datetime.date) -> float:
        """
        Get the lead time based multiplier factor for a given room type and date.

        Args:
            room_type (RoomType): The room type to get the lead time based multiplier factor for.
            date (date): The date to get the lead time based multiplier factor for.

        Returns:
            float: The lead time based multiplier factor for the given room type and date.
        """
        if not self.is_lead_days_based:
            return (1, FactorChoices.MULTIPLIER)
        lead_days = (date - timezone.localtime().date()).days
        if lead_days < 0:
            raise ValueError("Lead time must be positive.")
        if lead_days >= len(self.lead_days_based_rules):
            return self._factor_to_repr(self.lead_days_based_rules[-1])
        return self._factor_to_repr(self.lead_days_based_rules[lead_days])

    def get_weekday_based_factor(self, date: timezone.datetime.date) -> float:
        """
        Get the weekday based multiplier factor for a given date.

        Args:
            date (date): The date to get the weekday based multiplier factor for.

        Returns:
            float: The weekday based multiplier factor for the given date.
        """
        if not self.is_weekday_based:
            return (1, FactorChoices.MULTIPLIER)
        return self._factor_to_repr(self.weekday_based_rules[date.weekday()])

    def get_month_based_factor(self, date: timezone.datetime.date) -> float:
        """
        Get the month based multiplier factor for a given date.

        Args:
            date (date): The date to get the month based multiplier factor for.

        Returns:
            float: The month based multiplier factor for the given date.
        """
        if not self.is_month_based:
            return (1, FactorChoices.MULTIPLIER)
        return self._factor_to_repr(self.month_based_rules[date.month - 1])

    def get_season_based_factor(self, date: timezone.datetime.date) -> float:
        """
        Get the season based multiplier factor for a given date.

        Args:
            date (date): The date to get the season based multiplier factor for.

        Returns:
            float: The season based multiplier factor for the given date.
        """
        if not self.is_season_based:
            return (1, FactorChoices.MULTIPLIER)
        for rule in self.season_based_rules:
            if is_within_period(rule["start_date"], rule["end_date"], date):
                return self._factor_to_repr(rule)
        return (1, FactorChoices.MULTIPLIER)

    def get_occupancy_based_factor(self, occupancy: int) -> tuple[int | float, int]:
        """
        Get the occupancy based multiplier factor for a given occupancy.

        Args:
            occupancy (int): The occupancy to get the occupancy based multiplier factor for.
            rate (int): The rate to get the occupancy based multiplier factor for.

        Returns:
            int | float: The occupancy based increment factor or multiplier factor for the given occupancy.
            int: The occupancy based increment factor or multiplier factor for the given occupancy.
        """
        for i in range(len(self.occupancy_based_trigger_rules)):
            if occupancy >= self.occupancy_based_trigger_rules[i]["min_occupancy"]:
                return self._factor_to_repr(self.occupancy_based_trigger_rules[i])
        return (1, FactorChoices.MULTIPLIER)

    def get_time_based_factor(self, time: timezone.datetime.time, occupancy: int):
        """
        Get the time based multiplier factor for a given time.

        Args:
            time (time): The time to get the time based multiplier factor for.

        Returns:
            float: The time based multiplier factor for the given time.
        """
        if not self.is_time_based or time is None:
            return (1, FactorChoices.MULTIPLIER)
        for rule in self.time_based_trigger_rules:
            if (
                rule["trigger_time"] == time
                and occupancy >= rule["min_occupancy"]
                and occupancy <= rule["max_occupancy"]
            ):
                return self._factor_to_repr(rule)
        return (1, FactorChoices.MULTIPLIER)

    @staticmethod
    def _calculate_rate_by_factors(rate: int, factors: list[tuple[int | float, int]]):
        for factor in factors:
            if factor[1] == FactorChoices.INCREMENT:
                rate += factor[0]
            else:
                rate *= factor[0]
        return rate

    def calculate_rate(
        self,
        date: date_class,
        rate: int,
        occupancy: int,
        time: timezone.datetime.time = None,
    ) -> int:
        """
        Calculate the rate for a given date, rate and occupancy.

        Args:
            date (date_class): The date to calculate the multiplier factor for.
            rate (int): The rate to calculate the multiplier factor for.
            occupancy (int): The occupancy to calculate the multiplier factor for.

        Returns:
            int: The calculated rate.
        """
        factors = []
        factors.append(self.get_lead_days_based_factor(date))
        factors.append(self.get_weekday_based_factor(date))
        factors.append(self.get_month_based_factor(date))
        factors.append(self.get_season_based_factor(date))
        factors.append(self.get_occupancy_based_factor(occupancy))
        factors.append(self.get_time_based_factor(time, occupancy))
        return math.ceil(self._calculate_rate_by_factors(rate, factors))
