"""Graha dignity: உச்சம், நீசம், மூலத்திரிகோணம், ஆட்சி and the friendships.

The tables here are small, fixed and entirely checkable against a textbook, so
the tests are mostly about pinning them — a rotated or mistyped row would rename
the state of a graha on every chart the app ever draws while breaking nothing
else.

Two invariants are worth more than the individual rows. Debilitation is *derived*
as exaltation plus 180 degrees rather than tabulated, so the two can never
disagree. And the natural friendship relation is deliberately **asymmetric**;
a test asserts the asymmetry so that nobody "tidies" the table into symmetry.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core import dignity as dg
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import (
    GRAHAS,
    JUPITER,
    KETU,
    MARS,
    MERCURY,
    MOON,
    RASI_SPAN,
    RAHU,
    SATURN,
    SUN,
    VENUS,
)

VISIBLE = (SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN)


def at(rasi: int, degree: float) -> float:
    return rasi * RASI_SPAN + degree


# --- the tables --------------------------------------------------------------


def test_the_seven_classical_exaltation_points():
    """Sign and degree, as every textbook prints them."""
    expected = {
        SUN: (0, 10.0),        # Mesham 10
        MOON: (1, 3.0),        # Rishabam 3
        MARS: (9, 28.0),       # Magaram 28
        MERCURY: (5, 15.0),    # Kanni 15
        JUPITER: (3, 5.0),     # Kadagam 5
        VENUS: (11, 27.0),     # Meenam 27
        SATURN: (6, 20.0),     # Thulam 20
    }
    for graha, (rasi, degree) in expected.items():
        assert dg.exaltation_point(graha) == pytest.approx(at(rasi, degree))


def test_debilitation_is_derived_from_exaltation_not_tabulated():
    """Exactly opposite, by definition. Two tables could drift; one cannot."""
    for graha in VISIBLE:
        exalt = dg.exaltation_point(graha)
        debil = dg.debilitation_point(graha)
        assert debil == pytest.approx((exalt + 180.0) % 360.0)
        # And the signs are opposite, which is the form a reader checks.
        assert (int(debil // RASI_SPAN) - int(exalt // RASI_SPAN)) % 12 == 6


def test_the_nodes_are_left_unassigned_rather_than_guessed():
    """BPHS gives them no exaltation and later practice splits two ways."""
    for node in (RAHU, KETU):
        assert dg.exaltation_point(node) is None
        result = dg.assess(node, at(1, 15.0))
        assert result.dignity is dg.Dignity.UNDEFINED
        assert result.from_exaltation is None
        assert "split" in result.reason
        # It still has a dispositor, which is real information.
        assert result.dispositor == VENUS


def test_every_state_has_a_tamil_name():
    for state in dg.Dignity:
        assert dg.DIGNITY_NAMES[state].ta.strip()
    assert dg.DIGNITY_NAMES[dg.Dignity.DEBILITATED].ta == "நீசம்"
    assert dg.DIGNITY_NAMES[dg.Dignity.EXALTED].ta == "உச்சம்"
    assert dg.DIGNITY_NAMES[dg.Dignity.OWN].ta == "ஆட்சி"


def test_natural_friendship_is_asymmetric_and_must_stay_so():
    """Mercury is an enemy of the Moon; the Moon is only neutral to Mercury.

    Making this table symmetric would look like a tidy-up and would change the
    dignity of real placements. The asymmetry is the classical relation.
    """
    assert MERCURY in dg.ENEMIES[MOON] or MOON in dg.ENEMIES[MERCURY]
    assert MOON in dg.ENEMIES[MERCURY]
    assert MERCURY not in dg.ENEMIES[MOON]
    assert MERCURY in dg.FRIENDS[MOON]


def test_no_graha_is_both_its_own_friend_and_enemy():
    for graha in VISIBLE:
        assert not (dg.FRIENDS[graha] & dg.ENEMIES[graha]), GRAHAS[graha].en
        assert graha not in dg.FRIENDS[graha]
        assert graha not in dg.ENEMIES[graha]


def test_moolatrikona_lies_in_the_own_sign_for_everyone_but_the_moon():
    """The Moon's is in Rishabam — its *exaltation* sign, not Kadagam.

    A genuine classical exception rather than a slip, and exactly the kind of
    thing a "surely this is uniform" refactor would quietly correct into being
    wrong.
    """
    from jyotish.core.zodiac import RASI_LORDS

    for graha, (rasi, low, high) in dg.MOOLATRIKONA.items():
        assert 0.0 <= low < high <= 30.0, GRAHAS[graha].en
        if graha is MOON:
            assert rasi == 1                                  # Rishabam
            assert rasi == int(dg.exaltation_point(MOON) // RASI_SPAN)
            assert RASI_LORDS[rasi] == VENUS                  # not the Moon
        else:
            assert RASI_LORDS[rasi] == graha, GRAHAS[graha].en


# --- the ladder --------------------------------------------------------------


def test_a_graha_at_its_exaltation_point_is_exalted():
    for graha in VISIBLE:
        result = dg.assess(graha, dg.exaltation_point(graha))
        assert result.is_exalted, GRAHAS[graha].en
        assert result.from_exaltation == pytest.approx(0.0)


def test_a_graha_at_its_debilitation_point_is_debilitated():
    for graha in VISIBLE:
        result = dg.assess(graha, dg.debilitation_point(graha))
        assert result.is_debilitated, GRAHAS[graha].en
        assert result.from_exaltation == pytest.approx(180.0)
        assert result.name.ta == "நீசம்"


def test_the_whole_sign_carries_the_dignity_not_just_the_degree():
    """Saturn anywhere in Thulam is exalted; the degree only says how much."""
    for degree in (0.0, 5.0, 20.0, 29.9):
        assert dg.assess(SATURN, at(6, degree)).is_exalted
        assert dg.assess(SATURN, at(0, degree)).is_debilitated


def test_moolatrikona_outranks_plain_own_sign():
    # Saturn's moolatrikona is Kumbam 0-20; beyond that it is simply its own.
    assert dg.assess(SATURN, at(10, 10.0)).dignity is dg.Dignity.MOOLATRIKONA
    assert dg.assess(SATURN, at(10, 25.0)).dignity is dg.Dignity.OWN
    # And its other own sign, Magaram, has no moolatrikona portion at all.
    assert dg.assess(SATURN, at(9, 10.0)).dignity is dg.Dignity.OWN


def test_friend_neutral_and_enemy_signs():
    # Sun in Dhanusu, ruled by Jupiter, a friend.
    assert dg.assess(SUN, at(8, 10.0)).dignity is dg.Dignity.FRIEND
    # Sun in Magaram, ruled by Saturn, an enemy.
    assert dg.assess(SUN, at(9, 10.0)).dignity is dg.Dignity.ENEMY
    # Sun in Mithunam, ruled by Mercury, neutral.
    assert dg.assess(SUN, at(2, 10.0)).dignity is dg.Dignity.NEUTRAL


def test_mercury_in_kanni_is_treated_as_exalted():
    """The documented precedence for the one sign that is all three at once."""
    result = dg.assess(MERCURY, at(5, 18.0))
    assert result.is_exalted
    assert "exaltation sign" in result.reason


def test_every_graha_gets_a_state_at_every_longitude():
    """No gap in the ladder anywhere on the circle."""
    for graha in range(9):
        for step in range(0, 3600):
            result = dg.assess(graha, step / 10.0)
            assert isinstance(result.dignity, dg.Dignity)
            assert result.reason
            if graha in VISIBLE:
                assert result.dignity is not dg.Dignity.UNDEFINED


def test_the_reason_names_the_rule_that_fired():
    assert "exaltation sign" in dg.assess(SATURN, at(6, 20.0)).reason
    assert "debilitation sign" in dg.assess(SATURN, at(0, 20.0)).reason
    assert "moolatrikona" in dg.assess(SATURN, at(10, 5.0)).reason
    assert "own sign" in dg.assess(SATURN, at(9, 5.0)).reason
    assert "natural friend" in dg.assess(SUN, at(8, 5.0)).reason


# --- combustion --------------------------------------------------------------


def test_a_graha_beside_the_sun_is_combust():
    sun = at(4, 10.0)
    assert dg.assess(MARS, at(4, 12.0), sun_longitude=sun).combust
    assert not dg.assess(MARS, at(4, 29.0), sun_longitude=sun).combust


def test_retrograde_venus_and_mercury_use_the_tighter_bound():
    """The one place the retrograde flag changes a dignity result.

    Those two spend much of their retrograde time close to the Sun, which is
    exactly the combination the tighter bound exists to separate.
    """
    sun = at(4, 10.0)
    nine_degrees_away = at(4, 19.0)
    assert dg.assess(VENUS, nine_degrees_away, sun_longitude=sun).combust
    assert not dg.assess(
        VENUS, nine_degrees_away, sun_longitude=sun, retrograde=True
    ).combust


def test_the_sun_and_the_nodes_are_never_combust():
    sun = at(4, 10.0)
    for graha in (SUN, RAHU, KETU):
        assert not dg.assess(graha, at(4, 11.0), sun_longitude=sun).combust


def test_combustion_is_measured_across_the_zero_seam():
    assert dg.assess(JUPITER, at(0, 2.0), sun_longitude=at(11, 27.0)).combust


def test_without_a_sun_longitude_nothing_is_combust():
    assert not dg.assess(MARS, at(4, 11.0)).combust


# --- against a real chart ----------------------------------------------------


def test_a_real_chart_gets_a_dignity_for_every_graha():
    birth = BirthData(
        when=datetime(1990, 5, 15, 6, 30), latitude=13.0827, longitude=80.2707,
        timezone_name="Asia/Kolkata",
    )
    chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
    dignities = dg.assess_chart(chart)

    assert sorted(dignities) == list(range(9))
    for graha, result in dignities.items():
        assert result.graha == graha
        assert result.reason
        if graha in VISIBLE:
            assert result.dignity is not dg.Dignity.UNDEFINED
        # The dispositor must be the lord of the rasi the graha actually sits in.
        from jyotish.core.zodiac import RASI_LORDS
        assert result.dispositor == RASI_LORDS[chart.grahas[graha].position.rasi]


def test_vargottama_reports_every_graha_and_the_lagna():
    """Key -1 is the lagna, which Tamil treats as vargottama in its own right."""
    from jyotish.charts import vargas

    birth = BirthData(
        when=datetime(1990, 5, 15, 6, 30), latitude=13.0827, longitude=80.2707,
        timezone_name="Asia/Kolkata",
    )
    chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
    flags = dg.vargottama(chart)

    assert sorted(flags) == [-1] + list(range(9))
    assert all(isinstance(v, bool) for v in flags.values())

    # Cross-checked against the varga module rather than restated from it.
    navamsa = vargas.compute(chart, "D9")
    for graha in range(9):
        assert flags[graha] == (
            navamsa.graha_rasis[graha] == chart.grahas[graha].position.rasi
        )
    assert flags[-1] == (navamsa.lagna_rasi == chart.lagna.rasi)


def test_vargottama_is_rare_but_not_impossible():
    """A sweep, so the function cannot be trivially always-False.

    One rasi in nine matches by chance, so across enough charts some graha must
    come out vargottama. A test that only ever saw False would pass on a
    function that returned False unconditionally.
    """
    seen_true = seen_false = False
    for day in range(1, 28, 3):
        chart = pos.compute(
            BirthData(
                when=datetime(1990, 5, day, 6, 30), latitude=13.0827,
                longitude=80.2707, timezone_name="Asia/Kolkata",
            ),
            ay.Ayanamsa.LAHIRI,
        )
        for value in dg.vargottama(chart).values():
            seen_true |= value
            seen_false |= not value
    assert seen_true and seen_false


def test_the_vargottama_tamil_is_the_doubled_ka_form():
    """வர்க்கோத்தமம், not வர்கோத்தமம் — the rival is real, not a typo.

    Adityaguruji derives the doubled form: வர்க்கம் + உத்தமம் → வர்க்கோத்தமம்.
    """
    assert dg.VARGOTTAMA.ta == "வர்க்கோத்தமம்"
    assert dg.NEECHA_VARGOTTAMA.ta.startswith("நீச ")   # not நீச்ச


def test_dignity_is_independent_of_the_house_it_falls_in():
    """It is a sign relationship, so it cannot depend on the lagna.

    Two births hours apart share every graha's dignity while the bhavas rotate
    right around. Getting this wrong -- by keying anything off the house -- is
    a plausible mistake that no single chart would expose.
    """
    def dignities_for(hour: int) -> dict[int, dg.Dignity]:
        birth = BirthData(
            when=datetime(1990, 5, 15, hour, 30), latitude=13.0827,
            longitude=80.2707, timezone_name="Asia/Kolkata",
        )
        chart = pos.compute(birth, ay.Ayanamsa.LAHIRI)
        return {g: d.dignity for g, d in dg.assess_chart(chart).items()}

    morning = dignities_for(6)
    evening = dignities_for(18)
    assert morning == evening
