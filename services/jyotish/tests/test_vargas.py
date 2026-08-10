"""Divisional charts (vargas), with D9 Navamsam as the headline.

Vargas are pure arithmetic on longitudes, so they add no astronomical risk --
but they are easy to get subtly wrong, and a wrong Navamsam is immediately
visible to anyone who practises. The strategy here is cross-validation: our
rules are derived from the classical texts, and jyotishganit's are an
independent implementation, so agreement between the two is evidence rather
than an assumption.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from jyotish.charts import vargas
from jyotish.core import ayanamsa as ay
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import RASI_SPAN

jg = pytest.importorskip(
    "jyotishganit.components.divisional_charts",
    reason="cross-validation reference",
)

JG_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

#: Divisions where we and jyotishganit must agree exactly. D30 is excluded and
#: handled separately below -- see test_trimsamsa_deviation_from_jyotishganit.
CROSS_CHECKED = {
    "D2": "hora_from_long",
    "D3": "drekkana_from_long",
    "D4": "chaturtamsa_from_long",
    "D7": "saptamsa_from_long",
    "D9": "navamsa_from_long",
    "D10": "dasamsa_from_long",
    "D12": "dwadasamsa_from_long",
    "D16": "shodasamsa_from_long",
    "D20": "vimsamsa_from_long",
    "D24": "chaturvimsamsa_from_long",
    "D27": "sapta_vimsamsa_from_long",
    "D40": "khavedamsa_from_long",
    "D45": "akshavedamsa_from_long",
    "D60": "shashtiamsa_from_long",
}

#: Sample points per sign, deliberately including exact part boundaries. The
#: 20-degree entry is not decorative: it is precisely a navamsa boundary, and it
#: caught a real floating-point bug where 30/9 being inexact floored 20 degrees
#: into the previous navamsa.
STEPS = [0.0, 0.01, 0.7, 1.3, 2.4, 3.3, 10 / 3, 3.34, 5.0, 5.01, 7.4, 7.5,
         9.99, 10.0, 12.5, 14.99, 15.0, 17.9, 18.0, 20.0, 22.5, 24.99,
         25.0, 27.5, 29.99]


def _theirs(func_name: str, rasi: int, degrees: float) -> int:
    _num, sign_str, _deg = getattr(jg, func_name)(JG_SIGNS[rasi], degrees)
    return JG_SIGNS.index(sign_str)


def _sample_points():
    """(rasi, degrees, longitude) triples that name exactly one point.

    We take an absolute longitude and derive the degrees-within-rasi *back* from
    it, rather than passing the original step. Building ``rasi * 30 + step`` and
    then handing the untouched ``step`` to the reference implementation compares
    two different points: for rasi 3 and step 10/3, the round trip yields
    3.3333333333333286 while the original step is 3.3333333333333335, and those
    two straddle an exact division boundary. The difference is 5e-15 degrees and
    astrologically meaningless, but it makes the comparison meaningless too.
    """
    for rasi in range(12):
        for step in STEPS:
            longitude = rasi * RASI_SPAN + step
            yield rasi, longitude - rasi * RASI_SPAN, longitude


@pytest.mark.parametrize("code", sorted(CROSS_CHECKED))
def test_agrees_with_independent_implementation(code: str) -> None:
    for rasi, degrees, longitude in _sample_points():
        ours = vargas.varga_rasi(longitude, code)
        theirs = _theirs(CROSS_CHECKED[code], rasi, degrees)
        assert ours == theirs, (
            f"{code} at rasi {rasi} + {degrees} deg: ours={ours} theirs={theirs}"
        )


# --- D9 Navamsa, the one users actually check -------------------------------

def _navamsa_longhand(longitude: float) -> int:
    """D9 written out from the classical rule, for comparison.

    Movable signs start counting from themselves, fixed signs from the 9th sign,
    dual signs from the 5th. The shipped implementation uses continuous counting
    instead; this exists to prove the two are the same thing.

    The (rasi, part) decomposition is shared with the implementation on purpose.
    What is under test is the *starting-sign rule*, not floating-point
    decomposition -- giving this helper its own arithmetic would only re-test
    binary representation and would disagree at exact boundaries for reasons
    that have nothing to do with Jyotish.
    """
    rasi, part = vargas._split(longitude, 9)
    if vargas.is_movable(rasi):
        start = rasi
    elif vargas.is_fixed(rasi):
        start = (rasi + 8) % 12
    else:
        start = (rasi + 4) % 12
    return (start + part) % 12


def test_navamsa_shortcut_equals_classical_rule() -> None:
    """The one-line form must reproduce movable/fixed/dual counting exactly."""
    for _rasi, _degrees, longitude in _sample_points():
        assert vargas.varga_rasi(longitude, "D9") == _navamsa_longhand(longitude), (
            f"longitude {longitude}"
        )


@pytest.mark.parametrize(
    "longitude,expected",
    [
        (0.0, vargas.ARIES),          # Aries is movable: first navamsa is Aries
        (30.0, vargas.CAPRICORN),     # Taurus is fixed: starts at the 9th
        (60.0, vargas.LIBRA),         # Gemini is dual: starts at the 5th
        (90.0, vargas.CANCER),        # Cancer is movable: starts at itself
        (20.0, vargas.LIBRA),         # exact navamsa boundary, Aries 20 deg
    ],
)
def test_navamsa_known_values(longitude: float, expected: int) -> None:
    assert vargas.varga_rasi(longitude, "D9") == expected


def test_navamsa_boundary_is_half_open() -> None:
    """A longitude exactly on a boundary belongs to the *following* navamsa."""
    boundary = 10 / 3  # end of the first navamsa of Aries
    assert vargas.varga_rasi(boundary - 1e-9, "D9") == vargas.ARIES
    assert vargas.varga_rasi(boundary, "D9") == vargas.TAURUS


def test_every_navamsa_of_aries_is_distinct_and_sequential() -> None:
    """Aries is movable, so its nine navamsas run Aries..Sagittarius in order."""
    got = [vargas.varga_rasi(i * (10 / 3) + 0.5, "D9") for i in range(9)]
    assert got == list(range(9))


# --- D30 Trimsamsa: a deliberate, documented deviation -----------------------

@pytest.mark.parametrize(
    "degrees,expected",
    [
        (2.0, vargas.ARIES),        # Mars 0-5
        (7.0, vargas.AQUARIUS),     # Saturn 5-10
        (14.0, vargas.SAGITTARIUS), # Jupiter 10-18
        (20.0, vargas.GEMINI),      # Mercury 18-25
        (27.0, vargas.LIBRA),       # Venus 25-30
    ],
)
def test_trimsamsa_odd_sign(degrees: float, expected: int) -> None:
    """Odd signs: Mars-Saturn-Jupiter-Mercury-Venus over 5/5/8/7/5 degrees."""
    assert vargas.varga_rasi(degrees, "D30") == expected  # Aries


@pytest.mark.parametrize(
    "degrees,expected",
    [
        (2.0, vargas.TAURUS),     # Venus 0-5
        (8.0, vargas.VIRGO),      # Mercury 5-12
        (16.0, vargas.PISCES),    # Jupiter 12-20
        (22.0, vargas.CAPRICORN), # Saturn 20-25
        (27.0, vargas.SCORPIO),   # Mars 25-30
    ],
)
def test_trimsamsa_even_sign(degrees: float, expected: int) -> None:
    """Even signs are the exact reverse: Venus-Mercury-Jupiter-Saturn-Mars,
    5/7/8/5/5, per Brihat Parashara Hora Shastra."""
    assert vargas.varga_rasi(RASI_SPAN + degrees, "D30") == expected  # Taurus


def test_trimsamsa_deviation_from_jyotishganit() -> None:
    """Pin the one place we knowingly differ from the reference implementation.

    jyotishganit puts Saturn at 12-19 and Jupiter at 19-24 in even signs, which
    swaps the pair and fails to mirror its own odd-sign sequence. BPHS makes the
    even-sign order the exact reverse of the odd one, so we follow the text.

    This test asserts the disagreement rather than skipping D30, so that if
    jyotishganit is ever corrected upstream we find out instead of drifting.
    """
    taurus_16 = RASI_SPAN + 16.0
    assert vargas.varga_rasi(taurus_16, "D30") == vargas.PISCES      # Jupiter
    assert _theirs("trimsamsa_from_long", 1, 16.0) == vargas.CAPRICORN  # Saturn


def test_trimsamsa_spans_sum_to_a_full_sign() -> None:
    """Both sequences must tile 30 degrees with no gap or overlap."""
    for rasi in (0, 1):  # one odd, one even
        seen = []
        for tenth in range(300):
            got = vargas.varga_rasi(rasi * RASI_SPAN + tenth / 10.0, "D30")
            if not seen or seen[-1] != got:
                seen.append(got)
        assert len(seen) == 5, f"rasi {rasi} produced {len(seen)} parts, expected 5"


# --- structure and integration ----------------------------------------------

def test_all_sixteen_divisions_present() -> None:
    assert len(vargas.VARGA_ORDER) == 16
    assert set(vargas.VARGA_ORDER) == set(vargas.VARGAS)


def test_d1_is_the_rasi_chart() -> None:
    for longitude in (0.0, 45.5, 123.4, 359.99):
        assert vargas.varga_rasi(longitude, "D1") == int(longitude // RASI_SPAN)


@pytest.mark.parametrize("code", vargas.VARGA_ORDER)
def test_every_varga_returns_a_valid_rasi(code: str) -> None:
    for tenth in range(0, 3600, 7):
        assert 0 <= vargas.varga_rasi(tenth / 10.0, code) <= 11


@pytest.mark.parametrize("code", vargas.VARGA_ORDER)
def test_longitude_wraps(code: str) -> None:
    """360 degrees is 0 degrees; nothing should behave oddly at the seam."""
    assert vargas.varga_rasi(360.0, code) == vargas.varga_rasi(0.0, code)
    assert vargas.varga_rasi(-30.0, code) == vargas.varga_rasi(330.0, code)


def test_unknown_varga_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown varga"):
        vargas.varga_rasi(0.0, "D5")


def test_varga_code_is_case_insensitive() -> None:
    assert vargas.varga_rasi(100.0, "d9") == vargas.varga_rasi(100.0, "D9")


def test_compute_builds_a_full_chart() -> None:
    birth = BirthData(
        when=datetime(1990, 5, 15, 6, 30),
        latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
    )
    chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
    d9 = vargas.compute(chart, "D9")

    assert d9.varga.code == "D9"
    assert d9.varga.name.ta == "நவாம்சம்"
    assert len(d9.graha_rasis) == 9
    assert 0 <= d9.lagna_rasi <= 11
    assert all(0 <= r <= 11 for r in d9.graha_rasis.values())

    # Houses are counted from the varga's own lagna, not the Rasi lagna.
    assert d9.house_of(0) == (d9.graha_rasis[0] - d9.lagna_rasi) % 12 + 1


def test_d1_varga_chart_matches_the_rasi_chart() -> None:
    """Computing D1 as a varga must reproduce the birth chart exactly."""
    birth = BirthData(
        when=datetime(1990, 5, 15, 6, 30),
        latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
    )
    chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
    d1 = vargas.compute(chart, "D1")

    assert d1.lagna_rasi == chart.lagna.rasi
    for gi, gp in chart.grahas.items():
        assert d1.graha_rasis[gi] == gp.position.rasi
        assert d1.house_of(gi) == chart.house_of(gi)


def test_retrogradation_carries_across_from_the_rasi_chart() -> None:
    """A varga is a remapping of longitudes; it cannot change actual motion."""
    birth = BirthData(
        when=datetime(1990, 5, 15, 6, 30),
        latitude=13.0827, longitude=80.2707, timezone_name="Asia/Kolkata",
    )
    chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
    expected = {gi for gi, gp in chart.grahas.items() if gp.retrograde}
    assert vargas.compute(chart, "D9").retrogrades == expected
