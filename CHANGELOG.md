1.3.0
-----

Released 2024-02-05.

**Breaking changes**:

- None

Release highlights:

- Adds support for python 3.12.
- Adds `fold` to the constructor of `datetime_tz`

1.2.0
-----

Released 2023-11-16.

**Breaking changes**:

- None

Release highlights:

- Adds support for using the `pydantic.v1` module from pydantic v2 for backward compatibility.

1.1.0
-----

Released 2023-10-02.

**Breaking changes**:

- None

Release highlights:

- Heliclockter now supports Pydantic v2. See the
  [migration guide](https://docs.pydantic.dev/latest/migration/) on how to migrate to Pydantic v2.
  Pydantic v1 is still supported for now. 

1.0.4
-----

Released 2022-12-02.

**Breaking changes**:

- None.

Release highlights:

- Allow `pydantic` models to parse `datetime.datetime` input values

1.0.3
-----

Released 2022-11-29.

**Breaking changes**:

- None.

Release highlights:

- Included `py.typed` in packaged release

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