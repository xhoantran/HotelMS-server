from datetime import datetime

from ..utils import is_within_period


def test_is_within_period():
    assert is_within_period("12/01", "01/20", "12/15/2022")
    assert is_within_period("12/01", "01/20", "01/15/2023")
    assert not is_within_period("12/01", "01/20", "11/30/2022")
    assert not is_within_period("12/01", "01/20", "02/01/2023")
    assert is_within_period("01/01", "12/31", "01/01/2023")
    assert is_within_period("01/01", "02/01", "01/15/2023")
    assert not is_within_period("03/01", "02/01", "02/15/2023")

    start_date = "01/20"
    end_date = "12/01"
    date_str = "12/15/2022"
    assert not is_within_period(start_date, end_date, date_str)

    start_date = "12/20"
    end_date = "01/01"
    date_str = "10/15/2022"
    date = datetime.strptime(date_str, "%m/%d/%Y").date()
    assert not is_within_period(start_date, end_date, date)

    start_date = "12/20"
    end_date = "01/01"
    date_str = "12/25/2022"
    date = datetime.strptime(date_str, "%m/%d/%Y").date()
    assert is_within_period(start_date, end_date, date)
