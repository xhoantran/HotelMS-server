from datetime import date as datetype
from datetime import datetime


def is_within_period(
    start_date: datetype,
    end_date: datetype,
    date: datetime | datetype | str,
) -> bool:
    # Convert the strings to datetime objects
    start_date = datetime.strptime(start_date, "%m/%d").date()
    end_date = datetime.strptime(end_date, "%m/%d").date()
    if isinstance(date, str):
        date = datetime.strptime(date, "%m/%d/%Y").date()
    elif isinstance(date, datetime):
        date = date.date()

    # Set the year of the start_date and end_date based on the date's year
    if start_date > end_date:
        # Handle the case where start_date is from the previous year of end_date
        if date.month < start_date.month:
            start_date = start_date.replace(year=date.year - 1)
            end_date = end_date.replace(year=date.year)
        else:
            start_date = start_date.replace(year=date.year)
            end_date = end_date.replace(year=date.year + 1)
    else:
        start_date = start_date.replace(year=date.year)
        end_date = end_date.replace(year=date.year)

    # Check if the date falls within the time period
    return start_date <= date <= end_date
