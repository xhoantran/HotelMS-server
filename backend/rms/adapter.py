import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.core.exceptions import ValidationError

from backend.pms.models import Hotel

from .models import (
    DynamicPricingSetting,
    FactorChoices,
    IntervalBaseRate,
    LeadDaysBasedRule,
    MonthBasedRule,
    OccupancyBasedTriggerRule,
    RatePlanPercentageFactor,
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
        elif isinstance(hotel, (Hotel, str, int)):
            self.setting: DynamicPricingSetting = DynamicPricingSetting.objects.get(
                hotel=hotel
            )
        else:
            raise ValidationError("Must provide either a hotel or a setting")
        self.load_from_cache()

    def load_from_db(self):
        """
        Load the dynamic pricing adapter from the database.

        Returns:
            DynamicPricingAdapter: The dynamic pricing adapter.
        """
        self.setting = DynamicPricingSetting.objects.get(pk=self.setting.id)
        self.timezone = self.setting.hotel.timezone
        self.is_enabled = self.setting.is_enabled

        # Base rate
        self.default_base_rate = self.setting.default_base_rate
        self.interval_base_rates = list(
            IntervalBaseRate.objects.filter(setting=self.setting)
            .order_by("dates")
            .values("dates", "base_rate")
        )
        # Rate plan percentage factors
        rate_plan_percentage_factors = list(
            RatePlanPercentageFactor.objects.filter(
                rate_plan__room_type__hotel=self.setting.hotel
            ).values("rate_plan__id", "percentage_factor")
        )
        self.rate_plan_percentage_factors = {
            factor["rate_plan__id"]: factor["percentage_factor"]
            for factor in rate_plan_percentage_factors
        }
        # Lead days based rules
        self.is_lead_days_based = self.setting.is_lead_days_based
        if self.is_lead_days_based:
            self.lead_days_based_rules = list(
                LeadDaysBasedRule.objects.filter(setting=self.setting)
                .order_by("lead_days")
                .values("percentage_factor", "increment_factor")
            )
        else:
            self.lead_days_based_rules = []
        # Weekday based rules
        self.is_weekday_based = self.setting.is_weekday_based
        if self.is_weekday_based:
            self.weekday_based_rules = list(
                WeekdayBasedRule.objects.filter(setting=self.setting)
                .order_by("weekday")
                .values("percentage_factor", "increment_factor")
            )
        else:
            self.weekday_based_rules = []
        # Month based rules
        self.is_month_based = self.setting.is_month_based
        if self.is_month_based:
            self.month_based_rules = list(
                MonthBasedRule.objects.filter(setting=self.setting)
                .order_by("month")
                .values("percentage_factor", "increment_factor")
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
                    "percentage_factor",
                    "increment_factor",
                )
            )
            self.season_based_rules = list(
                {
                    "start_date": f"{rule['start_month']}/{rule['start_day']}",
                    "end_date": f"{rule['end_month']}/{rule['end_day']}",
                    "percentage_factor": rule["percentage_factor"],
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
                .values("min_occupancy", "increment_factor", "percentage_factor")
            )
        else:
            self.occupancy_based_trigger_rules = []
        # Time based trigger rules
        self.is_time_based = self.setting.is_time_based
        if self.is_time_based:
            self.time_based_trigger_rules = list(
                TimeBasedTriggerRule.objects.filter(setting=self.setting)
                .order_by("day_ahead", "-hour", "-min_occupancy")
                .values(
                    "hour",
                    "percentage_factor",
                    "increment_factor",
                    "min_occupancy",
                    "day_ahead",
                )
            )
        else:
            self.time_based_trigger_rules = []

    @staticmethod
    def get_cache_key(setting_id) -> str:
        """
        Get the cache key for the dynamic pricing adapter.

        Returns:
            str: The cache key for the dynamic pricing adapter.
        """
        return f"rms:adapter:{setting_id}"

    @staticmethod
    def invalidate_cache(setting_id):
        """
        Invalidate the cache for the dynamic pricing adapter.
        """
        cache.delete(DynamicPricingAdapter.get_cache_key(setting_id))

    def save_to_cache(self):
        """
        Save the dynamic pricing adapter to the cache.
        """
        cache.set(
            self.get_cache_key(self.setting.id),
            {
                "timezone": self.timezone,
                "is_enabled": self.is_enabled,
                # Base rate
                "default_base_rate": self.default_base_rate,
                "interval_base_rates": self.interval_base_rates,
                # Rate plan percentage factors
                "rate_plan_percentage_factors": self.rate_plan_percentage_factors,
                # Lead days based rules
                "is_lead_days_based": self.is_lead_days_based,
                "lead_days_based_rules": self.lead_days_based_rules,
                # Weekday based rules
                "is_weekday_based": self.is_weekday_based,
                "weekday_based_rules": self.weekday_based_rules,
                # Month based rules
                "is_month_based": self.is_month_based,
                "month_based_rules": self.month_based_rules,
                # Season based rules
                "is_season_based": self.is_season_based,
                "season_based_rules": self.season_based_rules,
                # Availability based trigger rules
                "is_occupancy_based": self.is_occupancy_based,
                "occupancy_based_trigger_rules": self.occupancy_based_trigger_rules,
                # Time based trigger rules
                "is_time_based": self.is_time_based,
                "time_based_trigger_rules": self.time_based_trigger_rules,
            },
            timeout=None,
        )

    def load_from_cache(self):
        """
        Load the dynamic pricing adapter from the cache.

        Returns:
            DynamicPricingAdapter: The dynamic pricing adapter.
        """
        ret = cache.get(self.get_cache_key(self.setting.id))
        if ret is None:
            self.load_from_db()
            self.save_to_cache()
        else:
            self.timezone = ret["timezone"]
            self.is_enabled = ret["is_enabled"]
            # Base rate
            self.default_base_rate = ret["default_base_rate"]
            self.interval_base_rates = ret["interval_base_rates"]
            # Rate plan percentage factors
            self.rate_plan_percentage_factors = ret["rate_plan_percentage_factors"]
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

    def get_base_rate(self, date: date, rate_plan_id: int) -> int:
        # Get the base rate for the given date and rate plan id.
        base_rate = self.default_base_rate
        for interval_base_rate in self.interval_base_rates:
            if interval_base_rate["start"] <= date < interval_base_rate["end"]:
                base_rate = interval_base_rate["base_rate"]
                break
        percentage_factor = self.rate_plan_percentage_factors[rate_plan_id]
        return math.ceil(base_rate * percentage_factor)

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
            return (factor["percentage_factor"], FactorChoices.PERCENTAGE)
        return (factor["increment_factor"], FactorChoices.INCREMENT)

    def get_lead_days_based_factor(
        self, date: date, current_datetime: datetime
    ) -> float:
        """
        Get the lead time based factor for a given room type and date.

        Args:
            date (date): The date to get the lead time based factor for.
            current_datetime (datetime): The current datetime.

        Returns:
            float: The lead time based factor for the given room type and date.
        """
        if not self.is_lead_days_based:
            return (0, FactorChoices.PERCENTAGE)
        lead_days = (date - current_datetime.date()).days
        if lead_days < 0:
            raise ValidationError("Lead time must be positive.")
        if lead_days >= len(self.lead_days_based_rules):
            return self._factor_to_repr(self.lead_days_based_rules[-1])
        return self._factor_to_repr(self.lead_days_based_rules[lead_days])

    def get_weekday_based_factor(self, date: date) -> float:
        """
        Get the weekday based factor for a given date.

        Args:
            date (date): The date to get the weekday based factor for.

        Returns:
            float: The weekday based factor for the given date.
        """
        if not self.is_weekday_based:
            return (0, FactorChoices.PERCENTAGE)
        return self._factor_to_repr(self.weekday_based_rules[date.weekday()])

    def get_month_based_factor(self, date: date | datetime) -> float:
        """
        Get the month based factor for a given date.

        Args:
            date (date): The date to get the month based factor for.

        Returns:
            float: The month based factor for the given date.
        """
        if not self.is_month_based:
            return (0, FactorChoices.PERCENTAGE)
        return self._factor_to_repr(self.month_based_rules[date.month - 1])

    def get_season_based_factor(self, date: date) -> float:
        """
        Get the season based factor for a given date.

        Args:
            date (date): The date to get the season based factor for.

        Returns:
            float: The season based factor for the given date.
        """
        if not self.is_season_based:
            return (0, FactorChoices.PERCENTAGE)
        for rule in self.season_based_rules:
            if is_within_period(rule["start_date"], rule["end_date"], date):
                return self._factor_to_repr(rule)
        return (0, FactorChoices.PERCENTAGE)

    def get_occupancy_based_factor(self, occupancy: int) -> tuple[int | float, int]:
        """
        Get the occupancy based factor for a given occupancy.

        Args:
            occupancy (int): The occupancy to get the occupancy based factor for.
            rate (int): The rate to get the occupancy based factor for.

        Returns:
            int | float: The occupancy based factor for the given occupancy.
            int: The occupancy based factor for the given occupancy.
        """
        if not self.is_occupancy_based:
            return (0, FactorChoices.PERCENTAGE)
        for i in range(len(self.occupancy_based_trigger_rules)):
            if occupancy >= self.occupancy_based_trigger_rules[i]["min_occupancy"]:
                return self._factor_to_repr(self.occupancy_based_trigger_rules[i])
        return (0, FactorChoices.PERCENTAGE)

    @staticmethod
    def _get_trigger_datetime(
        date: date,
        day_ahead: int,
        hour: int,
        tzinfo: ZoneInfo,
    ) -> datetime:
        return datetime.combine(
            date - timedelta(days=day_ahead),
            time(hour),
            tzinfo=tzinfo,
        )

    def get_time_based_factor(
        self,
        date: date,
        current_datetime: datetime,
        occupancy: int,
    ) -> float:
        """
        Get the time based multiplier factor for a given date and time.

        Args:
            date (date): The date to get the time based multiplier factor for.
            current_datetime (datetime): The time to get the time based multiplier factor for.
            occupancy (int): The occupancy to get the time based multiplier factor for.

        Returns:
            float: The time based multiplier factor for the given date and time.
        """
        # Skip date in the past
        lead_days = (date - current_datetime.date()).days
        if lead_days < 0:
            raise ValidationError("Date must be in the future.")
        # Early return if not time based or lead days is invalid
        if not self.is_time_based or lead_days > TimeBasedTriggerRule.MAX_DAY_AHEAD:
            return (0, FactorChoices.PERCENTAGE)
        for rule in self.time_based_trigger_rules:
            trigger_datetime = self._get_trigger_datetime(
                date,
                rule["day_ahead"],
                rule["hour"],
                self.timezone,
            )
            if (
                current_datetime >= trigger_datetime
                and occupancy >= rule["min_occupancy"]
            ):
                return self._factor_to_repr(rule)
        return (0, FactorChoices.PERCENTAGE)

    @staticmethod
    def _calculate_rate_by_factors(
        base_rate: int, factors: list[tuple[int | float, int]]
    ):
        percentage_sum = 0
        increment_sum = 0
        for factor in factors:
            if factor[1] == FactorChoices.PERCENTAGE:
                percentage_sum += factor[0]
            else:
                increment_sum += factor[0]
        return math.ceil(base_rate * (1 + percentage_sum / 100)) + increment_sum

    def calculate_rate(
        self,
        rate_plan_id: int,
        date: date,
        current_datetime: datetime,
        occupancy: int,
    ) -> int:
        """
        Calculate the rate for a given date, rate and occupancy.

        Args:
            rate (int): The rate to calculate the multiplier factor for.
            date (date): The date to calculate the multiplier factor for.
            current_time (timezone.datetime.time): The time to calculate the multiplier factor for.
            occupancy (int): The occupancy to calculate the multiplier factor for.

        Returns:
            int: The calculated rate.
        """
        base_rate = self.get_base_rate(date, rate_plan_id)

        if not self.is_enabled:
            return base_rate

        factors = []
        factors.append(self.get_lead_days_based_factor(date, current_datetime))
        factors.append(self.get_weekday_based_factor(date))
        factors.append(self.get_month_based_factor(date))
        factors.append(self.get_season_based_factor(date))
        factors.append(self.get_occupancy_based_factor(occupancy))
        factors.append(self.get_time_based_factor(date, current_datetime, occupancy))
        return self._calculate_rate_by_factors(base_rate, factors)
