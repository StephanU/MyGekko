"""Test MyGekko sensor helpers."""
from datetime import datetime
from datetime import timezone
from unittest.mock import patch

from custom_components.mygekko import sensor


class _FakeEMobil:
    """Minimal stand-in exposing the charge fields the helper reads."""

    def __init__(self, start, duration=None):
        """Store the raw MyGekko charge start and duration strings."""
        self.charge_start_time = start
        self.charge_duration_time = duration


def _expected(year, month, day, hour, minute, second):
    """Build the expected timezone-aware datetime the helper should return."""
    return datetime(
        year, month, day, hour, minute, second, tzinfo=sensor.dt_util.DEFAULT_TIME_ZONE
    )


def test_charge_start_parses_german_format():
    """The German 'dd.mm.YYYY HH:MM:SS' layout is parsed as local time."""
    result = sensor._emobil_charge_start(_FakeEMobil("23.07.2026 14:47:23"))
    assert result == _expected(2026, 7, 23, 14, 47, 23)
    assert result.tzinfo is not None


def test_charge_start_parses_iso_and_us_layouts():
    """ISO and unambiguous US layouts are parsed to the same instant."""
    # 23 > 12, so only the US mm/dd reading is valid - no anchor needed.
    assert sensor._emobil_charge_start(
        _FakeEMobil("07/23/2026 14:47:23")
    ) == _expected(2026, 7, 23, 14, 47, 23)
    assert sensor._emobil_charge_start(
        _FakeEMobil("2026-07-23 14:47:23")
    ) == _expected(2026, 7, 23, 14, 47, 23)


def test_charge_start_ambiguous_date_uses_duration_anchor():
    """dd/mm vs mm/dd is resolved via the elapsed-duration anchor."""
    # "05/07/2026" could be 5 Jul (dd/mm) or 7 May (mm/dd).
    now = datetime(2026, 5, 7, 12, 0, 0, tzinfo=timezone.utc)
    with patch.object(sensor.dt_util, "now", return_value=now):
        result = sensor._emobil_charge_start(
            _FakeEMobil("05/07/2026 10:00:00", "2h 0m 0s")
        )
    # now - 2h = 2026-05-07 10:00, so the 7 May reading wins.
    assert result == _expected(2026, 5, 7, 10, 0, 0)


def test_charge_start_none_when_missing_or_invalid():
    """Missing or unparseable start times yield None (sensor 'unknown')."""
    assert sensor._emobil_charge_start(_FakeEMobil(None)) is None
    assert sensor._emobil_charge_start(_FakeEMobil("")) is None
    # The duration field's own format must not parse as a start time.
    assert sensor._emobil_charge_start(_FakeEMobil("20h 50m 51s")) is None
    assert sensor._emobil_charge_start(_FakeEMobil("not a date")) is None


def test_duration_seconds_handles_letter_and_colon_formats():
    """Both '20h 50m 51s' and '20:50:51' style durations are read."""
    assert sensor._emobil_charge_duration_seconds("20h 50m 51s") == 75051
    assert sensor._emobil_charge_duration_seconds("01:23:45") == 5025
    assert sensor._emobil_charge_duration_seconds("1d 2h 3m 4s") == 93784


def test_duration_seconds_none_when_zero_or_empty():
    """A zero, missing or number-less duration reads as None."""
    assert sensor._emobil_charge_duration_seconds("0h 0m 0s") is None
    assert sensor._emobil_charge_duration_seconds("00:00:00") is None
    assert sensor._emobil_charge_duration_seconds("") is None
    assert sensor._emobil_charge_duration_seconds(None) is None
