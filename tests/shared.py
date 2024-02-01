"""
We cannot write unittest using `datetime_local` that asserts a fixed offset compared to some
other datetime_tz class because the local timezone depends on the machine that runs the tests.

Because of this we declare `datetime_cet` here to test with.
"""

from zoneinfo import ZoneInfo

from heliclockter import datetime_tz


class datetime_cet(datetime_tz):
    """
    A `datetime_cet` is a `datetime_tz` but which is guaranteed to be in the 'CET' timezone.
    """

    assumed_timezone_for_timezone_naive_input = ZoneInfo('CET')
