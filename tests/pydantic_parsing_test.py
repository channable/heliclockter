from datetime import datetime, timezone
from typing import Union
from zoneinfo import ZoneInfo

import pytest
from parameterized import parameterized  # type: ignore[import-untyped]
from pydantic import BaseModel, ValidationError

from heliclockter import DateTimeTzT, datetime_local, datetime_tz, datetime_utc, timedelta

from tests.shared import datetime_cet


class DatetimeTZModel(BaseModel):
    dt: datetime_tz


class DatetimeUTCModel(BaseModel):
    dt: datetime_utc


class DatetimeCETModel(BaseModel):
    dt: datetime_cet


class DatetimeLocalModel(BaseModel):
    dt: datetime_local


class DatetimeDefaultObject(BaseModel):
    dt_now: datetime_tz = datetime_utc.now()
    dt: str = datetime_utc.future(days=120).isoformat()


TestModelT = Union[DatetimeTZModel, DatetimeUTCModel, DatetimeCETModel]


@parameterized.expand(
    [
        # UTC tests
        (
            '2021-01-10T10:00:00',
            datetime_utc(2021, 1, 10, 10, 00, 00, tzinfo=ZoneInfo('UTC')),
            DatetimeUTCModel,
        ),
        (
            '2021-01-10T10:00:00+04:00',
            datetime_utc(2021, 1, 10, 6, 00, 00, tzinfo=ZoneInfo('UTC')),
            DatetimeUTCModel,
        ),
        (
            '2021-01-10T10:00:00+00:00',
            datetime_utc(2021, 1, 10, 10, 00, 00, tzinfo=ZoneInfo('UTC')),
            DatetimeUTCModel,
        ),
        (
            '2021-01-10T10:00:00-04:00',
            datetime_utc(2021, 1, 10, 14, 00, 00, tzinfo=ZoneInfo('UTC')),
            DatetimeUTCModel,
        ),
        # TZ tests
        (
            '2021-01-10T10:00:00+04:00',
            datetime_tz(2021, 1, 10, 10, 0, tzinfo=timezone(timedelta(hours=4))),
            DatetimeTZModel,
        ),
        (
            '2021-01-10T10:00:00-04:00',
            datetime_tz(2021, 1, 10, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
            DatetimeTZModel,
        ),
        # CET tests
        (
            '2021-01-10T10:00:00',
            datetime_cet(2021, 1, 10, 10, 00, 00, tzinfo=ZoneInfo('CET')),
            DatetimeCETModel,
        ),
        (
            '2021-01-10T10:00:00+04:00',
            datetime_cet(2021, 1, 10, 7, 00, 00, tzinfo=ZoneInfo('CET')),
            DatetimeCETModel,
        ),
        (
            '2021-01-10T10:00:00+00:00',
            datetime_cet(2021, 1, 10, 11, 00, 00, tzinfo=ZoneInfo('CET')),
            DatetimeCETModel,
        ),
        (
            '2021-01-10T10:00:00-04:00',
            datetime_cet(2021, 1, 10, 15, 00, 00, tzinfo=ZoneInfo('CET')),
            DatetimeCETModel,
        ),
    ]
)
def test_datetime_parsing(test_str: str, expectation: DateTimeTzT, model: TestModelT) -> None:
    parsed_model = model.model_validate({'dt': test_str})
    assert isinstance(parsed_model.dt, type(expectation))
    assert parsed_model.dt == expectation


def test_datetime_local_parsing() -> None:
    parsed_model = DatetimeLocalModel.model_validate({'dt': '2021-01-10T10:00:00-04:00'})
    assert isinstance(parsed_model.dt, datetime_local)


def test_create_default_pydantic_field() -> None:
    obj = DatetimeDefaultObject()
    assert obj.dt
    assert obj.dt_now


def test_parse_datetime_utc_as_datetime_tz() -> None:
    obj = DatetimeDefaultObject(dt_now=datetime_utc.now())
    assert isinstance(obj.dt_now, datetime_tz)


def test_parse_datetime_tz_without_timezone() -> None:
    with pytest.raises(ValidationError):
        DatetimeTZModel.model_validate({'dt': '2021-01-10T10:00:00'})


def test_parse_datetime_instance() -> None:
    dt = datetime(2021, 1, 10, 10, 0, 0, tzinfo=ZoneInfo('UTC'))
    DatetimeTZModel.model_validate({'dt': dt})

    parsed_tz_model = DatetimeTZModel(dt=dt)  # type: ignore[arg-type]
    assert isinstance(parsed_tz_model.dt, datetime_tz)

    parsed_utc_model = DatetimeUTCModel(dt=dt)  # type: ignore[arg-type]
    assert isinstance(parsed_utc_model.dt, datetime_utc)
