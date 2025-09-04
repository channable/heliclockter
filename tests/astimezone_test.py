from zoneinfo import ZoneInfo

from parameterized import parameterized  # type: ignore[import-untyped]

from heliclockter import datetime_local, datetime_tz, datetime_utc, tz_local
from tests.shared import datetime_cet


@parameterized.expand(
    [
        # Test astimezone on datetime_utc
        (
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('CET'),
            datetime_tz(2021, 1, 1, 11, 0, 0, tzinfo=ZoneInfo('CET')),
        ),
        (
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('EST'),
            datetime_tz(2021, 1, 1, 5, 0, 0, tzinfo=ZoneInfo('EST')),
        ),
        (
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('UTC'),
            datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        ),
        # Test astimezone on datetime_cet
        (
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('UTC'),
            datetime_tz(2021, 1, 1, 9, 0, 0, tzinfo=ZoneInfo('UTC')),
        ),
        (
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('EST'),
            datetime_tz(2021, 1, 1, 4, 0, 0, tzinfo=ZoneInfo('EST')),
        ),
        (
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('CET'),
            datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
        ),
        # Test astimezone on datetime_tz
        (
            datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('CET'),
            datetime_tz(2021, 1, 1, 11, 0, 0, tzinfo=ZoneInfo('CET')),
        ),
        (
            datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('UTC'),
            datetime_tz(2021, 1, 1, 9, 0, 0, tzinfo=ZoneInfo('UTC')),
        ),
    ]
)
def test_astimezone(
    original_dt: datetime_tz, target_tz: ZoneInfo, expected_dt: datetime_tz
) -> None:
    """Test that astimezone returns the correct datetime with proper timezone conversion."""
    result = original_dt.astimezone(target_tz)

    # Check that the result is of the same class as the original
    assert isinstance(result, datetime_tz)

    # Check that the timezone conversion is correct
    assert result.year == expected_dt.year
    assert result.month == expected_dt.month
    assert result.day == expected_dt.day
    assert result.hour == expected_dt.hour
    assert result.minute == expected_dt.minute
    assert result.second == expected_dt.second
    assert result.microsecond == expected_dt.microsecond
    assert result.tzinfo == expected_dt.tzinfo


def test_astimezone_converts_type() -> None:
    """Test that astimezone converts to datetime_tz when changing timezones."""
    utc_dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    result_utc = utc_dt.astimezone(ZoneInfo('CET'))
    assert isinstance(result_utc, datetime_tz)

    cet_dt = datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET'))
    result_cet = cet_dt.astimezone(ZoneInfo('UTC'))
    assert isinstance(result_cet, datetime_tz)

    local_dt = datetime_local.now()
    result_local = local_dt.astimezone(ZoneInfo('CET'))
    assert isinstance(result_local, datetime_tz)

    tz_dt = datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    result_tz = tz_dt.astimezone(ZoneInfo('CET'))
    assert isinstance(result_tz, datetime_tz)


def test_astimezone_same_timezone() -> None:
    """Test astimezone when converting to the same timezone."""
    dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))

    # Convert to the same timezone
    result = dt.astimezone(ZoneInfo('UTC'))

    assert isinstance(result, datetime_tz)
    assert result == dt  # Should be identical
    assert result.tzinfo == ZoneInfo('UTC')


def test_astimezone_with_different_datetime_types() -> None:
    """Test astimezone behavior with different datetime_tz subclasses."""
    # Test datetime_utc
    utc_dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    utc_to_cet = utc_dt.astimezone(ZoneInfo('CET'))
    assert type(utc_to_cet) is datetime_tz  # pylint: disable=unidiomatic-typecheck
    assert utc_to_cet.tzinfo == ZoneInfo('CET')
    assert utc_to_cet.hour == utc_dt.hour + 1

    # Test datetime_cet
    cet_dt = datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET'))
    cet_to_utc = cet_dt.astimezone(ZoneInfo('UTC'))
    assert type(cet_to_utc) is datetime_tz  # pylint: disable=unidiomatic-typecheck
    assert cet_to_utc.tzinfo == ZoneInfo('UTC')
    assert cet_to_utc.hour == cet_dt.hour - 1

    # Test datetime_local
    local_dt = datetime_local.now()
    local_to_cet = local_dt.astimezone(ZoneInfo('CET'))
    assert type(local_to_cet) is datetime_tz  # pylint: disable=unidiomatic-typecheck
    assert local_to_cet.tzinfo == ZoneInfo('CET')


def test_astimezone_timezone_conversion_accuracy() -> None:
    """Test that astimezone correctly handles timezone conversions."""
    # Test UTC to various timezones
    utc_dt = datetime_utc(2021, 1, 1, 12, 0, 0, tzinfo=ZoneInfo('UTC'))

    # UTC to EST (UTC-5)
    est_result = utc_dt.astimezone(ZoneInfo('EST'))
    assert est_result.hour == 7  # 12:00 UTC - 5 hours = 7:00 EST

    # UTC to CET (UTC+1 in January)
    cet_result = utc_dt.astimezone(ZoneInfo('CET'))
    assert cet_result.hour == 13  # 12:00 UTC + 1 hour = 13:00 CET

    # UTC to JST (UTC+9)
    jst_result = utc_dt.astimezone(ZoneInfo('Asia/Tokyo'))
    assert jst_result.hour == 21  # 12:00 UTC + 9 hours = 21:00 JST

@parameterized.expand(
    [
        datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
        datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_local.now(),
    ]
)
def test_astimezone_without_arguments(dt: datetime_tz) -> None:
    result = dt.astimezone()
    assert isinstance(result, datetime_tz)
    assert result.tzinfo == tz_local

    result2 = dt.astimezone(None)
    assert isinstance(result2, datetime_tz)
    assert result2.tzinfo == tz_local

    assert dt.timestamp() == result.timestamp() == result2.timestamp()
