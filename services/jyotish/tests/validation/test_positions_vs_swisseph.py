"""Accuracy gate: graha longitudes, lagna and nakshatra pada vs Swiss Ephemeris.

This is the test that protects the product's credibility. The target audience
includes practising astrologers, and a single wrong nakshatra pada is enough for
them to abandon the app permanently. Pada assignment must therefore be exact,
not merely close.

The fixture set is chosen to exercise the cases that actually break engines:

* Wartime India (1942-09 to 1945-10), when the country ran UTC+06:30.
* Pre-1906 Madras local mean time (UTC+05:21:10).
* Diaspora births across Singapore, Malaysia, the UK, the US and Australia,
  including DST-active dates.
* High northern latitude, where the ascendant formula is most sensitive.
* Southern hemisphere, where a sign error in the latitude term would show.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData

swe = pytest.importorskip("swisseph", reason="dev-only accuracy oracle")

#: Longitude agreement gate for everything except the Moon.
TOLERANCE_ARCSEC = 1.0

#: The Moon gets a looser gate, and the reason is the *oracle's* limitation
#: rather than ours. pyswisseph ships without the .se1 data files, so it
#: silently falls back to Moshier's analytical theory (see
#: test_oracle_backend_is_declared below, which pins this). Moshier is accurate
#: to roughly 1-3 arcsec for the Moon, while our DE440s figure is sub-arcsecond.
#: In other words, where the two disagree on the Moon, we are the more accurate
#: source. Cross-checking the Moon to sub-arcsecond needs Jagannatha Hora, which
#: bundles genuine Swiss ephemeris files.
MOON_TOLERANCE_ARCSEC = 3.0

SWE_BODY = {
    0: "SUN", 1: "MOON", 2: "MARS", 3: "MERCURY",
    4: "JUPITER", 5: "VENUS", 6: "SATURN",
}

# (label, local datetime, lat, lon, IANA zone)
FIXTURES = [
    ("chennai-1990",        datetime(1990, 5, 15, 6, 30),   13.0827,  80.2707, "Asia/Kolkata"),
    ("madurai-1975",        datetime(1975, 11, 3, 22, 15),   9.9252,  78.1198, "Asia/Kolkata"),
    ("coimbatore-2005",     datetime(2005, 8, 30, 4, 12),   11.0168,  76.9558, "Asia/Kolkata"),
    ("trichy-1968",         datetime(1968, 1, 19, 17, 40),  10.7905,  78.7047, "Asia/Kolkata"),
    ("salem-1999",          datetime(1999, 12, 31, 23, 59), 11.6643,  78.1460, "Asia/Kolkata"),
    # Wartime India: UTC+06:30, a classic source of one-rasi lagna errors.
    ("madras-1943-war",     datetime(1943, 3, 12, 11, 20),  13.0827,  80.2707, "Asia/Kolkata"),
    ("madras-1944-war",     datetime(1944, 9, 2, 5, 5),     13.0827,  80.2707, "Asia/Kolkata"),
    # Pre-1906 Madras local mean time, UTC+05:21:10.
    ("madras-1899-lmt",     datetime(1899, 6, 7, 9, 30),    13.0827,  80.2707, "Asia/Kolkata"),
    ("madras-1905-lmt",     datetime(1905, 2, 14, 20, 45),  13.0827,  80.2707, "Asia/Kolkata"),
    # Diaspora.
    ("singapore-2001",      datetime(2001, 2, 9, 14, 5),     1.3521, 103.8198, "Asia/Singapore"),
    ("kualalumpur-1993",    datetime(1993, 6, 18, 8, 22),    3.1390, 101.6869, "Asia/Kuala_Lumpur"),
    ("london-1988-bst",     datetime(1988, 7, 21, 3, 45),   51.5074,  -0.1278, "Europe/London"),
    ("london-1988-gmt",     datetime(1988, 1, 21, 3, 45),   51.5074,  -0.1278, "Europe/London"),
    # Both of the next two sit on daylight-saving transitions and are kept
    # deliberately: newjersey-2010 01:30 occurs twice, sanfrancisco-1997 02:30
    # never occurred at all. They pass here because we and the oracle derive the
    # same UTC instant, which is exactly the point -- the *astronomy* agrees
    # regardless. Whether the instant is the intended one is a separate
    # question, covered by tests/test_timezones.py.
    ("newjersey-2010",      datetime(2010, 11, 7, 1, 30),   40.0583, -74.4057, "America/New_York"),
    ("sanfrancisco-1997",   datetime(1997, 4, 6, 2, 30),    37.7749,-122.4194, "America/Los_Angeles"),
    ("toronto-2015",        datetime(2015, 3, 8, 3, 15),    43.6532, -79.3832, "America/Toronto"),
    ("sydney-2003",         datetime(2003, 10, 26, 2, 30),  -33.8688, 151.2093, "Australia/Sydney"),
    ("colombo-1982",        datetime(1982, 4, 14, 6, 0),     6.9271,  79.8612, "Asia/Colombo"),
    ("dubai-2018",          datetime(2018, 12, 25, 13, 45), 25.2048,  55.2708, "Asia/Dubai"),
    # High latitude: the ascendant is most sensitive here.
    ("oslo-1994",           datetime(1994, 6, 21, 0, 30),   59.9139,  10.7522, "Europe/Oslo"),
]


def _swisseph_reference(bd: BirthData):
    """Sidereal Lahiri longitudes and ascendant from the oracle."""
    u = bd.utc
    jd = swe.julday(
        u.year, u.month, u.day,
        u.hour + u.minute / 60.0 + u.second / 3600.0 + u.microsecond / 3.6e9,
    )
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    longitudes = {
        gi: swe.calc_ut(jd, getattr(swe, name), flags)[0][0]
        for gi, name in SWE_BODY.items()
    }
    longitudes[7] = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0]
    longitudes[8] = (longitudes[7] + 180.0) % 360.0

    _cusps, ascmc = swe.houses_ex(jd, bd.latitude, bd.longitude, b"P", swe.FLG_SIDEREAL)
    return longitudes, ascmc[0]


def _sep_arcsec(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0) * 3600.0


@pytest.fixture(scope="module", params=FIXTURES, ids=[f[0] for f in FIXTURES])
def case(request):
    label, when, lat, lon, tz = request.param
    bd = BirthData(when=when, latitude=lat, longitude=lon, timezone_name=tz, name=label)
    chart = pos.compute(bd, ay.Ayanamsa.LAHIRI)
    reference, ref_asc = _swisseph_reference(bd)
    return label, chart, reference, ref_asc


def test_oracle_backend_is_declared() -> None:
    """Pin which ephemeris backend the oracle actually used.

    Swiss Ephemeris falls back from SWIEPH to Moshier *silently* when its .se1
    files are absent, which would otherwise leave us quietly validating against
    a lower-accuracy source and mistaking its error for ours. If someone later
    installs the real data files this test fails loudly, and the Moon tolerance
    below should then be tightened to 1 arcsec.
    """
    jd = swe.julday(1997, 4, 6, 10.5)
    _vals, returned = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    assert returned & swe.FLG_MOSEPH, (
        "Oracle is no longer using Moshier -- real Swiss ephemeris files appear "
        "to be installed. Tighten MOON_TOLERANCE_ARCSEC to 1.0."
    )


def test_graha_longitudes(case) -> None:
    label, chart, reference, _ = case
    for gi, expected in reference.items():
        actual = chart.grahas[gi].longitude
        diff = _sep_arcsec(actual, expected)
        tolerance = MOON_TOLERANCE_ARCSEC if gi == 1 else TOLERANCE_ARCSEC
        assert diff < tolerance, (
            f"{label} {chart.grahas[gi].name}: ours={actual:.6f} "
            f"swisseph={expected:.6f} diff={diff:.4f} arcsec"
        )


def test_lagna(case) -> None:
    label, chart, _, ref_asc = case
    diff = _sep_arcsec(chart.lagna.longitude, ref_asc)
    assert diff < TOLERANCE_ARCSEC, (
        f"{label} lagna: ours={chart.lagna.longitude:.6f} "
        f"swisseph={ref_asc:.6f} diff={diff:.4f} arcsec"
    )


def test_nakshatra_and_pada_match_exactly(case) -> None:
    """Pada must agree 100% of the time, not merely to a tolerance."""
    from jyotish.core.zodiac import NAKSHATRA_SPAN, PADA_SPAN, resolve

    label, chart, reference, ref_asc = case

    for gi, expected_lon in reference.items():
        expected = resolve(expected_lon)
        actual = chart.grahas[gi].position
        assert (actual.nakshatra, actual.pada) == (expected.nakshatra, expected.pada), (
            f"{label} {chart.grahas[gi].name}: "
            f"ours nak{actual.nakshatra + 1} pada{actual.pada}, "
            f"swisseph nak{expected.nakshatra + 1} pada{expected.pada}"
        )
        assert actual.rasi == expected.rasi, f"{label} {chart.grahas[gi].name}: rasi differs"

    expected_asc = resolve(ref_asc)
    assert (chart.lagna.nakshatra, chart.lagna.pada, chart.lagna.rasi) == (
        expected_asc.nakshatra, expected_asc.pada, expected_asc.rasi,
    ), f"{label}: lagna nakshatra/pada/rasi differ"


def test_wartime_india_offset_is_six_thirty() -> None:
    """India ran UTC+06:30 during the war. Hardcoding +05:30 shifts the lagna
    by a full hour of right ascension, which is usually a whole rasi."""
    bd = BirthData(
        when=datetime(1943, 3, 12, 11, 20),
        latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
    )
    assert bd.utc_offset.total_seconds() == 6.5 * 3600


def test_pre_1906_madras_uses_local_mean_time() -> None:
    """Before 1906 Madras kept local mean time at UTC+05:21:10."""
    bd = BirthData(
        when=datetime(1899, 6, 7, 9, 30),
        latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
    )
    assert bd.utc_offset.total_seconds() == pytest.approx(5 * 3600 + 21 * 60 + 10, abs=1)


def test_timezone_resolved_from_coordinates_when_omitted() -> None:
    bd = BirthData(when=datetime(1990, 5, 15, 6, 30), latitude=13.0827, longitude=80.2707)
    assert bd.zone.key == "Asia/Kolkata"


def test_aware_datetime_is_rejected() -> None:
    """An aware datetime would bypass historical-offset resolution silently."""
    from datetime import timezone

    with pytest.raises(ValueError, match="naive local datetime"):
        BirthData(
            when=datetime(1990, 5, 15, 6, 30, tzinfo=timezone.utc),
            latitude=13.0827, longitude=80.2707,
        )


def test_ketu_is_exactly_opposite_rahu(case) -> None:
    _label, chart, _, _ = case
    sep = (chart.grahas[8].longitude - chart.grahas[7].longitude) % 360.0
    assert sep == pytest.approx(180.0, abs=1e-9)


def test_kp_ayanamsa_shifts_every_graha_equally() -> None:
    """Switching ayanamsa must translate the whole chart rigidly.

    If it did not, some downstream code would be mixing frames.
    """
    bd = BirthData(
        when=datetime(1990, 5, 15, 6, 30),
        latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
    )
    lahiri = pos.compute(bd, ay.Ayanamsa.LAHIRI)
    kp = pos.compute(bd, ay.Ayanamsa.KP)

    # KP ayanamsa is the smaller value, so KP sidereal longitudes are the
    # larger ones; the signed shift is therefore positive in this direction.
    shifts = [
        (kp.grahas[gi].longitude - lahiri.grahas[gi].longitude + 180.0) % 360.0 - 180.0
        for gi in range(9)
    ]
    assert max(shifts) - min(shifts) < 1e-9, "ayanamsa change is not a rigid translation"
    # ~5'49" between Lahiri and KP.
    assert 0.08 < shifts[0] < 0.11, f"Lahiri/KP separation {shifts[0] * 60:.3f} arcmin"
