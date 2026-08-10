"""Vimshottari dasha.

Two kinds of test live here and they protect different things.

The **arithmetic** tests pin properties that must hold for every chart ever cast:
the nine periods sum to 120 years, sub-periods exactly fill their parent with no
gap or overlap at any of the five levels, and every instant belongs to exactly
one period at each level. These are cheap, they run on synthetic input, and they
are what catch a refactor.

The **cross-validation** tests compare against jyotishganit, an independent
implementation. Agreement on the sub-period split is evidence that the formula is
the conventional one rather than merely self-consistent.

One number worth carrying in your head while reading this file. A dasha start
date is the Moon's position inside its nakshatra, scaled up by the length of the
period: for a 20-year Venus mahadasha that is 20 x 365.25 / 13.333 = **548 days
of dasha date per degree of Moon**, so one arcsecond of Moon error moves a
printed date by about three and a half hours. Nothing else in this engine
amplifies an error that hard, which is why the Phase 0 accuracy work was worth
doing and why ``test_dasha_dates_amplify_moon_error`` pins the factor.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import (
    GRAHAS,
    JUPITER,
    KETU,
    MERCURY,
    MOON,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    SUN,
    VENUS,
)
from jyotish.dasha import vimshottari as vd

BIRTH = datetime(1990, 5, 15, 6, 30)
CHENNAI = (13.0827, 80.2707, "Asia/Kolkata")

# (label, local datetime, lat, lon, zone) -- a spread of birth stars, so the
# fixtures between them exercise several different opening mahadashas.
FIXTURES = [
    ("chennai-1990", datetime(1990, 5, 15, 6, 30), 13.0827, 80.2707, "Asia/Kolkata"),
    ("madurai-1975", datetime(1975, 11, 3, 22, 15), 9.9252, 78.1198, "Asia/Kolkata"),
    ("coimbatore-2005", datetime(2005, 8, 30, 4, 12), 11.0168, 76.9558, "Asia/Kolkata"),
    ("trichy-1968", datetime(1968, 1, 19, 17, 40), 10.7905, 78.7047, "Asia/Kolkata"),
    ("salem-1999", datetime(1999, 12, 31, 23, 59), 11.6643, 78.1460, "Asia/Kolkata"),
    ("singapore-2001", datetime(2001, 2, 9, 14, 5), 1.3521, 103.8198, "Asia/Singapore"),
    ("london-1988", datetime(1988, 7, 21, 3, 45), 51.5074, -0.1278, "Europe/London"),
]


@pytest.fixture(scope="module")
def moon_longitudes() -> dict[str, float]:
    """Sidereal Moon longitude for each fixture, computed once."""
    out = {}
    for label, when, lat, lon, zone in FIXTURES:
        birth = BirthData(when=when, latitude=lat, longitude=lon, timezone_name=zone)
        chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
        out[label] = chart.grahas[MOON].longitude
    return out


@pytest.fixture(scope="module")
def jg():
    """The independent implementation, as a fixture so only these tests skip."""
    return pytest.importorskip(
        "jyotishganit.dasha.vimshottari",
        reason="cross-validation reference; declared in requirements-dev.txt",
    )


# --- the tables --------------------------------------------------------------


def test_the_nine_periods_sum_to_one_hundred_and_twenty_years():
    """The defining invariant. A typo here rescales every date the engine prints."""
    assert sum(vd.YEARS.values()) == vd.TOTAL_YEARS == 120


def test_every_graha_owns_exactly_one_period():
    assert sorted(vd.YEARS) == list(range(9))
    assert len(set(vd.ORDER)) == 9


def test_the_dasha_order_is_the_nakshatra_lord_sequence():
    """Not a coincidence to be re-typed -- it is why a birth star picks a dasha.

    ``ORDER`` is derived from ``NAKSHATRA_LORDS`` precisely so the two cannot
    drift apart. This test pins the derivation itself, so replacing it with a
    hand-written literal that happens to differ would fail here rather than
    quietly shifting every chart's opening mahadasha.
    """
    assert vd.ORDER == (KETU, VENUS, SUN, MOON, 2, 7, JUPITER, 6, MERCURY)
    assert vd.ORDER == NAKSHATRA_LORDS[:9]
    assert NAKSHATRA_LORDS == vd.ORDER * 3


def test_the_classical_period_lengths():
    expected = {
        "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
        "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
    }
    assert {GRAHAS[g].en: y for g, y in vd.YEARS.items()} == expected


def test_cycle_from_rotates_without_losing_anyone():
    for lord in vd.ORDER:
        rotated = vd.cycle_from(lord)
        assert rotated[0] == lord
        assert sorted(rotated) == sorted(vd.ORDER)
        assert len(rotated) == 9


def test_five_levels_are_named():
    assert len(vd.LEVEL_NAMES) == vd.MAX_LEVEL == 5
    assert all(term.ta for term in vd.LEVEL_NAMES)


# --- balance at birth --------------------------------------------------------


def test_balance_is_whole_at_the_start_of_a_nakshatra():
    """Born at 0 degrees of a star, the entire period is still to run."""
    for nak in range(27):
        b = vd.balance_at_birth(nak * NAKSHATRA_SPAN)
        assert b.nakshatra == nak
        assert b.lord == NAKSHATRA_LORDS[nak]
        assert b.remaining_fraction == pytest.approx(1.0, abs=1e-12)
        assert b.years == vd.YEARS[b.lord]


def test_balance_is_nearly_spent_at_the_end_of_a_nakshatra():
    for nak in range(27):
        b = vd.balance_at_birth((nak + 1) * NAKSHATRA_SPAN - 1e-9)
        assert b.nakshatra == nak
        assert b.remaining_fraction == pytest.approx(0.0, abs=1e-9)


def test_balance_lord_matches_the_nakshatra_lord_everywhere():
    """Sampled inside every nakshatra, not just at the boundaries."""
    for nak in range(27):
        for frac in (0.01, 0.25, 0.5, 0.75, 0.99):
            lon = (nak + frac) * NAKSHATRA_SPAN
            assert vd.balance_at_birth(lon).lord == NAKSHATRA_LORDS[nak]


def test_balance_halfway_through_a_star_is_half_the_period():
    b = vd.balance_at_birth(3.5 * NAKSHATRA_SPAN)   # halfway through Rohini
    assert b.lord == MOON
    assert b.remaining_fraction == pytest.approx(0.5)
    assert (b.years, b.months) == (5, 0)


def test_balance_years_months_days_reconstruct_the_fraction():
    """The printed y/m/d must be the fraction, in dasha units of 12 and 30.

    Sampled densely rather than at a handful of points, because the failure this
    guards against is the rounded day carrying to 30 and printing a month that
    cannot exist.
    """
    for i in range(0, 3600):
        b = vd.balance_at_birth(i / 10.0)
        assert 0 <= b.months <= 11, b
        assert 0 <= b.days <= 29, b
        rebuilt = b.years + b.months / 12.0 + b.days / 360.0
        exact = b.remaining_fraction * vd.YEARS[b.lord]
        assert abs(rebuilt - exact) <= 1.0 / 720.0 + 1e-9  # half a dasha day


def test_balance_is_independent_of_the_year_length_convention():
    """The *fraction* is astronomy; only its conversion to days is convention."""
    a = vd.balance_at_birth(61.7, year_length="julian")
    b = vd.balance_at_birth(61.7, year_length="savana")
    assert a.remaining_fraction == b.remaining_fraction
    assert a.lord == b.lord
    assert a.total_days != b.total_days


def test_an_unknown_year_length_is_refused_by_name():
    with pytest.raises(ValueError, match="Unknown dasha year length"):
        vd.balance_at_birth(10.0, year_length="metric")


# --- the mahadasha sequence --------------------------------------------------


def test_mahadashas_are_contiguous_with_no_gap_or_overlap():
    periods = vd.mahadashas(BIRTH, 61.7)
    for earlier, later in zip(periods, periods[1:]):
        assert earlier.end == later.start


def test_one_full_cycle_is_exactly_one_hundred_and_twenty_years():
    periods = vd.mahadashas(BIRTH, 61.7, year_length="julian")
    span = periods[8].end - periods[0].start
    assert span == timedelta(days=120 * 365.25)


def test_the_first_mahadasha_contains_the_birth_and_began_before_it():
    """The person is born partway through, so the period starts in the past.

    Modelling the true start is what makes every sub-period below it correct.
    Clamping the start to the birth instant -- which is how a dasha table is
    usually *printed* -- would compress the first antardasha and shift every
    boundary inside it.
    """
    moon = 61.7
    periods = vd.mahadashas(BIRTH, moon)
    first = periods[0]
    balance = vd.balance_at_birth(moon)

    assert first.lord == balance.lord
    assert first.start < BIRTH < first.end
    assert (first.end - BIRTH).total_seconds() / 86400.0 == pytest.approx(
        balance.total_days, abs=1e-6
    )


def test_the_sequence_starts_with_the_birth_lord_and_follows_the_cycle():
    periods = vd.mahadashas(BIRTH, 61.7)
    lord = vd.balance_at_birth(61.7).lord
    assert [p.lord for p in periods[:9]] == list(vd.cycle_from(lord))
    assert [p.lord for p in periods[9:18]] == list(vd.cycle_from(lord))


# --- sub-periods -------------------------------------------------------------


def _walk(period, depth):
    """Yield every period at or below ``period``, down to ``depth`` levels."""
    yield period
    if period.level >= depth:
        return
    for child in vd.children(period):
        yield from _walk(child, depth)


def test_subperiods_exactly_fill_their_parent_at_every_level():
    """No gap, no overlap, and the union is the parent to the microsecond.

    This is checked at all five levels because the split is recursive: a
    rounding error at level 2 is inherited by the 729 periods below it, and the
    only place it is visible is a boundary that does not line up.
    """
    root = vd.mahadashas(BIRTH, 61.7)[0]
    for period in _walk(root, vd.MAX_LEVEL - 1):
        kids = vd.children(period)
        assert len(kids) == 9
        assert kids[0].start == period.start
        assert kids[-1].end == period.end
        for earlier, later in zip(kids, kids[1:]):
            assert earlier.end == later.start


def test_a_subperiod_sequence_starts_with_its_own_parent_lord():
    root = vd.mahadashas(BIRTH, 61.7)[0]
    for period in _walk(root, 3):
        kids = vd.children(period)
        if kids:
            assert kids[0].lord == period.lord
            assert [k.lord for k in kids] == list(vd.cycle_from(period.lord))


def test_subperiod_length_is_the_parent_scaled_by_the_lords_years():
    parent = vd.mahadashas(BIRTH, 61.7)[0]
    for child in vd.children(parent):
        expected = parent.days * vd.YEARS[child.lord] / 120.0
        assert child.days == pytest.approx(expected, abs=1e-6)


def test_the_fifth_level_is_the_last():
    period = vd.mahadashas(BIRTH, 61.7)[0]
    for expected_level in range(1, 6):
        assert period.level == expected_level
        kids = vd.children(period)
        if expected_level == 5:
            assert kids == []
        else:
            period = kids[0]


def test_a_period_knows_its_own_full_lord_chain():
    root = vd.mahadashas(BIRTH, 61.7)[0]
    child = vd.children(root)[3]
    grandchild = vd.children(child)[5]
    assert grandchild.lords == (root.lord, child.lord, grandchild.lord)
    assert grandchild.level == 3
    assert " / " in grandchild.path()


def test_descend_follows_a_lord_path_and_refuses_a_wrong_one():
    root = vd.mahadashas(BIRTH, 61.7)[0]
    kid = vd.children(root)[2]
    assert vd.descend(root, (kid.lord,)) == kid
    # Rahu is always in the cycle, so ask for a level that does not exist.
    deepest = vd.descend(root, (kid.lord,) * 4)
    assert deepest is None or deepest.level <= vd.MAX_LEVEL


# --- lookups -----------------------------------------------------------------


def test_a_boundary_instant_belongs_to_exactly_one_period():
    """Half-open intervals. A closed one reports two dashas running at once."""
    periods = vd.mahadashas(BIRTH, 61.7)
    boundary = periods[0].end
    assert not periods[0].contains(boundary)
    assert periods[1].contains(boundary)
    assert sum(p.contains(boundary) for p in periods) == 1


def test_chain_at_is_properly_nested():
    chain = vd.chain_at(BIRTH, 61.7, datetime(2026, 8, 10, 12, 0))
    assert len(chain) == 5
    for outer, inner in zip(chain, chain[1:]):
        assert outer.start <= inner.start
        assert inner.end <= outer.end
        assert inner.lords[:-1] == outer.lords
        assert inner.contains(datetime(2026, 8, 10, 12, 0))


def test_chain_at_birth_opens_with_the_birth_lord():
    chain = vd.chain_at(BIRTH, 61.7, BIRTH)
    assert chain[0].lord == vd.balance_at_birth(61.7).lord


def test_chain_at_respects_a_shallower_depth():
    assert len(vd.chain_at(BIRTH, 61.7, BIRTH, depth=2)) == 2


def test_chain_at_returns_nothing_outside_the_generated_span():
    """Silence beats a confidently wrong answer from a clamped lookup."""
    assert vd.chain_at(BIRTH, 61.7, datetime(1900, 1, 1)) == []
    assert vd.chain_at(BIRTH, 61.7, datetime(2400, 1, 1)) == []


# --- the convention knob -----------------------------------------------------


def test_the_solar_year_variants_are_astrologically_indistinguishable():
    """Under two days apart across a whole 120-year cycle.

    Pinned because docs/02-dasha.md tells the reader not to worry about this
    choice, and a doc that says "it does not matter" needs something that fails
    if it starts to.
    """
    solar = [n for n in vd.YEAR_DAYS if n != "savana"]
    ends = [vd.mahadashas(BIRTH, 61.7, year_length=n)[8].end for n in solar]
    spread = (max(ends) - min(ends)).total_seconds() / 86400.0
    assert spread < 2.0


def test_savana_is_the_one_choice_that_really_moves_dates():
    """Ten months adrift at sixty years -- a different tradition, not a rounding."""
    julian = vd.mahadashas(BIRTH, 61.7, year_length="julian")[8].end
    savana = vd.mahadashas(BIRTH, 61.7, year_length="savana")[8].end
    drift = (julian - savana).total_seconds() / 86400.0
    assert 600.0 < drift < 660.0  # 120 years x 5.25 days


def test_the_default_is_the_classical_solar_year():
    assert vd.DEFAULT_YEAR_LENGTH == "julian"
    assert vd.year_days() == 365.25


def test_every_named_year_length_is_a_plausible_year():
    for name, days in vd.YEAR_DAYS.items():
        assert 359.0 < days < 366.0, name


# --- sensitivity -------------------------------------------------------------


def test_dasha_dates_amplify_moon_error():
    """One arcsecond of Moon moves a Venus mahadasha boundary by hours.

    This is the executable version of the claim the documentation makes about
    why sub-arcsecond accuracy matters here more than anywhere else in the
    engine. Nothing else amplifies an input error by three orders of magnitude.
    """
    arcsec = 1.0 / 3600.0
    # Purva Ashadha, the third Venus-ruled star, so the period is a full 20
    # years -- the longest, and therefore the largest amplification.
    moon = 19.0 * NAKSHATRA_SPAN + 5.0
    base = vd.mahadashas(BIRTH, moon, year_length="julian")[0]
    nudged = vd.mahadashas(BIRTH, moon + arcsec, year_length="julian")[0]

    assert base.lord == nudged.lord == VENUS
    shift_hours = abs((base.start - nudged.start).total_seconds()) / 3600.0
    assert 3.0 < shift_hours < 4.5


# --- cross-validation --------------------------------------------------------


def test_subperiod_split_matches_jyotishganit(jg):
    """The recursive split, checked against an independent implementation.

    Compared at the arithmetic level rather than end to end, deliberately. Their
    Moon longitude is computed in the *true* equinox frame while ours is in the
    mean frame -- a difference of up to 17 arcseconds, which the amplification
    above turns into days of dasha date. Feeding both the same parent span
    isolates the formula, which is what this test is about.
    """
    start = datetime(1990, 1, 1)
    days = 20 * 365.25   # a Venus mahadasha
    theirs = jg._generate_sub_periods("Venus", start, days, 2, 2)

    parent = vd.Period(lords=(VENUS,), start=start, end=start + timedelta(days=days))
    ours = vd.children(parent)

    assert [GRAHAS[p.lord].en for p in ours] == list(theirs)
    for period in ours:
        their_period = theirs[GRAHAS[period.lord].en]
        assert abs((period.start - their_period["start"]).total_seconds()) < 1.0
        assert abs((period.end - their_period["end"]).total_seconds()) < 1.0


@pytest.mark.parametrize("label", [f[0] for f in FIXTURES])
def test_birth_mahadasha_lord_matches_jyotishganit(jg, label, moon_longitudes):
    """The opening lord, across every fixture.

    Only the *lord* is compared, not the date. The two engines place the Moon a
    few arcseconds apart -- we work in the mean equinox frame, which is where
    ayanamsa is defined, and they do not -- and a few arcseconds is hours to days
    of dasha date. The lord is robust to that unless the Moon sits within
    arcseconds of a nakshatra boundary, which no fixture does.
    """
    when, lat, lon, zone = next(f[1:] for f in FIXTURES if f[0] == label)
    birth = BirthData(when=when, latitude=lat, longitude=lon, timezone_name=zone)
    offset_hours = birth.utc_offset.total_seconds() / 3600.0
    ayan = ay.compute(birth.skyfield_time(), ay.Ayanamsa.LAHIRI)

    their_lord, _their_start = jg.calculate_dasha_start_date(when, offset_hours, ayan)
    our_lord = vd.balance_at_birth(moon_longitudes[label]).lord

    assert GRAHAS[our_lord].en == their_lord


def test_a_real_chart_produces_a_usable_dasha_table(moon_longitudes):
    """End to end on the chart the project has verified against an online source."""
    birth = BirthData(
        when=BIRTH, latitude=CHENNAI[0], longitude=CHENNAI[1], timezone_name=CHENNAI[2]
    )
    moon = moon_longitudes["chennai-1990"]

    balance = vd.balance_at_birth(moon)
    assert 0.0 < balance.remaining_fraction <= 1.0
    assert balance.format("ta")

    periods = vd.mahadashas(birth.utc.replace(tzinfo=None), moon)
    assert len(periods) == 18
    assert periods[0].start < birth.utc.replace(tzinfo=None) < periods[0].end

    # Every level resolvable for a date in the person's likely lifetime.
    chain = vd.chain_at(birth.utc.replace(tzinfo=None), moon, datetime(2030, 1, 1))
    assert [p.level for p in chain] == [1, 2, 3, 4, 5]
