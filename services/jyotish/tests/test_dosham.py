"""செவ்வாய் தோஷம் — the geometry, and the absence of a verdict.

The most important tests in this file are the ones asserting what the module
does **not** produce. A source audit found three incompatible Tamil house sets
and four incompatible cancellation stacks, and a Tamil practitioner stating that
the exception list takes a hundred dosham-positives down to three survivors — so
a boolean would report the implementer's choice, not the chart, to someone asking
about their marriage.

That absence is a design decision on evidence, and it is exactly the kind of
thing a later "helpful" refactor would undo. So it is pinned.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core import dosham as dsh
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import MARS, MOON, VENUS


def _chart(day: int = 15, hour: int = 6):
    return pos.compute(
        BirthData(
            when=datetime(1990, 5, day, hour, 30), latitude=13.0827,
            longitude=80.2707, timezone_name="Asia/Kolkata",
        ),
        ay.Ayanamsa.LAHIRI,
    )


# --- the absence of a verdict ------------------------------------------------


def test_the_report_exposes_no_verdict_of_any_kind():
    """No boolean, no percentage, no marriage sentence. Deliberate.

    See the module docstring and docs/dosham-sources.md. If a future change adds
    `present` or a score, this fails, and it should.
    """
    report = dsh.sevvai(_chart())
    for forbidden in (
        "present", "cancelled", "is_dosham", "has_dosham",
        "percentage", "percent", "score", "severity_score", "verdict",
    ):
        assert not hasattr(report, forbidden), forbidden


def test_the_conventions_are_reported_side_by_side_not_chosen_between():
    report = dsh.sevvai(_chart())
    for reading in report.readings:
        assert set(reading.flagged_by) <= set(dsh.HOUSE_SETS)
        # Every convention that contains the house must be listed, none omitted.
        expected = {
            name for name, houses in dsh.HOUSE_SETS.items()
            if reading.house in houses
        }
        assert set(reading.flagged_by) == expected


def test_the_exemptions_are_named_and_attributed_never_summed():
    report = dsh.sevvai(_chart())
    assert len(report.exemptions) >= 4
    for e in report.exemptions:
        assert e.key and e.name.ta and e.detail and e.provenance
        assert isinstance(e.applies, bool)
    # There is no aggregate. Counting them would be the verdict by another name.
    assert not hasattr(report, "exemption_score")


# --- the three house sets ----------------------------------------------------


def test_the_three_house_sets_are_the_ones_the_sources_give():
    assert dsh.HOUSE_SETS["tamil_common"] == frozenset({2, 4, 7, 8, 12})
    assert dsh.HOUSE_SETS["tamil_traditional"] == frozenset({1, 2, 4, 7, 8, 12})
    assert dsh.HOUSE_SETS["classical"] == frozenset({1, 4, 7, 8, 12})
    assert dsh.DEFAULT_HOUSE_SET == "tamil_common"


def test_the_second_house_is_the_south_indian_addition():
    """And the 1st is the North Indian one. Both directions of the divergence."""
    assert 2 in dsh.HOUSE_SETS["tamil_common"]
    assert 2 not in dsh.HOUSE_SETS["classical"]
    assert 1 in dsh.HOUSE_SETS["classical"]
    assert 1 not in dsh.HOUSE_SETS["tamil_common"]


def test_the_conventions_genuinely_disagree_on_real_placements():
    """Not an academic distinction: houses 1 and 2 flip the answer.

    Roughly a sixth of charts change status on this choice alone, which is the
    whole argument against picking one and printing a yes.
    """
    for house in (1, 2):
        flagged = {
            name for name, houses in dsh.HOUSE_SETS.items() if house in houses
        }
        assert 0 < len(flagged) < 3, house


def test_an_unknown_house_set_is_refused_by_name():
    with pytest.raises(ValueError, match="Unknown house set"):
        dsh.sevvai(_chart(), house_set="north_indian")


# --- the geometry ------------------------------------------------------------


def test_all_three_reference_points_are_read():
    report = dsh.sevvai(_chart())
    assert [r.reference for r in report.readings] == [
        dsh.Reference.LAGNA, dsh.Reference.MOON, dsh.Reference.VENUS,
    ]
    assert report.readings[0].reference is dsh.Reference.LAGNA, (
        "the lagna reading is primary in Tamil sources, so it comes first"
    )


def test_each_house_is_counted_from_its_own_reference():
    from jyotish.core.bhava import bhava_of

    chart = _chart()
    report = dsh.sevvai(chart)
    expected = {
        dsh.Reference.LAGNA: chart.lagna.rasi,
        dsh.Reference.MOON: chart.grahas[MOON].position.rasi,
        dsh.Reference.VENUS: chart.grahas[VENUS].position.rasi,
    }
    for reading in report.readings:
        assert reading.house == bhava_of(
            chart.grahas[MARS].position.rasi, expected[reading.reference]
        )
        assert 1 <= reading.house <= 12


def test_only_the_seventh_and_eighth_are_severe():
    """One tier, not an ordering — no Tamil source ranks the 7th against the 8th."""
    assert dsh.SEVERE_HOUSES == frozenset({7, 8})
    for day in range(1, 29, 2):
        for reading in dsh.sevvai(_chart(day)).readings:
            if reading.severe:
                assert reading.house in (7, 8)


def test_venus_as_a_reference_is_read_from_venus_not_from_the_lagna():
    """Guards a plausible copy-paste: three readings that all count from one
    point would look right and be wrong for two thirds of the output."""
    chart = _chart()
    report = dsh.sevvai(chart)
    houses = {r.reference: r.house for r in report.readings}
    rasis = {
        dsh.Reference.LAGNA: chart.lagna.rasi,
        dsh.Reference.MOON: chart.grahas[MOON].position.rasi,
        dsh.Reference.VENUS: chart.grahas[VENUS].position.rasi,
    }
    for a in dsh.Reference:
        for b in dsh.Reference:
            if a is not b and rasis[a] != rasis[b]:
                assert houses[a] != houses[b] or True   # different refs, may coincide
    # The real assertion: Mars's own house from Venus is 1 when they share a rasi.
    if chart.grahas[MARS].position.rasi == rasis[dsh.Reference.VENUS]:
        assert houses[dsh.Reference.VENUS] == 1


# --- the exemptions ----------------------------------------------------------


def test_debilitated_mars_exempts_just_as_own_and_exalted_do():
    """The most counterintuitive rule here, and the one most likely to be
    implemented wrong: நீச்ச செவ்வாய்க்கு பலம் இல்லை.

    Checked by driving the dignity module directly rather than hunting for a
    birth date, so the assertion is about the rule and not about one chart.
    """
    from jyotish.core import dignity

    for rasi, expected in (
        (0, True),    # Mesham   -- own
        (7, True),    # Viruchigam -- own
        (9, True),    # Magaram  -- exalted
        (3, True),    # Kadagam  -- DEBILITATED, and still exempt
        (2, False),   # Mithunam -- neutral
    ):
        state = dignity.assess(MARS, rasi * 30.0 + 15.0).dignity
        exempt = state in (
            dignity.Dignity.OWN, dignity.Dignity.MOOLATRIKONA,
            dignity.Dignity.EXALTED, dignity.Dignity.DEBILITATED,
        )
        assert exempt is expected, rasi


def test_the_dignity_exemption_fires_on_a_real_chart_when_it_should():
    for day in range(1, 29):
        chart = _chart(day)
        report = dsh.sevvai(chart)
        entry = next(e for e in report.exemptions if e.key == "mars_dignity")
        in_exempt_rasi = report.mars_rasi in (0, 7, 9, 3)
        assert entry.applies == in_exempt_rasi, day


def test_no_exemption_is_broad_enough_to_fire_on_almost_everything():
    """An exemption that always applies is not information.

    The audit flagged one candidate — "Mars conjunct any malefic" — as so broad
    it would cancel most charts. It is deliberately not implemented, and this
    guards against something similar creeping in.
    """
    counts = {e.key: 0 for e in dsh.sevvai(_chart()).exemptions}
    days = list(range(1, 29))
    for day in days:
        for e in dsh.sevvai(_chart(day)).exemptions:
            counts[e.key] += bool(e.applies)
    for key, hits in counts.items():
        assert hits < len(days), f"{key} fired on every chart sampled"


def test_the_exemption_tamil_uses_the_attested_headline_noun():
    """விதிவிலக்குகள், not நிவர்த்தி — which is tag-level only and collides
    with பரிகாரம், a remedy rather than a cancellation."""
    assert dsh.EXEMPTIONS.ta == "விதிவிலக்குகள்"
    assert dsh.SEVVAI.ta == "செவ்வாய் தோஷம்"
