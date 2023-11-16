from zoneinfo import ZoneInfo

from parameterized import parameterized  # type: ignore[import-untyped]

from heliclockter import datetime_tz, datetime_utc


@parameterized.expand(
    [
        (
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
            '%Y-%m-%d',
            '2021-01-10',
        ),
        (
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
            '%Y-%m-%d %H:%M',
            '2021-01-10 09:00',
        ),
        (
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
            '%Y-%m-%d %H:%M:%S',
            '2021-01-10 09:00:00',
        ),
        (
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
            '%Y-%m-%d %H:%M:%SZ',
            '2021-01-10 09:00:00Z',
        ),
        (
            datetime_utc(2021, 1, 10, 9, 00, 00, tzinfo=ZoneInfo('UTC')),
            '%Y-%m-%dT%H:%M:%S.%f',
            '2021-01-10T09:00:00.000000',
        ),
    ]
)
def test_strftime(dt: datetime_tz, fmt: str, expected_str: str) -> None:
    formatted_str = dt.strftime(fmt)
    assert formatted_str == expected_str
