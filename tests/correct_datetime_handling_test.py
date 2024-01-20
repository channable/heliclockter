#!/usr/bin/env python3

from __future__ import annotations as __annotations

import platform
import time
from contextlib import contextmanager
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from functools import partial, wraps
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pytest

from heliclockter import datetime_local, datetime_tz, tz_local
from heliclockter.systemtz import SystemTZ

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from datetime import tzinfo
    from time import _TimeTuple as TimeTuple
    from time import struct_time
    from typing import ContextManager, Dict, List, Optional, Tuple, Union

    from pytest import FixtureRequest, MonkeyPatch
    from _pytest.mark.structures import ParameterSet


@pytest.fixture()
def systemtz() -> tzinfo:
    """Fixture that returns the system time zone as a tzinfo object.

    SystemTZ is a tzinfo implementation that uses the system timezone.
    This allows tests to run against the local system timezone, possibly mocked
    by the `welldefined_timezone()` fixture.

    Example:
        ```
        def test_foobar(systemtz):
            dt = datetime.datetime.now(systemtz)
            assert dt.timetuple()[:4] == time.localtime()[:4]
        ```
    """
    return SystemTZ()


def winkle_tz_out_of_zoneinfo(
    zi: ZoneInfo,
) -> Tuple[int, int, int, Tuple[Optional[str], Optional[str]]]:
    """Extract timezone information from a ZoneInfo object.

    Iterates through 2 years worth of timestamps to detect daylight saving time
    transitions. Returns the UTC offset, DST offset, whether daylight savings
    transitions happen (during the sampled interval) as well as standard and
    daylight timezone names.

    Example:
        >>> zi = zoneinfo.ZoneInfo('America/New_York')
        >>> winkle_tz_out_of_zoneinfo(zi)
        (18000, 14400, 1, ('EST', 'EDT'))
    """
    assert isinstance(zi, ZoneInfo)

    log: List[Tuple[int, Optional[int], Optional[str], Optional[str]]] = []
    i_dstoff = i_stdname = i_dstname = -1
    now = round(time.time())
    for days in range(0, 365 + 366, 7):
        dt = DateTime.fromtimestamp(now + days * 86400, tz=zi)
        off = dt.utcoffset()
        name = dt.tzname()
        assert off is not None
        dst = dt.dst()
        if dst:
            utcoff = round((off - dst).total_seconds())
            dstoff = round(off.total_seconds())
            stdname = log[-1][2] if log else None
            dstname = name
        else:
            utcoff = round(off.total_seconds())
            dstoff = log[-1][1] if log else None
            stdname = name
            dstname = log[-1][3] if log else None

        if dstoff is not None and i_dstoff < 0:
            i_dstoff = len(log)
        if stdname and i_stdname < 0:
            i_stdname = len(log)
        if dstname and i_dstname < 0:
            i_dstname = len(log)

        if not log or log[-1] != (utcoff, dstoff, stdname, dstname):
            log.append((utcoff, dstoff, stdname, dstname))

        if i_dstoff >= 0 and i_stdname >= 0 and i_dstname >= 0:
            break

    if i_dstoff < 0:
        return -log[0][0], -log[0][0], 0, (log[i_stdname][2], log[i_stdname][2])

    return -log[0][0], -log[i_dstoff][1], 1, (log[i_stdname][2], log[i_dstname][3])


@pytest.fixture(scope='session')
def tzset() -> Iterator[Callable[[], None]]:
    """Fixture to prepare time.tzset and related functions for testing purposes.

    This fixture is responsible for setting up the environment for timezone
    tests. It patches the `time.tzset` function if available (on Unix systems)
    or emulates its behavior on platforms where `time.tzset` is not available
    (like Windows). The fixture also modifies the `tzlocal` availability map to
    ensure that all timezones from `zoneinfo.available_timezones()` are
    considered available.

    The fixture yields a callable that, when invoked, will apply the patched or
    emulated `tzset` function to the current environment. This is useful for
    tests that need to simulate changes in the system's timezone settings.

    Example:
        ```
        def test_my_function(tzset):
            os.environ['TZ'] = 'Pacific/Niue'
            tzset()
            assert time.localtime(1641038400)[:4] == (2022, 1, 1, 1)
        ```
    """
    from zoneinfo import available_timezones

    pytest.importorskip('tzlocal')
    import tzlocal.utils
    from tzlocal.windows_tz import tz_win as bogus_tzlocal_availability_map

    orig_tzset = getattr(time, 'tzset', None)
    if orig_tzset:

        @wraps(orig_tzset)
        def patched_tzset() -> None:
            orig_tzset()
            tzlocal.reload_localzone()

    else:

        @wraps(time.localtime)
        def emulated_localtime(zi: ZoneInfo, secs: Optional[float] = None) -> struct_time:
            if secs is None:
                secs = time.time()
            dt = DateTime.fromtimestamp(secs, tz=zi)
            off = dt.utcoffset()
            off = round(off.total_seconds()) if off else 0
            dst = dt.dst()
            assert dst is not None, "not sure if we properly deal with unknown DST"
            return time.struct_time(
                (
                    dt.year,
                    dt.month,
                    dt.day,
                    dt.hour,
                    dt.minute,
                    dt.second,
                    dt.weekday(),
                    dt.toordinal() - Date(dt.year, 1, 1).toordinal() + 1,
                    -1 if dst is None else int(bool(dst)),
                ),
                {'tm_gmtoff': off, 'tm_zone': dt.tzname()},
            )

        @wraps(time.mktime)
        def emulated_mktime(zi: ZoneInfo, t: Union[struct_time, TimeTuple]) -> float:
            candidate_ts = None
            dt = DateTime(*t[:6], tzinfo=zi)
            ts_fold_0 = dt.timestamp()
            if t[8] < 0 or bool(dt.dst()) == bool(t[8]):
                return ts_fold_0
            if dt.dst():
                candidate_ts = ts_fold_0 + dt.dst().total_seconds()
            dt = DateTime(*t[:6], tzinfo=zi, fold=1)
            ts_fold_1 = dt.timestamp()
            if bool(dt.dst()) == bool(t[8]):
                return ts_fold_1
            if candidate_ts is not None:
                return candidate_ts
            if dt.dst():
                return ts_fold_1 + dt.dst().total_seconds()
            return ts_fold_0 - (time.timezone - time.altzone)

        def emulated_tzset(monkeypatch: MonkeyPatch) -> None:
            monkeypatch.setattr(tzlocal.utils, 'assert_tz_offset', lambda *_, **__: None)
            zi = tzlocal.reload_localzone()
            timezone, altzone, daylight, tzname = winkle_tz_out_of_zoneinfo(zi)
            monkeypatch.setattr(time, 'timezone', timezone)
            monkeypatch.setattr(time, 'altzone', altzone)
            monkeypatch.setattr(time, 'daylight', daylight)
            monkeypatch.setattr(time, 'tzname', tzname)
            monkeypatch.setattr(time, 'localtime', partial(emulated_localtime, zi))
            monkeypatch.setattr(time, 'mktime', partial(emulated_mktime, zi))

    with pytest.MonkeyPatch.context() as monkeypatch:
        for tz in (tz for tz in available_timezones() if tz not in bogus_tzlocal_availability_map):
            monkeypatch.setitem(bogus_tzlocal_availability_map, tz, NotImplemented)
        modified_tzset = patched_tzset if orig_tzset else partial(emulated_tzset, monkeypatch)
        monkeypatch.setattr(time, 'tzset', modified_tzset, raising=False)
        monkeypatch.delenv('TZ', raising=False)  # FIXME: use predefined TZ
        modified_tzset()
        yield modified_tzset


@pytest.fixture(scope='function')
def welldefined_timezone(
    request: FixtureRequest, tzset: Callable[[], None], monkeypatch: MonkeyPatch
) -> Iterator[Callable[[str], ContextManager[ZoneInfo]]]:
    """Ensures a well-defined and constant system timezone while testing.

    Ordinarily, you cannot easily test code that relies on the system timezone
    and some `time` module functions and values, as they would be dependent on
    the system running the test and its configured timezone.

    This fixture provides a context in which code relying on the standard
    library's `time` module functionality, the `tzlocal` module or the `TZ`
    environment variable can be tested under well-defined conditions.

    It achieves this by monkeypatching the `TZ` environment variable and calling
    `tzset()` while itself depending on the fixture preparing `tzset()` to work
    as desired in our test environment.

    By default, tests which depend on this fixture will appear to run in the
    `Etc/UTC` system timezone. Furthermore, it provides a context manager that
    allows convenient changes to the apparent system timezone.

    It can be used like this:

        ```
        def test_foobar(welldefined_timezone):

            # here, the apparent system timezone starts out as Etc/UTC

            with welldefined_timezone('Asia/Ho_Chi_Minh') as tz:
                # code under test that runs as though
                # the system timezone were Asia/Ho_Chi_Minh
                ...
                # It can optionally use the ZoneInfo object returned by the
                # context manager.

            # here, the system timezone is restored to Etc/UTC

            with welldefined_timezone('America/Mexico_City') as tz:
                # code under test that runs as though
                # the system timezone were America/Mexico_City
                ...

            # and here it's back to Etc/UTC again
        ```

    As a side feature, you can also parametrize this fixture itself with
    several timezone names and tests that depend on this fixture will then be
    tested will all of them in turn while outside of the explicitly used
    context manager.
    """

    @contextmanager
    def use_timezone(key: str) -> Iterator[ZoneInfo]:
        zi = ZoneInfo(key)
        assert zi.key == key

        try:
            with monkeypatch.context() as ctx:
                ctx.setenv('TZ', key)
                tzset()
                yield zi
        finally:
            tzset()

    key = getattr(request, 'param', 'Etc/UTC')
    assert key

    tz = ZoneInfo(key)
    assert tz.key == key

    try:
        with monkeypatch.context() as ctx:
            ctx.setenv('TZ', key)
            tzset()
            yield use_timezone
    finally:
        tzset()


POINTS_IN_TIME: Dict[
    str, Union[Tuple[str, int, Tuple[int, ...], int, int, str, Dict[str, int]], ParameterSet]
] = {
    # fmt: off
    'america_st_johns_new_year':              ('America/St_Johns', 1672543800, (2023,  1,  1,  0,  0,  0), -12600,     0, 'NST', {}),
    'america_st_johns_standard_time':         ('America/St_Johns', 1676477096, (2023,  2, 15, 12, 34, 56), -12600,     0, 'NST', {}),
    'america_st_johns_before_dst':            ('America/St_Johns', 1678598999, (2023,  3, 12,  1, 59, 59), -12600,     0, 'NST', {}),
    'america_st_johns_start_of_dst':          ('America/St_Johns', 1678599000, (2023,  3, 12,  3,  0,  0),  -9000,  3600, 'NDT', {}),
    'america_st_johns_during_dst':            ('America/St_Johns', 1689433496, (2023,  7, 15, 12, 34, 56),  -9000,  3600, 'NDT', {}),
    'america_st_johns_still_dst':             ('America/St_Johns', 1699154999, (2023, 11,  5,  0, 59, 59),  -9000,  3600, 'NDT', {}),
    'america_st_johns_fold_0':                ('America/St_Johns', 1699155000, (2023, 11,  5,  1,  0,  0),  -9000,  3600, 'NDT', {'fold': 0}),
    'america_st_johns_end_of_dst':            ('America/St_Johns', 1699158599, (2023, 11,  5,  1, 59, 59),  -9000,  3600, 'NDT', {'fold': 0}),
    'america_st_johns_start_of_fold':         ('America/St_Johns', 1699158600, (2023, 11,  5,  1,  0,  0), -12600,     0, 'NST', {'fold': 1}),
    'america_st_johns_end_of_fold':           ('America/St_Johns', 1699162199, (2023, 11,  5,  1, 59, 59), -12600,     0, 'NST', {'fold': 1}),
    'america_st_johns_after_fold':            ('America/St_Johns', 1699162200, (2023, 11,  5,  2,  0,  0), -12600,     0, 'NST', {}),
    'america_st_johns_new_years_eve':         ('America/St_Johns', 1704079799, (2023, 12, 31, 23, 59, 59), -12600,     0, 'NST', {}),
    # Europe/Dublin designates their GMT usage during winter as DST so that their IST is the standard time
    # with the net effect of their DST offset being negative
    'europe_dublin_new_year':                    ('Europe/Dublin', 1672531200, (2023,  1,  1,  0,  0,  0),      0, -3600, 'GMT', {}),
    'europe_dublin_during_dst':                  ('Europe/Dublin', 1676464496, (2023,  2, 15, 12, 34, 56),      0, -3600, 'GMT', {}),
    'europe_dublin_end_of_dst':                  ('Europe/Dublin', 1679792399, (2023,  3, 26,  0, 59, 59),      0, -3600, 'GMT', {}),
    'europe_dublin_after_dst':                   ('Europe/Dublin', 1679792400, (2023,  3, 26,  2,  0,  0),   3600,     0, 'IST', {}),
    'europe_dublin_standard_time':               ('Europe/Dublin', 1689420896, (2023,  7, 15, 12, 34, 56),   3600,     0, 'IST', {}),
    'europe_dublin_before_dst':                  ('Europe/Dublin', 1698537599, (2023, 10, 29,  0, 59, 59),   3600,     0, 'IST', {}),
    'europe_dublin_fold_0':                      ('Europe/Dublin', 1698537600, (2023, 10, 29,  1,  0,  0),   3600,     0, 'IST', {'fold': 0}),
    'europe_dublin_before_fold':                 ('Europe/Dublin', 1698541199, (2023, 10, 29,  1, 59, 59),   3600,     0, 'IST', {'fold': 0}),
    'europe_dublin_start_of_dst':                ('Europe/Dublin', 1698541200, (2023, 10, 29,  1,  0,  0),      0, -3600, 'GMT', {'fold': 1}),
    'europe_dublin_end_of_fold':                 ('Europe/Dublin', 1698544799, (2023, 10, 29,  1, 59, 59),      0, -3600, 'GMT', {'fold': 1}),
    'europe_dublin_after_fold':                  ('Europe/Dublin', 1698544800, (2023, 10, 29,  2,  0,  0),      0, -3600, 'GMT', {}),
    'europe_dublin_new_years_eve':               ('Europe/Dublin', 1704067199, (2023, 12, 31, 23, 59, 59),      0, -3600, 'GMT', {}),
    # Africa/El_Aaiun (and Africa/Casablanca) are special in that they use negative DST during Ramadan and which lasts only about a month
    'africa_el_aaiun_new_year':                ('Africa/El_Aaiun', 1672527600, (2023,  1,  1,  0,  0,  0),   3600,     0, '+01', {}),
    'africa_el_aaiun_before_dst':              ('Africa/El_Aaiun', 1679187599, (2023,  3, 19,  1, 59, 59),   3600,     0, '+01', {}),
    'africa_el_aaiun_fold_0':                  ('Africa/El_Aaiun', 1679187600, (2023,  3, 19,  2,  0,  0),   3600,     0, '+01', {'fold': 0}),
    'africa_el_aaiun_before_fold':             ('Africa/El_Aaiun', 1679191199, (2023,  3, 19,  2, 59, 59),   3600,     0, '+01', {'fold': 0}),
    'africa_el_aaiun_start_of_dst':            ('Africa/El_Aaiun', 1679191200, (2023,  3, 19,  2,  0,  0),      0, -3600, '+00', {'fold': 1}),
    'africa_el_aaiun_end_of_fold':             ('Africa/El_Aaiun', 1679194799, (2023,  3, 19,  2, 59, 59),      0, -3600, '+00', {'fold': 1}),
    'africa_el_aaiun_after_fold':              ('Africa/El_Aaiun', 1679194800, (2023,  3, 19,  3,  0,  0),      0, -3600, '+00', {}),
    'africa_el_aaiun_during_dst':              ('Africa/El_Aaiun', 1680698096, (2023,  4,  5, 12, 34, 56),      0, -3600, '+00', {}),
    'africa_el_aaiun_end_of_dst':              ('Africa/El_Aaiun', 1682215199, (2023,  4, 23,  1, 59, 59),      0, -3600, '+00', {}),
    'africa_el_aaiun_after_dst':               ('Africa/El_Aaiun', 1682215200, (2023,  4, 23,  3,  0,  0),   3600,     0, '+01', {}),
    'africa_el_aaiun_standard_time':           ('Africa/El_Aaiun', 1692099296, (2023,  8, 15, 12, 34, 56),   3600,     0, '+01', {}),
    'africa_el_aaiun_new_years_eve':           ('Africa/El_Aaiun', 1704063599, (2023, 12, 31, 23, 59, 59),   3600,     0, '+01', {}),
    # Australia/Lord_Howe island changes by only half an hour when transitioning to/from DST
    'australia_lord_howe_new_year':        ('Australia/Lord_Howe', 1672491600, (2023,  1,  1,  0,  0,  0),  39600,  1800, '+11', {}),
    'australia_lord_howe_during_dst':      ('Australia/Lord_Howe', 1676424896, (2023,  2, 15, 12, 34, 56),  39600,  1800, '+11', {}),
    'australia_lord_howe_still_dst':       ('Australia/Lord_Howe', 1680359399, (2023,  4,  2,  1, 29, 59),  39600,  1800, '+11', {}),
    'australia_lord_howe_fold_0':          ('Australia/Lord_Howe', 1680359400, (2023,  4,  2,  1, 30, 00),  39600,  1800, '+11', {'fold': 0}),
    'australia_lord_howe_end_of_dst':      ('Australia/Lord_Howe', 1680361199, (2023,  4,  2,  1, 59, 59),  39600,  1800, '+11', {'fold': 0}),
    'australia_lord_howe_start_of_fold':   ('Australia/Lord_Howe', 1680361200, (2023,  4,  2,  1, 30, 00),  37800,     0, '+1030', {'fold': 1}),
    'australia_lord_howe_end_of_fold':     ('Australia/Lord_Howe', 1680362999, (2023,  4,  2,  1, 59, 59),  37800,     0, '+1030', {'fold': 1}),
    'australia_lord_howe_after_fold':      ('Australia/Lord_Howe', 1680363000, (2023,  4,  2,  2,  0,  0),  37800,     0, '+1030', {}),
    'australia_lord_howe_standard_time':   ('Australia/Lord_Howe', 1689386696, (2023,  7, 15, 12, 34, 56),  37800,     0, '+1030', {}),
    'australia_lord_howe_before_dst':      ('Australia/Lord_Howe', 1696087799, (2023, 10,  1,  1, 59, 59),  37800,     0, '+1030', {}),
    'australia_lord_howe_start_of_dst':    ('Australia/Lord_Howe', 1696087800, (2023, 10,  1,  2, 30,  0),  39600,  1800, '+11', {}),
    'australia_lord_howe_new_years_eve':   ('Australia/Lord_Howe', 1704027599, (2023, 12, 31, 23, 59, 59),  39600,  1800, '+11', {}),
    # Antarctica/Troll station is special in that it's currently the only location to make 2 hour time adjustments twice a year
    'antarctica_troll_new_year':              ('Antarctica/Troll', 1672531200, (2023,  1,  1,  0,  0,  0),      0,     0, '+00', {}),
    'antarctica_troll_standard_time':         ('Antarctica/Troll', 1676464496, (2023,  2, 15, 12, 34, 56),      0,     0, '+00', {}),
    'antarctica_troll_before_dst':            ('Antarctica/Troll', 1679792399, (2023,  3, 26,  0, 59, 59),      0,     0, '+00', {}),
    'antarctica_troll_start_of_dst':          ('Antarctica/Troll', 1679792400, (2023,  3, 26,  3,  0,  0),   7200,  7200, '+02', {}),
    'antarctica_troll_during_dst':            ('Antarctica/Troll', 1689417296, (2023,  7, 15, 12, 34, 56),   7200,  7200, '+02', {}),
    'antarctica_troll_still_dst':             ('Antarctica/Troll', 1698533999, (2023, 10, 29,  0, 59, 59),   7200,  7200, '+02', {}),
    'antarctica_troll_fold_0':                ('Antarctica/Troll', 1698534000, (2023, 10, 29,  1,  0,  0),   7200,  7200, '+02', {'fold': 0}),
    'antarctica_troll_end_of_dst':            ('Antarctica/Troll', 1698541199, (2023, 10, 29,  2, 59, 59),   7200,  7200, '+02', {'fold': 0}),
    'antarctica_troll_start_of_fold':         ('Antarctica/Troll', 1698541200, (2023, 10, 29,  1,  0,  0),      0,     0, '+00', {'fold': 1}),
    'antarctica_troll_end_of_fold':           ('Antarctica/Troll', 1698548399, (2023, 10, 29,  2, 59, 59),      0,     0, '+00', {'fold': 1}),
    'antarctica_troll_after_fold':            ('Antarctica/Troll', 1698548400, (2023, 10, 29,  3,  0,  0),      0,     0, '+00', {}),
    'antarctica_troll_new_years_eve':         ('Antarctica/Troll', 1704067199, (2023, 12, 31, 23, 59, 59),      0,     0, '+00', {}),
    # America/Scoresbysund switches timezone rules at the same instant as entering DST in March 2024 resulting in a net offset change of 0
    'america_scoresbysund_new_year':      ('America/Scoresbysund', 1704070800, (2024,  1,  1,  0,  0,  0),  -3600,     0, '-01', {}),
    'america_scoresbysund_standard_time': ('America/Scoresbysund', 1708004096, (2024,  2, 15, 12, 34, 56),  -3600,     0, '-01', {}),
    'america_scoresbysund_before_dst':    ('America/Scoresbysund', 1711846799, (2024,  3, 30, 23, 59, 59),  -3600,     0, '-01', {}),
    'america_scoresbysund_start_of_dst':  pytest.param(
                                           'America/Scoresbysund', 1711846800, (2024,  3, 31,  0,  0,  0),  -3600,  3600, '-01', {},
                                           # glibc cannot properly handle irregular DST changes, its
                                           # localtime() claiming DST not taking effect until months later
                                           # (the total gmtoff it returns is still correct, though,
                                           # which is sufficient for most practical cases), so we
                                           # mark this parameter set for it to forgo the DST check
                                           marks=pytest.mark.glibc_limitation
    ),
    'america_scoresbysund_during_dst':    ('America/Scoresbysund', 1721050496, (2024,  7, 15, 12, 34, 56),  -3600,  3600, '-01', {}),
    'america_scoresbysund_still_dst':     ('America/Scoresbysund', 1729987199, (2024, 10, 26, 22, 59, 59),  -3600,  3600, '-01', {}),
    'america_scoresbysund_fold_0':        ('America/Scoresbysund', 1729987200, (2024, 10, 26, 23,  0,  0),  -3600,  3600, '-01', {'fold': 0}),
    'america_scoresbysund_end_of_dst':    ('America/Scoresbysund', 1729990799, (2024, 10, 26, 23, 59, 59),  -3600,  3600, '-01', {'fold': 0}),
    'america_scoresbysund_start_of_fold': ('America/Scoresbysund', 1729990800, (2024, 10, 26, 23,  0,  0),  -7200,     0, '-02', {'fold': 1}),
    'america_scoresbysund_end_of_fold':   ('America/Scoresbysund', 1729994399, (2024, 10, 26, 23, 59, 59),  -7200,     0, '-02', {'fold': 1}),
    'america_scoresbysund_after_fold':    ('America/Scoresbysund', 1729994400, (2024, 10, 27,  0,  0,  0),  -7200,     0, '-02', {}),
    'america_scoresbysund_new_years_eve': ('America/Scoresbysund', 1735696799, (2024, 12, 31, 23, 59, 59),  -7200,     0, '-02', {}),
    # Pacific/Kiritimati has no DST and an extreme difference to UTC by +14 h
    'pacific_kiritimati_new_year':          ('Pacific/Kiritimati', 1672480800, (2023,  1,  1,  0,  0,  0),  50400,     0, '+14', {}),
    'pacific_kiritimati_standard_time':     ('Pacific/Kiritimati', 1689374096, (2023,  7, 15, 12, 34, 56),  50400,     0, '+14', {}),
    'pacific_kiritimati_new_years_eve':     ('Pacific/Kiritimati', 1704016799, (2023, 12, 31, 23, 59, 59),  50400,     0, '+14', {}),
    # fmt: on
}


@pytest.mark.parametrize(
    ('key', 'ts', 'tt', 'off', 'dst', 'zone', 'kwds'),
    POINTS_IN_TIME.values(),
    ids=POINTS_IN_TIME.keys(),
)
def test_datetime_tz(
    key: str,
    ts: int,
    tt: Tuple[int, ...],
    off: int,
    dst: int,
    zone: str,
    kwds: Dict[str, int],
    systemtz: tzinfo,
) -> None:
    dt = datetime_tz(*tt, tzinfo=ZoneInfo(key), fold=kwds.get('fold', 0))
    dt = dt.astimezone(systemtz)
    datetime_tz.assert_aware_datetime(dt)
    dt = dt.astimezone(ZoneInfo(key))
    datetime_tz.assert_aware_datetime(dt)
    assert dt.timestamp() == ts
    assert dt.utcoffset() == TimeDelta(seconds=off)
    assert dt.tzname() == zone
    assert dt.dst() == TimeDelta(seconds=dst)


@pytest.mark.parametrize(
    ('key', 'ts', 'tt', 'off', 'dst', 'zone', 'kwds'),
    POINTS_IN_TIME.values(),
    ids=POINTS_IN_TIME.keys(),
)
def test_datetime_tz_fromtimestamp(
    key: str,
    ts: int,
    tt: Tuple[int, ...],
    off: int,
    dst: int,
    zone: str,
    kwds: Dict[str, int],
    systemtz: tzinfo,
) -> None:
    dt = datetime_tz.fromtimestamp(ts, tz=ZoneInfo(key))
    dt = dt.astimezone(systemtz)
    datetime_tz.assert_aware_datetime(dt)
    dt = dt.astimezone(ZoneInfo(key))
    datetime_tz.assert_aware_datetime(dt)
    expected_fold = kwds.get('fold', 0)
    assert dt.fold == expected_fold
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) == tt
    assert dt.utcoffset() == TimeDelta(seconds=off)
    assert dt.tzname() == zone
    assert dt.dst() == TimeDelta(seconds=dst)


@pytest.mark.parametrize(
    ('key', 'ts', 'tt', 'off', 'dst', 'zone', 'kwds'),
    POINTS_IN_TIME.values(),
    ids=POINTS_IN_TIME.keys(),
)
def test_datetime_local(
    key: str,
    ts: int,
    tt: Tuple[int, ...],
    off: int,
    dst: int,
    zone: str,
    kwds: Dict[str, int],
    welldefined_timezone: Callable[[str], ContextManager[ZoneInfo]],
    request: FixtureRequest,
) -> None:
    with welldefined_timezone(key):
        dt = datetime_local(*tt, tzinfo=tz_local, fold=kwds.get('fold', 0))
        assert isinstance(dt.tzinfo, SystemTZ)
        assert dt.timestamp() == ts
        assert dt.utcoffset() == TimeDelta(seconds=off)
        assert dt.tzname() == zone

        if platform.libc_ver()[0] != 'glibc' or not request.node.get_closest_marker(
            'glibc_limitation'
        ):
            assert dt.dst() == TimeDelta(seconds=dst)


@pytest.mark.parametrize(
    ('key', 'ts', 'tt', 'off', 'dst', 'zone', 'kwds'),
    POINTS_IN_TIME.values(),
    ids=POINTS_IN_TIME.keys(),
)
def test_datetime_local_fromtimestamp(
    key: str,
    ts: int,
    tt: Tuple[int, ...],
    off: int,
    dst: int,
    zone: str,
    kwds: Dict[str, int],
    welldefined_timezone: Callable[[str], ContextManager[ZoneInfo]],
    request: FixtureRequest,
) -> None:
    with welldefined_timezone(key):
        dt = datetime_local.fromtimestamp(ts, tz=tz_local)
        assert isinstance(dt.tzinfo, SystemTZ)
        expected_fold = kwds.get('fold', 0)
        assert dt.fold == expected_fold
        assert (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) == tt
        assert dt.utcoffset() == TimeDelta(seconds=off)
        assert dt.tzname() == zone

        if platform.libc_ver()[0] != 'glibc' or not request.node.get_closest_marker(
            'glibc_limitation'
        ):
            assert dt.dst() == TimeDelta(seconds=dst)


if __name__ == '__main__':
    pytest.main()
