from datetime import date

import pytest
from psycopg2._range import DateRange
from rest_framework import serializers

from ..serializers import DateRangeField


def test_to_internal_value_valid_data():
    data = {"start_date": "2023-05-20", "end_date": "2023-05-25", "bounds": "[]"}
    result = DateRangeField().to_internal_value(data)
    expected_start_date = date(2023, 5, 20)
    expected_end_date = date(2023, 5, 26)  # normalizing bounds
    expected_bounds = "[)"  # normalizing bounds
    assert isinstance(result, DateRange)
    assert result.lower == expected_start_date
    assert result.upper == expected_end_date
    assert result._bounds == expected_bounds


def test_to_internal_value_missing_dates():
    data = {
        "start_date": "2023-05-20",
        # Missing "end_date" key
        "bounds": "[]",
    }
    with pytest.raises(serializers.ValidationError):
        DateRangeField().to_internal_value(data)


def test_to_internal_value_invalid_date_format():
    data = {"start_date": "2023-05-20", "end_date": "2023-05-25", "bounds": "[]"}
    # Change the start_date to an invalid format
    data["start_date"] = "2023/05/20"
    with pytest.raises(serializers.ValidationError):
        DateRangeField().to_internal_value(data)


def test_to_internal_value_invalid_date_order():
    data = {
        "start_date": "2023-05-25",  # Later date
        "end_date": "2023-05-20",  # Earlier date
        "bounds": "[]",
    }
    with pytest.raises(serializers.ValidationError):
        DateRangeField().to_internal_value(data)


def test_to_internal_value_normalized_bounds():
    data = {"start_date": "2023-05-20", "end_date": "2023-05-25", "bounds": "()"}
    result = DateRangeField().to_internal_value(data)
    expected_start_date = date(2023, 5, 21)  # start_date + 1 day
    expected_end_date = date(2023, 5, 25)
    expected_bounds = "[)"
    assert isinstance(result, DateRange)
    assert result.lower == expected_start_date
    assert result.upper == expected_end_date
    assert result._bounds == expected_bounds


def test_to_representation():
    value = DateRange(date(2023, 5, 20), date(2023, 5, 25), bounds="[]")
    result = DateRangeField().to_representation(value)
    expected_result = {
        "start_date": date(2023, 5, 20),
        "end_date": date(2023, 5, 24),  # end_date - 1 day
        "bounds": "[]",
    }
    assert result == expected_result
