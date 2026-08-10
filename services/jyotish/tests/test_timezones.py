"""Timezone resolution and daylight-saving edge cases.

These need no place index and no ephemeris kernel -- they are pure calendar
arithmetic, and they guard the input layer that feeds the validated astronomy.

Why this matters more here than in most apps: the ascendant advances roughly one
degree every four minutes, so an hour of timezone doubt is about 15 degrees of
lagna. That is frequently a different rasi, and therefore a different chart, a
different dasha balance and different predictions. Silently guessing is not an
acceptable behaviour.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from jyotish.core.birthdata import BirthData, format_time_12h, parse_time


def _at(when: datetime, zone: str, fold: int = 0, lat: float = 13.0827,
        lon: float = 80.2707) -> BirthData:
    return BirthData(when=when, latitude=lat, longitude=lon,
                     timezone_name=zone, fold=fold)


# --- historical Indian offsets ---------------------------------------------

def test_modern_india_is_five_thirty() -> None:
    assert _at(datetime(1990, 5, 15, 6, 30), "Asia/Kolkata").utc_offset == timedelta(
        hours=5, minutes=30
    )


def test_wartime_india_is_six_thirty() -> None:
    """India ran UTC+06:30 from 1942-09-01 to 1945-10-15."""
    assert _at(datetime(1943, 3, 12, 11, 20), "Asia/Kolkata").utc_offset == timedelta(
        hours=6, minutes=30
    )


def test_wartime_is_labelled_as_wartime_not_daylight_saving() -> None:
    """The tz database models the wartime offset as DST.

    Reporting "daylight saving" for a 1943 Indian birth would be actively
    misleading, so the specific case is checked before the generic one.
    """
    note = _at(datetime(1943, 3, 12, 11, 20), "Asia/Kolkata").offset_note
    assert note is not None and "wartime" in note


def test_pre_1906_madras_local_mean_time() -> None:
    """Madras kept local mean time, UTC+05:21:10, until 1906."""
    birth = _at(datetime(1899, 6, 7, 9, 30), "Asia/Kolkata")
    assert birth.utc_offset == timedelta(hours=5, minutes=21, seconds=10)
    assert "local mean time" in (birth.offset_note or "")


def test_ordinary_indian_birth_has_no_annotation() -> None:
    assert _at(datetime(1990, 5, 15, 6, 30), "Asia/Kolkata").offset_note is None


# --- nonexistent local times (spring forward) -------------------------------

def test_nonexistent_time_is_detected() -> None:
    """02:30 on 1997-04-06 never happened in California; clocks went 02:00->03:00."""
    birth = _at(datetime(1997, 4, 6, 2, 30), "America/Los_Angeles",
                lat=37.7749, lon=-122.4194)
    assert birth.time_is_nonexistent
    assert not birth.time_is_ambiguous


def test_real_time_is_not_flagged_nonexistent() -> None:
    birth = _at(datetime(1997, 4, 6, 4, 30), "America/Los_Angeles",
                lat=37.7749, lon=-122.4194)
    assert not birth.time_is_nonexistent


# --- ambiguous local times (fall back) --------------------------------------

def test_ambiguous_time_is_detected() -> None:
    """01:30 on 2010-11-07 happened twice on the US east coast."""
    birth = _at(datetime(2010, 11, 7, 1, 30), "America/New_York",
                lat=40.2171, lon=-74.7429)
    assert birth.time_is_ambiguous
    assert not birth.time_is_nonexistent


def test_fold_selects_the_other_occurrence() -> None:
    first = _at(datetime(2010, 11, 7, 1, 30), "America/New_York", fold=0,
                lat=40.2171, lon=-74.7429)
    second = _at(datetime(2010, 11, 7, 1, 30), "America/New_York", fold=1,
                 lat=40.2171, lon=-74.7429)

    assert first.utc_offset == timedelta(hours=-4)   # still on summer time
    assert second.utc_offset == timedelta(hours=-5)  # back on standard time
    assert second.utc - first.utc == timedelta(hours=1)


def test_alternative_round_trips() -> None:
    birth = _at(datetime(2010, 11, 7, 1, 30), "America/New_York",
                lat=40.2171, lon=-74.7429)
    other = birth.alternative
    assert other is not None and other.fold == 1
    assert other.alternative.fold == 0


def test_unambiguous_time_has_no_alternative() -> None:
    assert _at(datetime(1990, 5, 15, 6, 30), "Asia/Kolkata").alternative is None


def test_india_never_has_ambiguous_times() -> None:
    """India has had no daylight saving since 1945, so no repeated hours."""
    for month in range(1, 13):
        birth = _at(datetime(1990, month, 15, 1, 30), "Asia/Kolkata")
        assert not birth.time_is_ambiguous
        assert not birth.time_is_nonexistent


# --- validation -------------------------------------------------------------

def test_fold_must_be_zero_or_one() -> None:
    with pytest.raises(ValueError, match="fold must be 0 or 1"):
        _at(datetime(1990, 5, 15, 6, 30), "Asia/Kolkata", fold=2)


def test_aware_datetime_still_rejected() -> None:
    with pytest.raises(ValueError, match="naive local datetime"):
        BirthData(
            when=datetime(1990, 5, 15, 6, 30, tzinfo=timezone.utc),
            latitude=13.0827, longitude=80.2707,
        )


def test_dst_is_annotated_for_diaspora_births() -> None:
    birth = _at(datetime(1988, 7, 21, 3, 45), "Europe/London", lat=51.5074, lon=-0.1278)
    assert birth.utc_offset == timedelta(hours=1)
    assert "daylight saving" in (birth.offset_note or "")


# --- birth time entry -------------------------------------------------------
#
# Twelve hours of error moves the ascendant by roughly 180 degrees, so an
# AM/PM mistake produces a chart that is wrong in every particular while looking
# entirely plausible. Same class of silent failure as the DST cases above.

@pytest.mark.parametrize(
    "text,expected",
    [
        ("06:30", (6, 30, 0)),          # bare times are 24-hour
        ("18:30", (18, 30, 0)),
        ("6:30 AM", (6, 30, 0)),
        ("6:30 PM", (18, 30, 0)),
        ("6:30pm", (18, 30, 0)),        # no space
        ("6:30 p.m.", (18, 30, 0)),     # dotted
        ("  6:30 Pm  ", (18, 30, 0)),   # whitespace and case
        ("18:30:45", (18, 30, 45)),
        ("12:00 AM", (0, 0, 0)),        # midnight
        ("12:00 PM", (12, 0, 0)),       # noon
        ("12:01 AM", (0, 1, 0)),
        ("00:00", (0, 0, 0)),
        ("23:59:59", (23, 59, 59)),
    ],
)
def test_parse_time(text: str, expected: tuple[int, int, int]) -> None:
    assert parse_time(text) == expected


def test_twelve_hour_and_twenty_four_hour_agree() -> None:
    assert parse_time("6:30 PM") == parse_time("18:30")
    assert parse_time("6:30 AM") == parse_time("06:30")


@pytest.mark.parametrize("text", ["13:30 PM", "0:30 AM", "25:00", "6:70", "13:00 am"])
def test_contradictory_or_invalid_times_are_rejected(text: str) -> None:
    """Refuse to guess. '13:30 PM' could mean 13:30 or 01:30."""
    with pytest.raises(ValueError):
        parse_time(text)


@pytest.mark.parametrize("text", ["", "630", "6.30", "six thirty", "6:30:00:00"])
def test_unreadable_times_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="Cannot read time"):
        parse_time(text)


@pytest.mark.parametrize(
    "hour,minute,expected",
    [(0, 0, "12:00 AM"), (6, 30, "6:30 AM"), (12, 0, "12:00 PM"),
     (18, 30, "6:30 PM"), (23, 59, "11:59 PM")],
)
def test_format_time_12h(hour: int, minute: int, expected: str) -> None:
    assert format_time_12h(hour, minute) == expected


def test_am_pm_error_moves_the_lagna_half_a_zodiac() -> None:
    """Why this is a correctness feature and not a convenience.

    The same clock reading taken as morning and as evening gives lagnas about
    six rasis apart -- here Taurus versus Scorpio, exact opposites.
    """
    from jyotish.core import ayanamsa as ay
    from jyotish.core import positions as pos

    def lagna_rasi_for(text: str) -> int:
        h, m, s = parse_time(text)
        birth = BirthData(
            when=datetime(1990, 5, 15, h, m, s),
            latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
        )
        return pos.compute(birth, ay.Ayanamsa.LAHIRI).lagna.rasi

    morning, evening = lagna_rasi_for("6:30 AM"), lagna_rasi_for("6:30 PM")
    assert (evening - morning) % 12 == 6, "expected opposite rasis"
