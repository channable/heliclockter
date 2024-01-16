from copy import deepcopy
from datetime import datetime, timezone, tzinfo
from typing import Optional, Type, Union
from zoneinfo import ZoneInfo

import pytest
from parameterized import parameterized  # type: ignore[import-untyped]

from heliclockter import (
    DateTimeTzT,
    DatetimeTzError,
    datetime_local,
    datetime_tz,
    datetime_utc,
    timedelta,
    tz_local,
)

from tests.shared import datetime_cet

DatetimeT = Union[Type[datetime_tz], Type[datetime_cet], Type[datetime_utc]]


@parameterized.expand(
    [
        # Tests for datetime_tz. Parsing datetime_tz from `datetime` should not modify hours.
        (ZoneInfo('CET'), datetime_tz, 10),
        (timezone(timedelta(hours=1)), datetime_tz, 10),
        (ZoneInfo('UTC'), datetime_tz, 10),
        (timezone(timedelta(hours=-4)), datetime_tz, 10),
        (timezone(timedelta(hours=4)), datetime_tz, 10),
        # Tests for datetime_cet. Parsing datetime_cet from `datetime` should modify hours, if
        # the UTC offset of the `datetime` is not equal to that of the 'CET' timezone.
        (ZoneInfo('CET'), datetime_cet, 10),
        (timezone(timedelta(hours=1)), datetime_cet, 10),
        (ZoneInfo('UTC'), datetime_cet, 11),
        (timezone(timedelta(hours=-4)), datetime_cet, 15),
        (timezone(timedelta(hours=4)), datetime_cet, 7),
        # Tests for datetime_utc. Parsing datetime_utc from `datetime` should modify hours, if
        # the timezone of the `datetime` is not UTC.
        (ZoneInfo('CET'), datetime_utc, 9),
        (timezone(timedelta(hours=1)), datetime_utc, 9),
        (ZoneInfo('UTC'), datetime_utc, 10),
        (timezone(timedelta(hours=-4)), datetime_utc, 14),
        (timezone(timedelta(hours=4)), datetime_utc, 6),
        # Tests to ensure a naive datetime can be parsed as datetime_utc, and datetime_cet.
        # We cannot test `datetime_local` as the expected hour will vary on the system testing.
        (None, datetime_utc, 10),
        (None, datetime_cet, 10),
    ]
)
def test_from_datetime(
    input_tz: Optional[tzinfo],
    expected_dt_class: DatetimeT,
    expected_hour: int,
) -> None:
    input_dt = datetime(year=2021, month=1, day=1, hour=10, tzinfo=input_tz)
    dt = expected_dt_class.from_datetime(input_dt)
    assert isinstance(dt, expected_dt_class)
    assert dt.hour == expected_hour


def test_datetime_local_from_datetime() -> None:
    input_dt = datetime(year=2021, month=1, day=1, hour=10)
    dt = datetime_local.from_datetime(input_dt)
    assert isinstance(dt, datetime_local)


def test_datetime_tz_from_naive_datetime() -> None:
    # datetime_tz should not be able to parse from a naive datetime.datetime
    input_dt = datetime(year=2021, month=1, day=1, hour=10)
    with pytest.raises(
        DatetimeTzError, match='Cannot create aware datetime from naive if no tz is assumed'
    ):
        datetime_tz.from_datetime(input_dt)


@parameterized.expand(
    [
        (
            datetime_utc,
            10,
            datetime_utc(year=2021, month=1, day=1, hour=10, tzinfo=ZoneInfo('UTC')),
        ),
        (
            datetime_cet,
            10,
            datetime_cet(year=2021, month=1, day=1, hour=10, tzinfo=ZoneInfo('CET')),
        ),
        (
            datetime_cet,
            11,
            datetime_utc(year=2021, month=1, day=1, hour=10, tzinfo=ZoneInfo('UTC')),
        ),
    ]
)
def test_from_datetime_tz(
    expected_dt_class: DatetimeT, expected_hour: int, input_dt: DateTimeTzT
) -> None:
    reparsed = expected_dt_class.from_datetime(input_dt)
    assert isinstance(reparsed, expected_dt_class)
    assert reparsed.hour == expected_hour


def test_datetime_tz_now() -> None:
    with pytest.raises(
        DatetimeTzError,
        match=(
            'Must override assumed_timezone_for_timezone_naive_input '
            'or give a timezone when calling now'
        ),
    ):
        datetime_tz.now()

    dt = datetime_tz.now(tz_local)
    assert isinstance(dt, datetime_tz)


def test_datetime_cet_now() -> None:
    dt = datetime_cet.now()
    assert isinstance(dt, datetime_cet)


def test_deepcopy_datetime_tz() -> None:
    dt = datetime_tz(year=2021, month=1, day=1, tzinfo=timezone(timedelta(hours=1)))
    dt_deep_copied = deepcopy(dt)
    assert id(dt) != id(dt_deep_copied)
    assert isinstance(dt_deep_copied, datetime_tz)


@parameterized.expand(
    [
        # UTC naive tests
        (
            '2021-01-10 09:00',
            '%Y-%m-%d %H:%M',
            datetime_utc,
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
        ),
        (
            '2021-01-10 09:00:00',
            '%Y-%m-%d %H:%M:%S',
            datetime_utc,
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
        ),
        (
            '2021-01-10T09:00:00.000000',
            '%Y-%m-%dT%H:%M:%S.%f',
            datetime_utc,
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
        ),
        # UTC aware tests
        (
            '2021-01-10 09:00+00:00',
            '%Y-%m-%d %H:%M%z',
            datetime_utc,
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
        ),
        (
            '2021-01-10 09:00:00+00:00',
            '%Y-%m-%d %H:%M:%S%z',
            datetime_utc,
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
        ),
        (
            '2021-01-10T09:00:00.000000+00:00',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            datetime_utc,
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
        ),
        # CET tests
        (
            '2021-01-10 09:00',
            '%Y-%m-%d %H:%M',
            datetime_cet,
            datetime_cet(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('CET')),
        ),
        (
            '2021-01-10 09:00:00',
            '%Y-%m-%d %H:%M:%S',
            datetime_cet,
            datetime_cet(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('CET')),
        ),
        (
            '2021-01-10T09:00:00.000000',
            '%Y-%m-%dT%H:%M:%S.%f',
            datetime_cet,
            datetime_cet(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('CET')),
        ),
        # CET aware tests
        (
            '2021-01-10 09:00+00:00',
            '%Y-%m-%d %H:%M%z',
            datetime_cet,
            datetime_cet(2021, 1, 10, 10, 00, 00, tzinfo=ZoneInfo('CET')),
        ),
        (
            '2021-01-10 09:00:00+00:00',
            '%Y-%m-%d %H:%M:%S%z',
            datetime_cet,
            datetime_cet(2021, 1, 10, 10, 00, 00, tzinfo=ZoneInfo('CET')),
        ),
        (
            '2021-01-10T09:00:00.000000+00:00',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            datetime_cet,
            datetime_cet(2021, 1, 10, 10, 00, 00, tzinfo=ZoneInfo('CET')),
        ),
    ]
)
def test_strptime(
    dt_string: str, fmt: str, dt_class: Type[DateTimeTzT], expected_dt: DateTimeTzT
) -> None:
    assert dt_class.strptime(dt_string, fmt) == expected_dt


def test_strptime_datetime_tz_naive_dt_string() -> None:
    with pytest.raises(
        DatetimeTzError, match='Cannot create aware datetime from naive if no tz is assumed'
    ):
        datetime_tz.strptime('2021-01-10 09:00', '%Y-%m-%d %H:%M')


@parameterized.expand(
    [
        (1609491600.0, datetime_utc(2021, 1, 1, 9, 0, tzinfo=ZoneInfo('UTC'))),
        (1625126400.0, datetime_utc(2021, 7, 1, 8, 0, tzinfo=ZoneInfo('UTC'))),
        (1656663915.0, datetime_utc(2022, 7, 1, 8, 25, 15, tzinfo=ZoneInfo('UTC'))),
        (1277972715.0, datetime_utc(2010, 7, 1, 8, 25, 15, tzinfo=ZoneInfo('UTC'))),
    ]
)
def test_fromtimestamp(timestamp: float, expected_dt: datetime_utc) -> None:
    parsed_dt = datetime_utc.fromtimestamp(timestamp)
    assert parsed_dt == expected_dt


@parameterized.expand(
    [
        (datetime_utc, 2),
        (datetime_utc, -2),
        (datetime_utc, 0, 2),
        (datetime_cet, 2),
        (datetime_cet, -2),
        (datetime_cet, 0, 2),
        (datetime_local, 2),
        (datetime_local, -2),
        (datetime_local, 0, 2),
        (datetime_tz, 2, 0, ZoneInfo('EST')),
        (datetime_tz, -2, 0, ZoneInfo('EST')),
        (datetime_tz, 0, 2, ZoneInfo('EST')),
    ]
)
def test_future_and_past(
    dt_class: Type[DateTimeTzT], days: int = 0, weeks: int = 0, tz: Optional[ZoneInfo] = None
) -> None:
    delta = timedelta(days=days, weeks=weeks)
    dt_past = dt_class.past(days=days, weeks=weeks, tz=tz)
    dt_now = dt_class.now(tz=tz)
    dt_future = dt_class.future(days=days, weeks=weeks, tz=tz)

    assert (dt_now - dt_past).days == delta.days
    assert (dt_future - dt_now).days == delta.days


def test_future_and_past_no_tz() -> None:
    error_msg = (
        'Must override assumed_timezone_for_timezone_naive_input '
        'or give a timezone when calling now'
    )
    with pytest.raises(DatetimeTzError, match=error_msg):
        datetime_tz.future(days=2)

    with pytest.raises(DatetimeTzError, match=error_msg):
        datetime_tz.past(days=2)


@parameterized.expand([(0,), (1,)])
def test_fold_tz(fold: int) -> None:
    dt = datetime_tz(2023, 10, 29, 2, 30, fold=fold, tzinfo=ZoneInfo("Europe/Berlin"))
    iso = "2023-10-29T02:30:00+01:00" if fold == 1 else '2023-10-29T02:30:00+02:00'
    assert dt.isoformat() == iso


@parameterized.expand([(0,), (1,)])
def test_fold_utc(fold: int) -> None:
    dt = datetime_utc(2023, 10, 29, 2, 30, fold=fold, tzinfo=ZoneInfo("UTC"))
    assert dt.isoformat() == "2023-10-29T02:30:00+00:00"
