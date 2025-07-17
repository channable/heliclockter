import pickle
from zoneinfo import ZoneInfo

from parameterized import parameterized  # type: ignore[import-untyped]

from heliclockter import datetime_local, datetime_tz, datetime_utc
from tests.shared import datetime_cet


@parameterized.expand(
    [
        datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
        datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('EST')),
        datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET')),
        datetime_local.now(),
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
    dt = datetime_cet(2021, 10, 31, 2, 30, 0, tzinfo=ZoneInfo('CET'), fold=1)

    # Pickle and unpickle
    pickled = pickle.dumps(dt)
    unpickled = pickle.loads(pickled)

    # Check that fold is preserved
    assert dt.fold == 1
    assert unpickled.fold == 1
    assert isinstance(unpickled, datetime_cet)


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


def test_pickling_edge_cases() -> None:
    """Test pickling with edge cases."""
    # Test with very early date
    early_dt = datetime_utc(1900, 1, 1, 0, 0, 0, tzinfo=ZoneInfo('UTC'))
    pickled = pickle.dumps(early_dt)
    unpickled = pickle.loads(pickled)
    assert unpickled == early_dt

    # Test with very late date
    late_dt = datetime_utc(2100, 12, 31, 23, 59, 59, 999999, tzinfo=ZoneInfo('UTC'))
    pickled = pickle.dumps(late_dt)
    unpickled = pickle.loads(pickled)
    assert unpickled == late_dt

    # Test with leap year date
    leap_dt = datetime_utc(2020, 2, 29, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
    pickled = pickle.dumps(leap_dt)
    unpickled = pickle.loads(pickled)
    assert unpickled == leap_dt


def test_pickling_different_protocols() -> None:
    """Test pickling with different pickle protocols."""
    dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))

    # Test with protocol 4 (Python 3.4+)
    pickled_4 = pickle.dumps(dt, protocol=4)
    unpickled_4 = pickle.loads(pickled_4)
    assert unpickled_4 == dt

    # Test with protocol 5 (Python 3.8+)
    pickled_5 = pickle.dumps(dt, protocol=5)
    unpickled_5 = pickle.loads(pickled_5)
    assert unpickled_5 == dt


def test_pickling_with_complex_timezones() -> None:
    """Test pickling with complex timezone objects."""
    # Test with timezone that has DST rules
    dt_cet = datetime_cet(2021, 7, 1, 12, 0, 0, tzinfo=ZoneInfo('CET'))
    pickled = pickle.dumps(dt_cet)
    unpickled = pickle.loads(pickled)
    assert unpickled.tzinfo == ZoneInfo('CET')

    # Test with timezone that has offset
    dt_est = datetime_tz(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('EST'))
    pickled = pickle.dumps(dt_est)
    unpickled = pickle.loads(pickled)
    assert unpickled.tzinfo == ZoneInfo('EST')


def test_pickling_roundtrip_equality() -> None:
    """Test that pickling and unpickling preserves exact equality."""
    test_cases = [
        datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC')),
        datetime_cet(2021, 6, 15, 14, 30, 45, 123456, tzinfo=ZoneInfo('CET')),
        datetime_tz(2021, 12, 31, 23, 59, 59, 999999, tzinfo=ZoneInfo('EST')),
        datetime_local.now(),
    ]

    for dt in test_cases:
        pickled = pickle.dumps(dt)
        unpickled = pickle.loads(pickled)

        # Check exact equality
        assert unpickled == dt

        # Check that all attributes match
        assert unpickled.year == dt.year
        assert unpickled.month == dt.month
        assert unpickled.day == dt.day
        assert unpickled.hour == dt.hour
        assert unpickled.minute == dt.minute
        assert unpickled.second == dt.second
        assert unpickled.microsecond == dt.microsecond
        assert unpickled.tzinfo == dt.tzinfo
        assert unpickled.fold == dt.fold


def test_pickling_subclass_preservation() -> None:
    """Test that pickling preserves the exact subclass type."""
    # Test datetime_utc
    utc_dt = datetime_utc(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    pickled = pickle.dumps(utc_dt)
    unpickled = pickle.loads(pickled)
    assert isinstance(unpickled, datetime_utc)

    # Test datetime_cet
    cet_dt = datetime_cet(2021, 1, 1, 10, 0, 0, tzinfo=ZoneInfo('CET'))
    pickled = pickle.dumps(cet_dt)
    unpickled = pickle.loads(pickled)
    assert isinstance(unpickled, datetime_cet)

    local_dt = datetime_local.now()
    pickled = pickle.dumps(local_dt)
    unpickled = pickle.loads(pickled)
    assert isinstance(unpickled, datetime_local)
