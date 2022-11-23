Heliclockter
=======

`heliclockter` is a robust way of dealing with datetimes and timestamps in python. It is statically
type checkable as well as runtime enforceable and integrates with [pydantic][pydantic].

The library exposes 3 classes:

- `datetime_tz`, a datetime ensured to be timezone-aware.
- `datetime_local`, a datetime ensured to be timezone-aware in the local timezone.
- `datetime_utc`, a datetime ensured to be timezone-aware in the UTC+0 timezone.

as well as various utilities to instantiate, mutate and serialize those classes.

See our [announcement post][announcement] for a more background on why we wrote `heliclockter`.

[pydantic]: https://github.com/pydantic/pydantic
[announcement]: https://www.channable.com/tech/heliclockter-timezone-aware-datetimes-in-python

Examples
-------

Say you want to create a timestamp of the current time in the UTC+0 timezone.

```python
from heliclockter import datetime_utc

now = datetime_utc.now()
# datetime_utc(2022, 11, 4, 15, 28, 10, 478176, tzinfo=zoneinfo.ZoneInfo(key='UTC'))
```

Or imagine you want to create a timestamp 2 hours in the future from now:

```python
from heliclockter import datetime_utc

two_hours_from_now = datetime_utc.future(hours=2)
# datetime_utc(2022, 11, 4, 17, 28, 52, 478176, tzinfo=zoneinfo.ZoneInfo(key='UTC'))
```

Features
--------

* Runtime enforcable timezone-aware datetimes
* Utilities for instantiating, mutating and serializing timezone-aware datetimes
* Statically type check-ble
* Pydantic integration
* Extensive test suite
* No third party dependencies

Installation
------------

To install `heliclockter`, simply: 

    $ pip install heliclockter

More examples
-------------

Imagine you want to parse a JSON response from a third party API which includes a timestamp, and you
want to handle the timestamp in the UTC+0 timezone regardless of how the 3rd party relays it. This 
can easily be done with `pydantic` and `heliclockter`:

```python
import requests
from pydantic import BaseModel
from heliclockter import datetime_utc


class ApiResponse(BaseModel):
    current_time: datetime_utc


def get_response() -> ApiResponse:
    response = requests.get('https://some-api.com/time')
    return ApiResponse.parse_obj(response.json())
```

The returned `ApiResponse` instance is guaranteed to have parsed the `current_time` attribute 
as UTC+0 no matter how the api provided the timestamp. If no timezone information is provided, 
it will be assumed to be UTC+0.

Expanding the module can be done with little effort, by creating a new class that inherits `datetime_tz`:

```python
from zoneinfo import ZoneInfo
from heliclockter import datetime_tz


class datetime_cet(datetime_tz):
    """
    A `datetime_cet` is a `datetime_tz` but which is guaranteed to be in the 'CET' timezone.
    """

    assumed_timezone_for_timezone_naive_input = ZoneInfo('CET')
```

If you have a timestamp which is naive, *but* the timezone in which it is made is known to you,
you can easily create a `datetime_tz` instance using your own defined classes:

```python
aware_dt = datetime_cet.strptime('2022-11-04T15:49:29', '%Y-%m-%dT%H:%M:%S')
# datetime_cet(2022, 11, 4, 15, 49, 29, tzinfo=zoneinfo.ZoneInfo(key='CET'))
```

About the name
--------------

`heliclockter` is a word play of "clock" and "helicopter". The module aims to guide the user and help them make little to no mistakes when handling datetimes, just like a [helicopter parent](https://en.wikipedia.org/wiki/Helicopter_parent) strictly supervises their children.