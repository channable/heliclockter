from zoneinfo import ZoneInfo

from pydantic import BaseModel

from heliclockter import datetime_tz


class DatetimeTZModel(BaseModel):
    dt: datetime_tz


def test_pydantic_serialization() -> None:
    obj = DatetimeTZModel(dt=datetime_tz(2021, 1, 10, 10, 0, tzinfo=ZoneInfo('UTC')))

    assert obj.model_dump_json() == '{"dt":"2021-01-10T10:00:00Z"}'
