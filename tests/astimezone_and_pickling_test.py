import pickle
from copy import deepcopy
from zoneinfo import ZoneInfo

import pytest
from parameterized import parameterized  # type: ignore[import-untyped]

from heliclockter import datetime_local, datetime_tz, datetime_utc
from tests.shared import datetime_cet


@parameterized.expand(
    [
        # Test astimezone on datetime_utc
        (
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('CET'),
            datetime_utc(2021, 1, 1, 11, 0, 0, tzinfo=ZoneInfo('CET')),
        ),
        (
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('EST'),
            datetime_utc(2021, 1, 1, 5, 0, 0, tzinfo=ZoneInfo('EST')),
        ),
        (
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
            ZoneInfo('UTC'),
            datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        ),
        # Test astimezone on datetime_cet
        (
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('UTC'),
            datetime_cet(2021, 1, 1, 9, 0, 0, tzinfo=ZoneInfo('UTC')),
        ),
        (
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('EST'),
            datetime_cet(2021, 1, 1, 4, 0, 0, tzinfo=ZoneInfo('EST')),
        ),
        (
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
            ZoneInfo('CET'),
            datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
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
    assert isinstance(result, type(original_dt))
    
    # Check that the timezone conversion is correct
    assert result.year == expected_dt.year
    assert result.month == expected_dt.month
    assert result.day == expected_dt.day
    assert result.hour == expected_dt.hour
    assert result.minute == expected_dt.minute
    assert result.second == expected_dt.second
    assert result.microsecond == expected_dt.microsecond
    assert result.tzinfo == expected_dt.tzinfo


def test_astimezone_preserves_type() -> None:
    """Test that astimezone preserves the original class type."""
    # Test with datetime_utc
    utc_dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    result_utc = utc_dt.astimezone(ZoneInfo('CET'))
    assert isinstance(result_utc, datetime_utc)
    
    # Test with datetime_cet
    cet_dt = datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET'))
    result_cet = cet_dt.astimezone(ZoneInfo('UTC'))
    assert isinstance(result_cet, datetime_cet)
    
    # Test with datetime_local
    local_dt = datetime_local(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    result_local = local_dt.astimezone(ZoneInfo('CET'))
    assert isinstance(result_local, datetime_local)
    
    # Test with datetime_tz
    tz_dt = datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    result_tz = tz_dt.astimezone(ZoneInfo('CET'))
    assert isinstance(result_tz, datetime_tz)


@parameterized.expand(
    [
        # Test pickling datetime_utc
        datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
        # Test pickling datetime_cet
        datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
        datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        # Test pickling datetime_tz
        datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('EST')),
        # Test pickling datetime_local
        datetime_local(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_local(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
    ]
)
def test_pickling(dt: datetime_tz) -> None:
    """Test that datetime_tz objects can be pickled and unpickled correctly."""
    # Pickle the datetime
    pickled = pickle.dumps(dt)
    
    # Unpickle the datetime
    unpickled = pickle.loads(pickled)
    
    # Check that the unpickled object is of the same class
    assert isinstance(unpickled, type(dt))
    
    # Check that all attributes are preserved
    assert unpickled.year == dt.year
    assert unpickled.month == dt.month
    assert unpickled.day == dt.day
    assert unpickled.hour == dt.hour
    assert unpickled.minute == dt.minute
    assert unpickled.second == dt.second
    assert unpickled.microsecond == dt.microsecond
    assert unpickled.tzinfo == dt.tzinfo
    assert unpickled.fold == dt.fold


def test_pickling_with_fold() -> None:
    """Test pickling with fold attribute set."""
    # Create a datetime with fold=1
    dt = datetime_utc(2021, 10, 31, 2, 30, 0, tzinfo=ZoneInfo('CET'), fold=1)
    
    # Pickle and unpickle
    pickled = pickle.dumps(dt)
    unpickled = pickle.loads(pickled)
    
    # Check that fold is preserved
    assert unpickled.fold == 1
    assert isinstance(unpickled, datetime_utc)


def test_deepcopy_astimezone() -> None:
    """Test that astimezone works correctly with deepcopy."""
    original = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    
    # Deep copy the original
    copied = deepcopy(original)
    
    # Apply astimezone to the copy
    result = copied.astimezone(ZoneInfo('CET'))
    
    # Check that the result is correct
    assert isinstance(result, datetime_utc)
    assert result.hour == 11  # UTC+1 for CET in January
    assert result.tzinfo == ZoneInfo('CET')


def test_astimezone_edge_cases() -> None:
    """Test astimezone with edge cases like DST transitions."""
    # Test around DST transition (CET to CEST)
    # March 28, 2021 - clocks go forward at 2:00 AM
    before_dst = datetime_utc(2021, 3, 28, 1, 30, 0, tzinfo=ZoneInfo('UTC'))
    after_dst = datetime_utc(2021, 3, 28, 2, 30, 0, tzinfo=ZoneInfo('UTC'))
    
    # Convert to CET
    before_dst_cet = before_dst.astimezone(ZoneInfo('CET'))
    after_dst_cet = after_dst.astimezone(ZoneInfo('CET'))
    
    assert isinstance(before_dst_cet, datetime_utc)
    assert isinstance(after_dst_cet, datetime_utc)
    
    # The hour difference should be 1 for before DST and 2 for after DST
    assert before_dst_cet.hour == 2  # 1:30 UTC + 1 hour = 2:30 CET
    assert after_dst_cet.hour == 4   # 2:30 UTC + 2 hours = 4:30 CEST


def test_astimezone_same_timezone() -> None:
    """Test astimezone when converting to the same timezone."""
    dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    
    # Convert to the same timezone
    result = dt.astimezone(ZoneInfo('UTC'))
    
    assert isinstance(result, datetime_utc)
    assert result == dt  # Should be identical
    assert result.tzinfo == ZoneInfo('UTC')


def test_pickling_complex_scenarios() -> None:
    """Test pickling with more complex scenarios."""
    # Test with microseconds
    dt_micro = datetime_utc(2021, 1, 1, 10, 0, 0, 123456, tzinfo=ZoneInfo('UTC'))
    pickled = pickle.dumps(dt_micro)
    unpickled = pickle.loads(pickled)
    assert unpickled.microsecond == 123456
    
    # Test with different timezones
    dt_est = datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('EST'))
    pickled = pickle.dumps(dt_est)
    unpickled = pickle.loads(pickled)
    assert unpickled.tzinfo == ZoneInfo('EST')
    
    # Test with fold attribute
    dt_fold = datetime_cet(2021, 10, 31, 2, 30, 0, tzinfo=ZoneInfo('CET'), fold=1)
    pickled = pickle.dumps(dt_fold)
    unpickled = pickle.loads(pickled)
    assert unpickled.fold == 1 