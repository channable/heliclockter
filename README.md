# Heliclockter

[![PyPI](https://img.shields.io/pypi/v/heliclockter)](https://pypi.org/project/heliclockter/)
[![License](https://img.shields.io/github/license/channable/heliclockter)](https://github.com/channable/heliclockter/blob/master/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/heliclockter)](https://pypi.org/project/heliclockter/)

**Timezone-aware datetimes for Python that just work.**

`heliclockter` is a powerful timezone-aware datetime library that ensures your timestamps are always timezone-aware. It's statically type checkable, runtime enforceable, and integrates seamlessly with [pydantic](https://github.com/pydantic/pydantic).

## Table of Contents

- [Why heliclockter?](#why-heliclockter)
- [Quickstart](#quickstart)
- [Features](#features)
- [Installation](#installation)
- [Examples](#examples)
  - [Working with different timezones](#working-with-different-timezones)
  - [Real-World Use Cases](#real-world-use-cases)
  - [Parsing and Pydantic integration](#parsing-and-pydantic-integration)
  - [String parsing with strptime](#string-parsing-with-strptime)
  - [Timezone conversions](#timezone-conversions)
  - [Handling DST transitions](#handling-dst-transitions)
  - [Error handling](#error-handling)
- [API Reference](#api-reference)
- [Advanced Usage](#advanced-usage)
  - [Type Hints and Static Analysis](#type-hints-and-static-analysis)
  - [Creating custom timezone classes](#creating-custom-timezone-classes)
- [Comparison with Standard datetime](#comparison-with-standard-datetime)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [About the Name](#about-the-name)
- [Contributing](#contributing)
- [License](#license)

## Why heliclockter?

Working with timezones in Python can be error-prone. The standard library's `datetime` allows "naive" datetimes that lack timezone information, leading to bugs when mixing naive and aware datetimes or when deploying across different timezones.

**Common problems heliclockter solves:**

1. **Accidental naive datetimes** - It's easy to forget `tzinfo` when creating datetimes
2. **Runtime TypeErrors** - Mixing naive and aware datetimes causes runtime errors
3. **Implicit timezone assumptions** - Code that works locally may break in production
4. **Complex timezone conversions** - Converting between timezones safely requires boilerplate

`heliclockter` enforces timezone-aware datetimes at the type level, catching these issues before they reach production.

## Quickstart

```python
from heliclockter import datetime_utc

# Create a UTC timestamp of the current time
now = datetime_utc.now()
# datetime_utc(2022, 11, 4, 15, 28, 10, 478176, tzinfo=zoneinfo.ZoneInfo(key='UTC'))

# Create a timestamp 2 hours in the future
future = datetime_utc.future(hours=2)
# datetime_utc(2022, 11, 4, 17, 28, 52, 478176, tzinfo=zoneinfo.ZoneInfo(key='UTC'))
```

## Features

- **Runtime enforceable timezone-aware datetimes** - No more naive datetime accidents
- **Statically type checkable** - Full typing support for better IDE experience
- **Pydantic integration** - First-class support for serialization and validation
- **No third-party dependencies** - Lightweight and minimal (pydantic is optional)
- **Battle-tested** - Extensive test suite and production-ready
- **Python 3.9+ support** - Modern Python for modern applications

## Examples

### Working with different timezones

`heliclockter` exposes 3 main classes:

```python
from heliclockter import datetime_tz, datetime_local, datetime_utc

# UTC datetime
utc_now = datetime_utc.now()

# Local timezone datetime  
local_now = datetime_local.now()

# Any timezone datetime (base class)
paris_tz = datetime_tz.now("Europe/Paris")
```

### Real-World Use Cases

#### Scheduling international meetings

```python
from heliclockter import datetime_utc, datetime_tz
from zoneinfo import ZoneInfo

# Schedule a meeting for 3 PM New York time
meeting_ny = datetime_tz(2023, 12, 15, 15, 0, 0, tzinfo=ZoneInfo('America/New_York'))

# Show the time for participants in different timezones
print(f"New York: {meeting_ny.strftime('%I:%M %p %Z')}")
print(f"London: {meeting_ny.astimezone(ZoneInfo('Europe/London')).strftime('%I:%M %p %Z')}")
print(f"Tokyo: {meeting_ny.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%I:%M %p %Z')}")
```

#### Processing server logs from multiple regions

```python
from heliclockter import datetime_utc, datetime_tz
from zoneinfo import ZoneInfo
from typing import List, Tuple

def parse_log_entry(timestamp: str, region: str) -> datetime_utc:
    """Parse log timestamps and normalize to UTC."""
    if region == "us-east":
        tz_name = "America/New_York"
    elif region == "eu-west":
        tz_name = "Europe/London"
    elif region == "asia-pac":
        tz_name = "Asia/Tokyo"
    else:
        tz_name = "UTC"
    
    # Parse with regional timezone
    tz = ZoneInfo(tz_name)
    regional_time = datetime_tz.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    # Assume the parsed time is in the regional timezone
    regional_time = regional_time.replace(tzinfo=tz)
    
    # Convert to UTC
    return datetime_utc.from_datetime(regional_time.astimezone(ZoneInfo('UTC')))

# All logs normalized to UTC for consistent analysis
logs: List[Tuple[datetime_utc, str]] = [
    (parse_log_entry("2023-12-15 10:30:00", "us-east"), "Error in payment processing"),
    (parse_log_entry("2023-12-15 15:30:00", "eu-west"), "Database connection timeout"),
    (parse_log_entry("2023-12-16 00:30:00", "asia-pac"), "API rate limit exceeded"),
]
```

#### Handling user-submitted dates

```python
from heliclockter import datetime_local, datetime_utc, tz_local
from pydantic import BaseModel, Field

class EventForm(BaseModel):
    name: str
    # User enters in their local time, stored as UTC
    start_time: datetime_utc = Field(description="Event start time")
    
    class Config:
        json_encoders = {
            datetime_utc: lambda v: v.isoformat()
        }

# User submits form with their local time
user_input = {
    "name": "Team Standup",
    "start_time": "2023-12-15T09:00:00"  # Assumes user's local time
}

# Convert to UTC for storage
event = EventForm(**user_input)
print(f"Stored as UTC: {event.start_time}")

# Display back in user's local timezone
local_time = event.start_time.astimezone(tz_local)
print(f"Your local time: {local_time.strftime('%I:%M %p on %B %d')}")
```

### Parsing and Pydantic integration

Parse timestamps from external sources with confidence:

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

The `current_time` attribute is guaranteed to be in UTC, regardless of how the API provides it. If no timezone information is provided, UTC is assumed.

### String parsing with strptime

```python
from heliclockter import datetime_utc

# Parse a naive timestamp - assumes UTC
parsed = datetime_utc.strptime('2022-11-04T15:49:29', '%Y-%m-%dT%H:%M:%S')
# datetime_utc(2022, 11, 4, 15, 49, 29, tzinfo=zoneinfo.ZoneInfo(key='UTC'))

# Parse ISO format strings
iso_parsed = datetime_utc.fromisoformat('2022-11-04T15:49:29+00:00')
# datetime_utc(2022, 11, 4, 15, 49, 29, tzinfo=zoneinfo.ZoneInfo(key='UTC'))
```

### Timezone conversions

Convert between timezones safely and explicitly:

```python
from heliclockter import datetime_utc, datetime_tz

# Start with UTC time
utc_time = datetime_utc.now()
# datetime_utc(2022, 11, 4, 15, 30, 0, tzinfo=zoneinfo.ZoneInfo(key='UTC'))

# Convert to Tokyo time
from zoneinfo import ZoneInfo
tokyo_time = utc_time.astimezone(ZoneInfo('Asia/Tokyo'))
# datetime(2022, 11, 5, 0, 30, 0, tzinfo=zoneinfo.ZoneInfo(key='Asia/Tokyo'))

# Convert to New York time
ny_time = utc_time.astimezone(ZoneInfo('America/New_York'))
# datetime(2022, 11, 4, 11, 30, 0, tzinfo=zoneinfo.ZoneInfo(key='America/New_York'))
```

### Handling DST transitions

`heliclockter` correctly handles Daylight Saving Time transitions:

```python
from heliclockter import datetime_tz

# During "fall back" - 2:30 AM happens twice
ambiguous_time = datetime_tz(2022, 11, 6, 2, 30, 0, tz='America/New_York', fold=0)  # First occurrence (DST)
ambiguous_time_later = datetime_tz(2022, 11, 6, 2, 30, 0, tz='America/New_York', fold=1)  # Second occurrence (Standard)

# Convert to UTC to see the difference
print(ambiguous_time.astimezone(ZoneInfo('UTC')))  # 2022-11-06 06:30:00+00:00
print(ambiguous_time_later.astimezone(ZoneInfo('UTC')))  # 2022-11-06 07:30:00+00:00
```

### Error handling

`heliclockter` provides clear error messages for common mistakes:

```python
from heliclockter import datetime_utc, DatetimeTzError
from datetime import datetime

# Attempting to create from naive datetime
try:
    naive_dt = datetime(2022, 11, 4, 15, 30, 0)
    utc_dt = datetime_utc.from_datetime(naive_dt)
except DatetimeTzError as e:
    print(e)  # "Refusing to create a datetime_utc from a naive datetime"

# Safe conversion - datetime_utc.from_datetime assumes UTC for naive datetimes
naive_dt = datetime(2022, 11, 4, 15, 30, 0)
safe_utc = datetime_utc.from_datetime(naive_dt)  # Assumes UTC
```

## Installation

```bash
pip install heliclockter
```

For pydantic support:

```bash
pip install heliclockter[pydantic]
```

### Requirements

- Python 3.9+
- No runtime dependencies (pydantic is optional)

## API Reference

### Core Classes

#### `datetime_tz`
Base class for timezone-aware datetimes. All other classes inherit from this.

**Class Methods:**
- `now(tz: str | ZoneInfo | None = None) -> datetime_tz` - Create a datetime for the current time
- `from_datetime(dt: datetime) -> datetime_tz` - Create from a datetime (assumes class's default timezone if naive)
- `strptime(date_string: str, format: str) -> datetime_tz` - Parse a string into a datetime
- `fromisoformat(date_string: str) -> datetime_tz` - Parse an ISO format string
- `future(**kwargs) -> datetime_tz` - Create a datetime in the future
- `past(**kwargs) -> datetime_tz` - Create a datetime in the past

**Instance Methods:**
- `astimezone(tz: ZoneInfo) -> datetime_tz` - Convert to another timezone (inherited from datetime)
- `strftime(format: str) -> str` - Format datetime as string
- `replace(**kwargs) -> datetime_tz` - Create a new datetime with replaced values

#### `datetime_utc`
A `datetime_tz` guaranteed to be in UTC timezone.

**Additional Class Methods:**
- `fromtimestamp(timestamp: float) -> datetime_utc` - Create from Unix timestamp

**Default Behavior:**
- Naive datetimes are assumed to be in UTC

#### `datetime_local`
A `datetime_tz` guaranteed to be in the system's local timezone.

**Default Behavior:**
- Naive datetimes are assumed to be in the local timezone

### Exceptions

#### `DatetimeTzError`
Raised when timezone-related operations fail, such as attempting to create a timezone-aware datetime from a naive one without explicit conversion.

### Module Exports

For convenience, `heliclockter` also exports:
- `date` - The standard library's date class
- `timedelta` - The standard library's timedelta class
- `tz_local` - The system's local timezone (ZoneInfo object)

## Advanced Usage

### Type Hints and Static Analysis

`heliclockter` provides excellent type safety with static type checkers like mypy:

```python
from heliclockter import datetime_utc, datetime_tz, datetime_local, timedelta
from typing import Union, Optional, TypeVar
from zoneinfo import ZoneInfo

# Type annotations work seamlessly
def schedule_task(when: datetime_utc) -> None:
    """Schedule a task to run at a specific UTC time."""
    print(f"Task scheduled for {when.isoformat()}")

# Union types for flexibility
def parse_timestamp(
    value: str, 
    tz: Optional[Union[str, ZoneInfo]] = None
) -> Union[datetime_utc, datetime_tz]:
    """Parse a timestamp, returning UTC if no timezone specified."""
    if tz:
        return datetime_tz.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(tz) if isinstance(tz, str) else tz)
    return datetime_utc.strptime(value, "%Y-%m-%d %H:%M:%S")

# Type narrowing with isinstance
def process_datetime(dt: Union[datetime_utc, datetime_local]) -> str:
    if isinstance(dt, datetime_utc):
        return f"UTC time: {dt}"
    else:  # Type checker knows this is datetime_local
        return f"Local time: {dt}"

# Generic functions with TypeVar
DateTimeTzT = TypeVar('DateTimeTzT', bound=datetime_tz)

def add_hours(dt: DateTimeTzT, hours: int) -> DateTimeTzT:
    """Add hours to any datetime_tz subclass, preserving the type."""
    return dt + timedelta(hours=hours)

# Usage maintains type safety
utc_time = datetime_utc.now()
new_utc_time = add_hours(utc_time, 3)  # Type: datetime_utc

local_time = datetime_local.now()
new_local_time = add_hours(local_time, 3)  # Type: datetime_local
```

### Creating custom timezone classes

Extend `heliclockter` for your specific needs:

```python
from zoneinfo import ZoneInfo
from heliclockter import datetime_tz


class datetime_cet(datetime_tz):
    """
    A `datetime_cet` is a `datetime_tz` guaranteed to be in the 'CET' timezone.
    """
    assumed_timezone_for_timezone_naive_input = ZoneInfo('CET')


# Parse naive timestamps with known timezone
aware_dt = datetime_cet.strptime('2022-11-04T15:49:29', '%Y-%m-%dT%H:%M:%S')
# datetime_cet(2022, 11, 4, 15, 49, 29, tzinfo=zoneinfo.ZoneInfo(key='CET'))
```

### Enforcing timezone-aware code

`heliclockter` ensures you never accidentally create naive datetimes:

```python
from heliclockter import datetime_utc

# ✅ This works
good = datetime_utc(2022, 11, 4, 15, 30, 0)

# ❌ This raises an exception
from datetime import datetime
bad = datetime_utc.from_datetime(datetime(2022, 11, 4, 15, 30, 0))
# Raises: HeliclockterError: Refusing to create a datetime_utc from a naive datetime
```

## Comparison with Standard datetime

### Standard datetime

```python
from datetime import datetime, timezone

# Easy to accidentally create naive datetimes
naive = datetime(2022, 11, 4, 15, 30)  # No timezone!

# Mixing naive and aware fails at runtime
aware = datetime.now(timezone.utc)
try:
    result = aware - naive  # TypeError!
except TypeError as e:
    print("Can't mix naive and aware datetimes")

# Timezone conversion is verbose
utc_time = datetime.now(timezone.utc)
from zoneinfo import ZoneInfo
tokyo_time = utc_time.astimezone(ZoneInfo('Asia/Tokyo'))
```

### With heliclockter

```python
from heliclockter import datetime_utc, datetime_tz

# Impossible to create naive datetimes
utc_time = datetime_utc(2022, 11, 4, 15, 30)  # Always UTC

# All datetimes are aware - operations just work
now = datetime_utc.now()
future = datetime_utc.future(hours=2)
diff = future - now  # No TypeError!

# Timezone conversion using standard method
from zoneinfo import ZoneInfo
tokyo_time = utc_time.astimezone(ZoneInfo('Asia/Tokyo'))
```

### Key Differences

| Feature | Standard datetime | heliclockter |
|---------|------------------|--------------|
| Naive datetime prevention | ❌ Allowed by default | ✅ Impossible to create |
| Type safety | ❌ No timezone guarantees | ✅ Types encode timezone |
| Default timezone | ❌ None (naive) | ✅ Explicit (UTC/Local) |
| API complexity | ❌ Verbose | ✅ Intuitive |
| Pydantic integration | ❌ Manual configuration | ✅ Built-in support |

## Performance

`heliclockter` adds minimal overhead compared to standard Python datetime operations:

- **Instantiation**: ~5% slower than naive datetime creation due to timezone validation
- **Timezone conversion**: Same performance as standard `astimezone()` (no overhead)
- **Memory usage**: Identical to timezone-aware datetime objects
- **Pydantic parsing**: Optimized validators with minimal overhead

The safety guarantees and developer experience improvements far outweigh the negligible performance impact.

## Troubleshooting

### Common Issues

#### "Cannot create aware datetime from naive if no tz is assumed"
This error occurs when trying to create a `datetime_tz` from a naive datetime without specifying a timezone.

**Solution**: Use `datetime_utc` or `datetime_local` which have default timezones, or explicitly convert the naive datetime first.

#### "Module 'zoneinfo' not found" (Python 3.8)
Python 3.8 doesn't include `zoneinfo` in the standard library.

**Solution**: Install the backport: `pip install backports.zoneinfo`

#### Type checker shows errors with datetime operations
Your type checker might not recognize that `datetime_tz` inherits from `datetime.datetime`.

**Solution**: Add type annotations or use `cast()` from the `typing` module when needed.

### Getting Help

- Check the [GitHub Issues](https://github.com/channable/heliclockter/issues) for known problems
- Read the [API Reference](#api-reference) for detailed method documentation
- See the [Examples](#examples) section for common use cases

## About the Name

`heliclockter` is a portmanteau of "clock" and "helicopter". Like a [helicopter parent](https://en.wikipedia.org/wiki/Helicopter_parent) that strictly supervises their children, `heliclockter` watches over your datetime handling, ensuring you never make timezone mistakes.

📖 Read the [announcement post](https://www.channable.com/tech/heliclockter-timezone-aware-datetimes-in-python) for more background on why we created `heliclockter`.

## Contributing

We'd love your contributions! Please see our [Contributing Guidelines](https://github.com/channable/heliclockter/blob/master/CONTRIBUTING.md) for details.

### Development setup

```bash
# Clone the repo
git clone https://github.com/channable/heliclockter.git
cd heliclockter

# Install development dependencies
pip install -e ".[dev,pydantic]"

# Run tests
pytest

# Run type checking
mypy src
```

## License

`heliclockter` is licensed under the BSD 3-Clause License. See [LICENSE](https://github.com/channable/heliclockter/blob/master/LICENSE) for details.
