"""Angle normalisation and sexagesimal formatting.

Formatting is not cosmetic here. The degree-minute-second line is the primary
output an astrologer reads, and a value that cannot exist on a clock face --
"16 deg 10' 60.00\"" -- undermines confidence in numbers that are otherwise
accurate to sub-arcsecond.
"""

from __future__ import annotations

import pytest

from jyotish.core.angles import (
    format_dms,
    format_zodiacal,
    norm180,
    norm360,
    sep360,
    to_dms,
)


# --- normalisation ----------------------------------------------------------

@pytest.mark.parametrize(
    "value,expected",
    [(0.0, 0.0), (360.0, 0.0), (720.0, 0.0), (-0.0, 0.0), (-30.0, 330.0),
     (-360.0, 0.0), (359.9, 359.9), (450.0, 90.0), (-450.0, 270.0)],
)
def test_norm360(value: float, expected: float) -> None:
    assert norm360(value) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    "value,expected",
    [(0.0, 0.0), (180.0, -180.0), (181.0, -179.0), (-180.0, -180.0), (359.0, -1.0)],
)
def test_norm180(value: float, expected: float) -> None:
    assert norm180(value) == pytest.approx(expected, abs=1e-12)


def test_sep360_crosses_the_seam() -> None:
    """359.9999 and 0.0001 are two ten-thousandths apart, not 359.9998."""
    assert sep360(359.9999, 0.0001) == pytest.approx(0.0002, abs=1e-9)
    assert sep360(0.0, 180.0) == pytest.approx(180.0)
    assert sep360(10.0, 350.0) == pytest.approx(20.0)


# --- the 60.00" defect ------------------------------------------------------

@pytest.mark.parametrize("precision", [0, 1, 2, 3, 4, 6])
def test_seconds_never_render_as_sixty(precision: int) -> None:
    """Sweep the whole approach to a minute boundary at several precisions.

    The old guard was a fixed `round(s, 6) >= 60.0`, so anything in
    [59.995, 59.9999995) survived it and then rendered as "60.00" at the two
    decimals actually displayed. The carry has to happen at display precision.
    """
    for i in range(2000):
        deg = 16.0 + (10 * 60 + 59.0 + i / 2000.0) / 3600.0
        out = format_dms(deg, precision)
        secs = out.split("'")[1].rstrip('"')
        assert float(secs) < 60.0, f"{deg!r} at precision {precision} -> {out}"


def test_the_reported_chart_no_longer_prints_sixty() -> None:
    """The exact value the audit found in a real chart."""
    assert format_dms(16 + 10 / 60 + 59.999 / 3600) == "16°11'00.00\""


def test_minutes_never_render_as_sixty() -> None:
    for i in range(2000):
        deg = 5.0 + (59.0 + i / 2000.0) / 60.0
        out = format_dms(deg, 2)
        minutes = out.split("°")[1].split("'")[0]
        assert int(minutes) < 60, f"{deg!r} -> {out}"


def test_carry_propagates_through_both_places() -> None:
    assert format_dms(29.99999999, 2) == "30°00'00.00\""


# --- zodiacal formatting ----------------------------------------------------

def test_zodiacal_never_shows_thirty_degrees() -> None:
    """A graha a hair below a rasi boundary must not display as "30 deg".

    That reads as the *start of the next rasi* while the rasi label beside it
    still names the current one -- a display thirty degrees out. Such a graha is
    at the very end of its rasi, so it shows the last representable value there.
    """
    for lon in (29.99999999, 59.999999999, 359.9999999, 89.9999999999):
        out = format_zodiacal(lon)
        degrees = int(out.split("°")[0])
        assert degrees < 30, f"{lon!r} -> {out}"


def test_zodiacal_end_of_rasi_reads_as_end_not_start() -> None:
    assert format_zodiacal(29.99999999) == "29°59'59.99\""
    assert format_zodiacal(0.0) == "0°00'00.00\""


@pytest.mark.parametrize(
    "longitude,expected",
    [(0.0, "0°00'00.00\""), (45.5, "15°30'00.00\""), (123.25, "3°15'00.00\"")],
)
def test_zodiacal_ordinary_values(longitude: float, expected: str) -> None:
    assert format_zodiacal(longitude) == expected


# --- structure --------------------------------------------------------------

def test_to_dms_sign_is_carried_separately() -> None:
    assert to_dms(-12.5).sign == -1
    assert to_dms(-12.5).degrees == 12
    assert format_dms(-12.5) == "-12°30'00.00\""


def test_to_dms_round_trips() -> None:
    for deg in (0.0, 1.5, 23.4392911, 179.999, 359.5):
        d = to_dms(deg)
        back = d.degrees + d.minutes / 60.0 + d.seconds / 3600.0
        assert back == pytest.approx(deg, abs=1e-9)
