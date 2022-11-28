1.0.2
-----

Released 2022-11-28.

**Breaking changes**:

- None.

Release highlights:

- Fix bug in `datetime_tz.from_datetime()` where if the input datetime is itself a different instance of `datetime_tz` than the class reparsing it an `AssertionError` would be raised.

1.0.1
-----

Released 2022-11-23.

**Breaking changes**:

- None.

Release highlights:

- Enrich project metadata

1.0.0
-----

Initial release. See [the blog post](https://www.channable.com/tech/heliclockter-timezone-aware-datetimes-in-python) to learn more.