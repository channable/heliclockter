import datetime
from zoneinfo import ZoneInfo

import pytest
from parameterized import parameterized  # type: ignore[import-untyped]

from heliclockter import datetime_tz, timedelta, tz_local


@parameterized.expand(
    [
        (datetime.datetime(2021, 1, 1, 10, tzinfo=tz_local),),
        (datetime.datetime(2021, 1, 1, 10, tzinfo=ZoneInfo('CET')),),
        (datetime.datetime(2021, 1, 1, 10, tzinfo=ZoneInfo('UTC')),),
        (
            datetime.datetime(
                2021, 1, 1, 10, tzinfo=datetime.timezone(datetime.timedelta(hours=-8))
            ),
        ),
        (datetime.datetime(2021, 1, 1, 10, tzinfo=datetime.timezone(timedelta(hours=6))),),
    ]
)
def test_assert_aware_datetime(dt: datetime.datetime) -> None:
    datetime_tz.assert_aware_datetime(dt)


def test_assert_aware_datetime_no_tz() -> None:
    with pytest.raises(AssertionError):
        datetime_tz.assert_aware_datetime(datetime.datetime(2021, 1, 1, 10))
