# pylint: disable=import-outside-toplevel
from __future__ import annotations

import datetime as _datetime
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# `date` and `timedelta` are exposed for your convenience in case this module is used in combination
# with an import linter that prohibits importing the `datetime` package anywhere.
date = _datetime.date
timedelta = _datetime.timedelta


tz_local = cast("ZoneInfo", _datetime.datetime.now().astimezone().tzinfo)

__version__ = "3.0.1"


DateTimeTzT = TypeVar("DateTimeTzT", bound="datetime_tz")
IntFloat = int | float


class DatetimeTzError(ValueError):
    """
    An error with the input value when trying to create or mutate a `datetime_tz` instance.
    """


class datetime_tz(_datetime.datetime):
    """
    A `datetime_tz` is just a `datetime.datetime` but which is guaranteed to be timezone aware.
    """

    assumed_timezone_for_timezone_naive_input: ClassVar[ZoneInfo | None] = None

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
            month: int = None,
            day: int = None,
            hour: int = 0,
            minute: int = 0,
            second: int = 0,
            microsecond: int = 0,
            tzinfo: _datetime.tzinfo = None,
            fold: int = 0,
        ) -> None:
            msg = f"{self.__class__} must have a timezone"
            assert self.tzinfo is not None, msg
            tz_expected = self.assumed_timezone_for_timezone_naive_input or self.tzinfo

            msg = f"{self.__class__} got invalid timezone {self.tzinfo!r}, expected {tz_expected!r}"
            assert self.tzinfo == tz_expected, msg

            self.assert_aware_datetime(self)

    # We don't require pydantic as a dependency, but add validate logic if it exists.
    try:
        import pydantic

        # To avoid using heliclockter from a `pydantic.v1` context, we raise an exception
        @classmethod
        def __get_validators__(cls) -> Iterator[Callable[[Any], datetime_tz | None]]:
            raise RuntimeError(
                "heliclockter 3.x and higher do not support Pydantic v1. "
                "See the README for more information about compatibility."
            )

        if pydantic.__version__[0] != "2":
            raise RuntimeError("Unexpected Pydantic version, expected 2.x")

        if TYPE_CHECKING:
            from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
            from pydantic.json_schema import JsonSchemaValue
            from pydantic_core import CoreSchema

        @classmethod
        def __get_pydantic_core_schema__(cls, _: Any, __: GetCoreSchemaHandler) -> CoreSchema:
            from pydantic_core import core_schema

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
            cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            from pydantic_core import core_schema

            return handler(core_schema.datetime_schema())

    except ImportError:
        pass

    @classmethod
    def from_datetime(cls: type[DateTimeTzT], dt: _datetime.datetime) -> DateTimeTzT:
        # Case datetime is naive and there is no assumed timezone.
        if dt.tzinfo is None and cls.assumed_timezone_for_timezone_naive_input is None:
            raise DatetimeTzError("Cannot create aware datetime from naive if no tz is assumed")

        # Case: datetime is naive, but the timezone is assumed.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls.assumed_timezone_for_timezone_naive_input)

        # Case: datetime is aware and the timezone is assumed, enforce that timezone.
        elif (assumed_tz := cls.assumed_timezone_for_timezone_naive_input) is not None:
            # Case: when `assumed_timezone_for_timezone_naive_input` is declared on the input
            # dt it cannot be instantiated in a different timezone.
            if getattr(dt, "assumed_timezone_for_timezone_naive_input", None) is not None:
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
    def now(cls: type[DateTimeTzT], tz: _datetime.tzinfo | None = None) -> DateTimeTzT:
        tz = cls.assumed_timezone_for_timezone_naive_input or tz
        if tz is None:
            raise DatetimeTzError(
                "Must override assumed_timezone_for_timezone_naive_input "
                "or give a timezone when calling now"
            )
        return cls.from_datetime(_datetime.datetime.now(tz))

    @classmethod
    def future(
        cls: type[DateTimeTzT],
        weeks: IntFloat = 0,
        days: IntFloat = 0,
        hours: IntFloat = 0,
        minutes: IntFloat = 0,
        seconds: IntFloat = 0,
        milliseconds: IntFloat = 0,
        microseconds: IntFloat = 0,
        tz: ZoneInfo | None = None,
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
        cls: type[DateTimeTzT],
        weeks: IntFloat = 0,
        days: IntFloat = 0,
        hours: IntFloat = 0,
        minutes: IntFloat = 0,
        seconds: IntFloat = 0,
        milliseconds: IntFloat = 0,
        microseconds: IntFloat = 0,
        tz: ZoneInfo | None = None,
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
    def fromisoformat(cls: type[DateTimeTzT], date_string: str) -> DateTimeTzT:
        return cls.from_datetime(_datetime.datetime.fromisoformat(date_string))

    @classmethod
    def strptime(cls: type[DateTimeTzT], date_string: str, __format: str) -> DateTimeTzT:
        dt = _datetime.datetime.strptime(date_string, __format)
        return cls.from_datetime(dt)

    @staticmethod
    def assert_aware_datetime(dt: _datetime.datetime) -> None:
        """
        Check that the given `datetime.datetime` instance is timezone aware. Throws
        an AssertionError otherwise.
        """
        assert dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

    def astimezone(self, tz: _datetime.tzinfo | None = None) -> datetime_tz:
        """
        Return a datetime_tz object with the same datetime data but in the specified timezone.
        Uses local timezone if no timezone is provided.
        """
        if tz is None:
            tz = tz_local
        if tz is self.tzinfo:
            return self
        return datetime_tz.fromtimestamp(self.timestamp(), tz=tz)

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

    assumed_timezone_for_timezone_naive_input = ZoneInfo("UTC")

    @classmethod
    def fromtimestamp(cls, timestamp: float) -> datetime_utc:  # type: ignore[override]  # pylint: disable=arguments-differ
        """
        Parses a timestamp to a timezone aware datetime.
        """
        return cls.from_datetime(_datetime.datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")))


class datetime_local(datetime_tz):
    """
    A `datetime_local` is a `datetime_tz` but which is guaranteed to be in the local timezone.
    """

    assumed_timezone_for_timezone_naive_input = tz_local
