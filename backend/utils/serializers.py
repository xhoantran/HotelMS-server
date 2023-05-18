from datetime import date, timedelta

from psycopg2._range import DateRange
from rest_framework import serializers


class DateRangeField(serializers.Field):
    def to_internal_value(self, data):
        start_date = data.get("start_date", None)
        end_date = data.get("end_date", None)

        # Validate start_date and end_date
        if start_date is None or end_date is None:
            raise serializers.ValidationError("start_date and end_date are required")
        try:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        except ValueError:
            raise serializers.ValidationError("Date must be in ISO format")
        if start_date > end_date:
            raise serializers.ValidationError("start_date must be before end_date")

        bounds = data.get("bounds", "[]")
        return DateRange(start_date, end_date, bounds)

    def to_representation(self, value: DateRange):
        if value._bounds == "[)":
            return {
                "start_date": value.lower,
                # We want [] instead of [)
                "end_date": value.upper - timedelta(days=1),
            }
        elif value._bounds == "[]":
            return {
                "start_date": value.lower,
                "end_date": value.upper,
            }
        else:
            raise ValueError("Invalid bounds")
