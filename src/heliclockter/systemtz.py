from __future__ import annotations as __annotations

import datetime as _datetime
import time as _time
from calendar import timegm as _timegm

try:
    import tzlocal as _tzlocal
except ImportError:
    _tzlocal = None

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime as DateTime
    from datetime import timedelta as TimeDelta
    from typing import Any, List, Optional, Tuple, Type


class SystemTZ(_datetime.tzinfo):
    """
    A `tzinfo` subclass modeling the system timezone.

    This class allows `datetime` objects to be created containing the local
    timezone information. It inherits from `tzinfo` and is compatible with
    `ZoneInfo` objects.

    You can provide a custom `datetime.datetime` compatible class during
    instantiation to have it return instances of that class rather than
    ordinary `datetime.datetime` objects.

    You can also specify a name for the instance that will be used as return
    values for `obj.__str__()` and `obj.__repr__()` instead of the defaults.

    The key methods are:

    - `fromutc()` - Convert a UTC datetime object to a local datetime object.
    - `utcoffset()` - Return the timezone offset.
    - `tzname()` - Return the timezone name.
    - `dst()` - Return the daylight saving offset.

    The methods pull timezone information from the `time` module rather than
    taking the information as arguments.

    Example:
        >>> tz = SystemTZ()
        >>> str(tz)
        '<SystemTZ>'
    """

    def __init__(
        self,
        datetime_like_cls: Type[DateTime] = _datetime.datetime,
        *args: Any,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._DateTime = datetime_like_cls
        self._unix_epoch = self._DateTime(1970, 1, 1, tzinfo=_datetime.UTC)
        self._zero_delta = self._unix_epoch - self._unix_epoch
        self._TimeDelta = type(self._zero_delta)
        self._name = str(name) if name else None

    def __str__(self) -> str:
        if self._name:
            return self._name
        return '<' + self.__class__.__name__ + '>'

    def __repr__(self) -> str:
        if self._name:
            return self._name
        args = []  # type: List[str]
        if self._DateTime is not _datetime.datetime:
            args.append(self._DateTime.__module__ + '.' + self._DateTime.__qualname__)
        return '{}({})'.format(self.__class__.__qualname__, ', '.join(args))

    def __eq__(self, other: Any) -> bool:
        if other.__class__ is not self.__class__:
            return NotImplemented

        return other._DateTime is self._DateTime

    @property
    def key(self) -> Optional[str]:
        """Return the key of the local timezone.

        This will return the name of the local timezone, like 'Europe/Amsterdam',
        if the tzlocal module is available. Otherwise it will return None.

        Example:
            >>> os.environ['TZ'] = 'Australia/Sydney'
            >>> time.tzset()
            >>> tz = SystemTZ()
            >>> tz.key
            'Australia/Sydney'
        """
        return _tzlocal.get_localzone_name() if _tzlocal else None

    def fromutc(self, dt: DateTime) -> DateTime:
        """Convert a UTC datetime object to a local datetime object.

        Takes a datetime object that is in UTC time and converts it to the
        local timezone, accounting for daylight savings time if necessary.

        Parameters:
            dt (datetime.datetime): The UTC datetime object to convert.

        Returns:
            datetime.datetime: The datetime converted to the local timezone.

        Example:
            >>> os.environ['TZ'] = 'Europe/Warsaw'
            >>> time.tzset()
            >>> utc_dt = datetime.datetime(2022, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
            >>> tz = SystemTZ()
            >>> local_dt = utc_dt.astimezone(tz)
            >>> local_dt
            datetime.datetime(2022, 1, 1, 13, 0, tzinfo=SystemTZ())
        """
        assert dt.tzinfo is self

        secs = _timegm((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
        t = _time.localtime(secs)
        args = t[:6]
        if not hasattr(self._DateTime, 'fold'):
            return self._DateTime(*args, microsecond=dt.microsecond, tzinfo=self)

        if t.tm_isdst < 0:
            return self._DateTime(*args, microsecond=dt.microsecond, tzinfo=self, fold=0)
        secs0 = _time.mktime((*t[:8], not t.tm_isdst))
        if secs0 >= secs:
            return self._DateTime(*args, microsecond=dt.microsecond, tzinfo=self, fold=0)
        t0 = _time.localtime(secs0)
        return self._DateTime(
            *args, microsecond=dt.microsecond, tzinfo=self, fold=int(t.tm_gmtoff < t0.tm_gmtoff)
        )

    def _mktime(self, dt: DateTime) -> Tuple[_time.struct_time, float]:
        assert dt.tzinfo is self
        secs = _time.mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 1, -1))
        t = _time.localtime(secs)
        if not hasattr(dt, 'fold'):
            return t, secs + dt.microsecond / 1_000_000

        if t.tm_isdst < 0:
            return t, secs + dt.microsecond / 1_000_000

        secs0 = _time.mktime((*t[:8], not t.tm_isdst))
        if secs0 == secs:
            return t, secs + dt.microsecond / 1_000_000

        t0 = _time.localtime(secs0)
        if t.tm_gmtoff == t0.tm_gmtoff:
            return t, secs + dt.microsecond / 1_000_000

        if (t.tm_gmtoff > t0.tm_gmtoff) ^ bool(dt.fold):
            return t, secs + dt.microsecond / 1_000_000
        return t0, secs0 + dt.microsecond / 1_000_000

    def utcoffset(self, dt: Optional[DateTime]) -> TimeDelta:
        """Return the timezone offset for the given datetime.

        Return the offset for the given datetime by
        calculating the offset between it and UTC.
        If dt is None, return the offset for the current time instead.

        Example:
            >>> os.environ['TZ'] = 'Europe/Amsterdam'
            >>> time.tzset()
            >>> tz = SystemTZ()
            >>> dt = datetime.datetime(2022, 1, 1, 12, 0, 0, tzinfo=tz)
            >>> tz.utcoffset(dt)
            datetime.timedelta(seconds=3600)
        """
        # TODO: investigate if we have to round to whole minutes for Python < 3.6
        if dt is None:
            return self._TimeDelta(seconds=_time.localtime().tm_gmtoff)

        return self._TimeDelta(seconds=self._mktime(dt)[0].tm_gmtoff)

    def tzname(self, dt: Optional[DateTime]) -> str:
        """Return the timezone name for the given datetime.

        Return the name of the timezone for the given datetime,
        unless dt is None, in which case return the name for the current time.

        Example:
            >>> os.environ['TZ'] = 'America/New_York'
            >>> time.tzset()
            >>> tz = SystemTZ()
            >>> dt = datetime.datetime(2022, 1, 1, 12, 0, 0, tzinfo=tz)
            >>> tz.tzname(dt)
            'EST'
        """
        if dt is None:
            return _time.localtime().tm_zone

        return self._mktime(dt)[0].tm_zone

    def dst(self, dt: Optional[DateTime]) -> Optional[TimeDelta]:
        """Return daylight saving time offset for given datetime.

        This method checks whether DST is in effect for a given datetime. If no
        datetime is provided, it defaults to the current local time. If DST is
        not in effect, it returns a zero duration. If DST is in effect, it
        calculates the DST offset and returns it as a `datetime.timedelta`.

        Example:
            >>> os.environ['TZ'] = 'Australia/Melbourne'
            >>> time.tzset()
            >>> tz = SystemTZ()
            >>> dt = datetime.datetime(2022, 1, 1, 12, 0, 0, tzinfo=tz)
            >>> tz.dst(dt)
            datetime.timedelta(seconds=3600)
        """
        if dt is None:
            secs = _time.time()
            t = _time.localtime(secs)
        else:
            t, secs = self._mktime(dt)
        if t.tm_isdst < 0:
            return None

        if not t.tm_isdst:
            return self._zero_delta
        secs0 = _time.mktime((*t[:8], 0)) + secs % 1
        dstoff = round(secs0 - secs)
        # TODO: investigate if we have to round to whole minutes for Python < 3.6
        return self._TimeDelta(seconds=dstoff)
