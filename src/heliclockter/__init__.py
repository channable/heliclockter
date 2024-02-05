from __future__ import annotations

import datetime as _datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Iterator,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)
from zoneinfo import ZoneInfo

# We don't require pydantic as a dependency, but add validate logic if it exists.
# `parse_datetime` doesn't exist in Pydantic v2, so `PYDANTIC_V1_AVAILABLE is False` when
# pydantic v2 is installed.
try:
    from pydantic.datetime_parse import parse_datetime

    PYDANTIC_V1_AVAILABLE = True
except ImportError:
    PYDANTIC_V1_AVAILABLE = False

try:
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic_core import CoreSchema, core_schema
    from pydantic.json_schema import JsonSchemaValue
    from pydantic.v1.datetime_parse import parse_datetime

    PYDANTIC_V2_AVAILABLE = True
except ImportError:
    PYDANTIC_V2_AVAILABLE = False


# `date` and `timedelta` are exposed for your convenience in case this module is used in combination
# with an import linter that prohibits importing the `datetime` package anywhere.
date = _datetime.date
timedelta = _datetime.timedelta


tz_local = cast(ZoneInfo, _datetime.datetime.now().astimezone().tzinfo)

__version__ = '1.3.0'


DateTimeTzT = TypeVar('DateTimeTzT', bound='datetime_tz')
IntFloat = Union[int, float]


class DatetimeTzError(ValueError):
    """
    An error with the input value when trying to create or mutate a `datetime_tz` instance.
    """


class datetime_tz(_datetime.datetime):
    """
    A `datetime_tz` is just a `datetime.datetime` but which is guaranteed to be timezone aware.
    """

    assumed_timezone_for_timezone_naive_input: ClassVar[Optional[ZoneInfo]] = None

    if TYPE_CHECKING:

        def __init__(
            self,
            year: int,
            month: int,
            day: int,
            hour: int = 0,
            minute: int = 0,
            second: int = 0,
            microsecond: int = 0,
            *,
            tzinfo: _datetime.tzinfo,
            fold: int = 0,
        ) -> None:
            pass

    else:

        def __init__(  # pylint: disable=unused-argument
            self,
            year: int,
            month: int,
            day: int,
            hour: int = 0,
            minute: int = 0,
            second: int = 0,
            microsecond: int = 0,
            tzinfo: _datetime.tzinfo = None,
            fold: int = 0,
        ) -> None:
            msg = f'{self.__class__} must have a timezone'
            assert tzinfo is not None and self.tzinfo is not None, msg
            tz_expected = self.assumed_timezone_for_timezone_naive_input or tzinfo

            msg = f'{self.__class__} got invalid timezone {self.tzinfo!r}, expected {tz_expected!r}'
            assert self.tzinfo == tz_expected, msg

            self.assert_aware_datetime(self)

    if PYDANTIC_V1_AVAILABLE or PYDANTIC_V2_AVAILABLE:

        @classmethod
        def __get_validators__(cls) -> Iterator[Callable[[Any], Optional[datetime_tz]]]:
            yield cls._validate

        @classmethod
        def _validate(cls: Type[DateTimeTzT], v: Any) -> Optional[DateTimeTzT]:
            if v is None:
                return None

            dt = v if isinstance(v, _datetime.datetime) else parse_datetime(v)
            return cls.from_datetime(dt)

    if PYDANTIC_V2_AVAILABLE:

        @classmethod
        def __get_pydantic_core_schema__(cls, _: Any, __: GetCoreSchemaHandler) -> CoreSchema:
            from_datetime_schema = core_schema.chain_schema(
                [
                    core_schema.datetime_schema(),
                    core_schema.no_info_plain_validator_function(cls.from_datetime),
                ]
            )

            return core_schema.json_or_python_schema(
                json_schema=from_datetime_schema,
                python_schema=core_schema.union_schema(
                    [
                        core_schema.is_instance_schema(datetime_tz),
                        from_datetime_schema,
                    ]
                ),
            )

        @classmethod
        def __get_pydantic_json_schema__(
            cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return handler(core_schema.datetime_schema())

    @classmethod
    def from_datetime(cls: Type[DateTimeTzT], dt: _datetime.datetime) -> DateTimeTzT:
        # Case datetime is naive and there is no assumed timezone.
        if dt.tzinfo is None and cls.assumed_timezone_for_timezone_naive_input is None:
            raise DatetimeTzError('Cannot create aware datetime from naive if no tz is assumed')

        # Case: datetime is naive, but the timezone is assumed.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls.assumed_timezone_for_timezone_naive_input)

        # Case: datetime is aware and the timezone is assumed, enforce that timezone.
        elif (assumed_tz := cls.assumed_timezone_for_timezone_naive_input) is not None:
            # Case: when `assumed_timezone_for_timezone_naive_input` is declared on the input
            # dt it cannot be instantiated in a different timezone.
            if getattr(dt, 'assumed_timezone_for_timezone_naive_input', None) is not None:
                dt = _datetime.datetime(
                    year=dt.year,
                    month=dt.month,
                    day=dt.day,
                    hour=dt.hour,
                    minute=dt.minute,
                    second=dt.second,
                    microsecond=dt.microsecond,
                    tzinfo=dt.tzinfo,
                    fold=dt.fold,
                ).astimezone(tz=assumed_tz)

            else:
                dt = dt.astimezone(assumed_tz)

        cls.assert_aware_datetime(dt)
        return cls(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            microsecond=dt.microsecond,
            tzinfo=dt.tzinfo,  # type: ignore[arg-type]
            fold=dt.fold,
        )

    @classmethod
    def now(cls: Type[DateTimeTzT], tz: Optional[_datetime.tzinfo] = None) -> DateTimeTzT:
        tz = cls.assumed_timezone_for_timezone_naive_input or tz
        if tz is None:
            raise DatetimeTzError(
                'Must override assumed_timezone_for_timezone_naive_input '
                'or give a timezone when calling now'
            )
        return cls.from_datetime(_datetime.datetime.now(tz))

    @classmethod
    def future(
        cls: Type[DateTimeTzT],
        weeks: IntFloat = 0,
        days: IntFloat = 0,
        hours: IntFloat = 0,
        minutes: IntFloat = 0,
        seconds: IntFloat = 0,
        milliseconds: IntFloat = 0,
        microseconds: IntFloat = 0,
        tz: Optional[ZoneInfo] = None,
    ) -> DateTimeTzT:
        delta = timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds,
            microseconds=microseconds,
        )
        return cls.now(tz=tz) + delta

    @classmethod
    def past(
        cls: Type[DateTimeTzT],
        weeks: IntFloat = 0,
        days: IntFloat = 0,
        hours: IntFloat = 0,
        minutes: IntFloat = 0,
        seconds: IntFloat = 0,
        milliseconds: IntFloat = 0,
        microseconds: IntFloat = 0,
        tz: Optional[ZoneInfo] = None,
    ) -> DateTimeTzT:
        delta = timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds,
            microseconds=microseconds,
        )
        return cls.now(tz=tz) - delta

    @classmethod
    def fromisoformat(cls: Type[DateTimeTzT], date_string: str) -> DateTimeTzT:
        return cls.from_datetime(_datetime.datetime.fromisoformat(date_string))

    @classmethod
    def strptime(cls: Type[DateTimeTzT], date_string: str, __format: str) -> DateTimeTzT:
        dt = _datetime.datetime.strptime(date_string, __format)
        return cls.from_datetime(dt)

    @staticmethod
    def assert_aware_datetime(dt: _datetime.datetime) -> None:
        """
        Check that the given `datetime.datetime` instance is timezone aware. Throws
        an AssertionError otherwise.
        """
        assert dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

    def __deepcopy__(self: DateTimeTzT, memodict: object) -> DateTimeTzT:
        """
        Deepcopy does not natively work with the __init__ we add to this class
        for extra assertions. Therefore, we override it.
        """
        return self.__class__(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
            tzinfo=self.tzinfo,  # type: ignore[arg-type]
            fold=self.fold,
        )


class datetime_utc(datetime_tz):
    """
    A `datetime_utc` is a `datetime_tz` but which is guaranteed to be in the UTC+0 timezone.
    """

    assumed_timezone_for_timezone_naive_input = ZoneInfo('UTC')

    @classmethod
    def fromtimestamp(cls, timestamp: float) -> datetime_utc:  # type: ignore[override]  # pylint: disable=arguments-differ
        """
        Parses a timestamp to a timezone aware datetime.
        """
        return cls.from_datetime(_datetime.datetime.fromtimestamp(timestamp, tz=ZoneInfo('UTC')))


class datetime_local(datetime_tz):
    """
    A `datetime_local` is a `datetime_tz` but which is guaranteed to be in the local timezone.
    """

    assumed_timezone_for_timezone_naive_input = tz_local
