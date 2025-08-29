# Heliclockter

[![PyPI](https://img.shields.io/pypi/v/heliclockter)](https://pypi.org/project/heliclockter/)
[![License](https://img.shields.io/github/license/channable/heliclockter)](https://github.com/channable/heliclockter/blob/master/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/heliclockter)](https://pypi.org/project/heliclockter/)

**Timezone-aware datetimes for Python that just work.**

`heliclockter` is a timezone-aware datetime library that ensures your timestamps are always timezone-aware. It's statically type checkable and runtime enforceable.

## Installation

```bash
pip install heliclockter
```

## Quick Start

```python
from heliclockter import datetime_utc, datetime_local, datetime_tz

# UTC datetime
utc_now = datetime_utc.now()
# datetime_utc(2022, 11, 4, 15, 28, 10, 478176, tzinfo=zoneinfo.ZoneInfo(key='UTC'))

# Local timezone datetime  
local_now = datetime_local.now()

# Any timezone datetime
from zoneinfo import ZoneInfo
paris_tz = datetime_tz.now(tz=ZoneInfo("Europe/Paris"))

# Create a timestamp 2 hours in the future
future = datetime_utc.future(hours=2)

# Parse strings (naive timestamps assumed UTC)
parsed = datetime_utc.strptime('2022-11-04T15:49:29', '%Y-%m-%dT%H:%M:%S')
```

## Why heliclockter?

Python's standard `datetime` allows "naive" datetimes without timezone info, leading to bugs when:
- Mixing naive and aware datetimes (causes runtime TypeErrors)
- Deploying across different timezones
- Forgetting to add `tzinfo` when creating datetimes

`heliclockter` enforces timezone-aware datetimes at the type level, catching these issues before production.

## Key Features

- **Always timezone-aware** - No more naive datetime accidents
- **Type safe** - Full typing support for better IDE experience  
- **Zero dependencies** - Lightweight, uses only standard library
- **Pydantic support** - Automatic integration when Pydantic is installed
- **Python 3.10+** - Modern Python for modern applications

## Examples

### Timezone conversions

```python
from heliclockter import datetime_utc, datetime_tz
from zoneinfo import ZoneInfo

# Start with UTC
utc_time = datetime_utc.now()

# To convert to different timezones, create custom classes
class datetime_tokyo(datetime_tz):
    assumed_timezone_for_timezone_naive_input = ZoneInfo('Asia/Tokyo')

class datetime_ny(datetime_tz):
    assumed_timezone_for_timezone_naive_input = ZoneInfo('America/New_York')

# Convert using from_datetime
tokyo_time = datetime_tokyo.from_datetime(utc_time)
ny_time = datetime_ny.from_datetime(utc_time)
```

### Handling naive datetimes

```python
from heliclockter import datetime_utc, datetime_tz
from datetime import datetime

# datetime_utc assumes UTC for naive inputs
naive_dt = datetime(2022, 11, 4, 15, 30, 0)
utc_dt = datetime_utc.from_datetime(naive_dt)  # OK - assumes UTC

# datetime_tz requires explicit timezone
try:
    tz_dt = datetime_tz.from_datetime(naive_dt)  # Raises error
except Exception as e:
    print(e)  # "Cannot create aware datetime from naive if no tz is assumed"
```

### Custom timezone classes

```python
from zoneinfo import ZoneInfo
from heliclockter import datetime_tz

class datetime_cet(datetime_tz):
    """Datetime guaranteed to be in CET timezone."""
    assumed_timezone_for_timezone_naive_input = ZoneInfo('CET')

# Parse naive timestamps as CET
aware_dt = datetime_cet.strptime('2022-11-04T15:49:29', '%Y-%m-%dT%H:%M:%S')
```

### Type safety with mypy

```python
from heliclockter import datetime_utc, datetime_local

def schedule_task(when: datetime_utc) -> None:
    """Schedule a task at a specific UTC time."""
    print(f"Task scheduled for {when.isoformat()}")

# Type checker ensures only UTC datetimes are passed
utc_time = datetime_utc.now()
schedule_task(utc_time)  # ✓ OK

local_time = datetime_local.now()  
schedule_task(local_time)  # ✗ Type error
```

## API Overview

### Core Classes

- **`datetime_tz`** - Base class for timezone-aware datetimes
- **`datetime_utc`** - Always UTC (naive inputs assumed UTC)
- **`datetime_local`** - Always local timezone (naive inputs assumed local)

### Key Methods

- `now()` - Current time
- `from_datetime()` - Convert from standard datetime
- `strptime()` - Parse string to datetime
- `future()/past()` - Create relative timestamps

## About the Name

`heliclockter` is a portmanteau of "clock" and "helicopter". Like a [helicopter parent](https://en.wikipedia.org/wiki/Helicopter_parent), it strictly supervises your datetime handling, ensuring you never make timezone mistakes.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/channable/heliclockter/blob/master/CONTRIBUTING.md).

## License

BSD 3-Clause License. See [LICENSE](https://github.com/channable/heliclockter/blob/master/LICENSE).