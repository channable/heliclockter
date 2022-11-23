from zoneinfo import ZoneInfo

from heliclockter import datetime_utc, timedelta


def test_datetime_tz_subtraction() -> None:
    dt_1 = datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC'))
    dt_2 = datetime_utc(2020, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC'))

    assert dt_1 - dt_2 == timedelta(days=366)
    assert dt_2 - dt_1 == timedelta(days=-366)

    assert dt_1 - timedelta(days=366) == dt_2
