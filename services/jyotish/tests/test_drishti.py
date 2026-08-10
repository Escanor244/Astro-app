"""Graha drishti — கிரக பார்வை.

Small module, high blast radius: sevvai dosham, the yogas, maraka/badhaka and
neechabhanga all ask this one question, so an off-by-one here would be wrong by
a house everywhere at once and look plausible in every individual chart.

The tests are therefore mostly invariants rather than examples — the 7th aspect
is mutual, the special aspects come in the pairs the texts name, and the count is
inclusive.
"""

from __future__ import annotations

from datetime import datetime

from jyotish.core import ayanamsa as ay
from jyotish.core import drishti as dr
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import (
    GRAHAS,
    JUPITER,
    KETU,
    MARS,
    MERCURY,
    MOON,
    RAHU,
    SATURN,
    SUN,
    VENUS,
)

VISIBLE = (SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN)


# --- the rule ----------------------------------------------------------------


def test_every_visible_graha_looks_at_the_seventh():
    for graha in VISIBLE:
        assert 7 in dr.houses_aspected(graha), GRAHAS[graha].en


def test_the_three_special_aspects_are_the_ones_the_texts_name():
    assert dr.houses_aspected(MARS) == (4, 7, 8)
    assert dr.houses_aspected(JUPITER) == (5, 7, 9)
    assert dr.houses_aspected(SATURN) == (3, 7, 10)


def test_the_other_four_have_only_the_seventh():
    for graha in (SUN, MOON, MERCURY, VENUS):
        assert dr.houses_aspected(graha) == (7,), GRAHAS[graha].en


def test_the_nodes_default_to_the_seventh_aspect():
    """Contested in Tamil practice, so it is a setting with an honest default.

    The 7th is the universal rule applied to the நவகிரகங்கள் without an
    exception, which is the position Tamil practitioners most commonly state.
    """
    assert dr.DEFAULT_NODE_DRISHTI is dr.NodeDrishti.SEVENTH
    for node in (RAHU, KETU):
        assert dr.houses_aspected(node) == (7,)
        assert dr.aspects_rasi(node, 0, 6)


def test_the_other_two_node_conventions_are_available():
    for node in (RAHU, KETU):
        assert dr.houses_aspected(node, dr.NodeDrishti.NONE) == ()
        assert dr.houses_aspected(node, dr.NodeDrishti.FIVE_SEVEN_NINE) == (5, 7, 9)
        assert dr.rasis_aspected(node, 0, dr.NodeDrishti.NONE) == ()


def test_under_the_default_the_nodes_only_ever_look_at_each_other():
    """Rahu and Ketu are always exactly opposite, so the 7th lands on the other.

    Worth pinning, because it means node drishti adds exactly one relationship
    to a chart and can never reach a third rasi — if a future change makes a
    node aspect somewhere else under this convention, something is wrong with
    the node positions, not with this module.
    """
    chart = _chart()
    views = dr.for_chart(chart)
    assert views[RAHU].rasis == (chart.grahas[KETU].position.rasi,)
    assert views[KETU].rasis == (chart.grahas[RAHU].position.rasi,)
    # Each node is *among* the grahas the other sees — not necessarily alone.
    # In this chart Saturn shares Magaram with Rahu, so Ketu's single aspect
    # legitimately catches both.
    assert KETU in views[RAHU].grahas
    assert RAHU in views[KETU].grahas


def test_the_node_convention_does_not_disturb_the_other_seven():
    chart = _chart()
    baseline = dr.for_chart(chart, dr.NodeDrishti.NONE)
    for convention in dr.NodeDrishti:
        views = dr.for_chart(chart, convention)
        for graha in VISIBLE:
            assert views[graha].rasis == baseline[graha].rasis, convention


# --- the counting ------------------------------------------------------------


def test_counting_is_inclusive_so_the_seventh_is_five_signs_on():
    """`+ 7` instead of `+ 6` is the whole bug, and it is invisible per-chart."""
    for rasi in range(12):
        assert dr.rasis_aspected(SUN, rasi) == ((rasi + 6) % 12,)


def test_the_seventh_aspect_is_mutual():
    """If A looks at B's rasi from its own, B looks straight back."""
    for graha in VISIBLE:
        for rasi in range(12):
            opposite = (rasi + 6) % 12
            assert dr.aspects_rasi(graha, rasi, opposite)
            assert dr.aspects_rasi(graha, opposite, rasi)


def test_a_graha_never_looks_at_its_own_rasi():
    for convention in dr.NodeDrishti:
        for graha in range(9):
            for rasi in range(12):
                assert rasi not in dr.rasis_aspected(graha, rasi, convention)


def test_the_special_aspects_land_where_the_texts_say():
    # Mars in Mesham (0) looks at Kadagam (3), Thulam (6), Magaram (9).
    assert dr.rasis_aspected(MARS, 0) == (3, 6, 7)
    # Jupiter in Mesham looks at Simmam (4), Thulam (6), Dhanusu (8).
    assert dr.rasis_aspected(JUPITER, 0) == (4, 6, 8)
    # Saturn in Mesham looks at Mithunam (2), Thulam (6), Magaram (9).
    assert dr.rasis_aspected(SATURN, 0) == (2, 6, 9)


def test_saturn_and_mars_aspects_wrap_the_zodiac():
    """Counting past Meenam must come round to Mesham, not run off the end."""
    assert dr.rasis_aspected(SATURN, 11) == (1, 5, 8)
    assert dr.rasis_aspected(MARS, 10) == (1, 4, 5)
    for graha in range(9):
        for rasi in range(12):
            assert all(0 <= r < 12 for r in dr.rasis_aspected(graha, rasi))


def test_the_three_special_grahas_look_at_three_distinct_rasis():
    for graha in (MARS, JUPITER, SATURN):
        for rasi in range(12):
            assert len(set(dr.rasis_aspected(graha, rasi))) == 3


# --- against a real chart ----------------------------------------------------


def _chart():
    return pos.compute(
        BirthData(
            when=datetime(1990, 5, 15, 6, 30), latitude=13.0827,
            longitude=80.2707, timezone_name="Asia/Kolkata",
        ),
        ay.Ayanamsa.LAHIRI,
    )


def test_a_real_chart_reports_drishti_for_all_nine_including_the_nodes():
    """The nodes appear with nothing, rather than being absent from the map.

    An absent key makes every caller write the same guard, and a caller that
    forgets silently drops Rahu and Ketu from a table instead of showing them.
    """
    chart = _chart()
    seen = dr.for_chart(chart, dr.NodeDrishti.NONE)
    assert sorted(seen) == list(range(9))
    assert seen[RAHU].rasis == () and seen[KETU].rasis == ()
    for graha in VISIBLE:
        assert len(seen[graha].rasis) in (1, 3)


def test_the_bhava_numbers_agree_with_the_rasis_they_came_from():
    chart = _chart()
    for view in dr.for_chart(chart).values():
        assert len(view.bhavas) == len(view.rasis)
        for rasi, bhava in zip(view.rasis, view.bhavas):
            assert bhava == (rasi - chart.lagna.rasi) % 12 + 1
            assert 1 <= bhava <= 12


def test_who_aspects_agrees_with_the_per_graha_view():
    """The two directions of the same question must not be able to disagree."""
    chart = _chart()
    views = dr.for_chart(chart)
    for rasi in range(12):
        forward = {g for g, v in views.items() if rasi in v.rasis}
        assert set(dr.who_aspects_rasi(chart, rasi)) == forward


def test_who_aspects_bhava_counts_from_the_lagna():
    chart = _chart()
    assert dr.who_aspects_bhava(chart, 1) == dr.who_aspects_rasi(
        chart, chart.lagna.rasi
    )
    assert dr.who_aspects_bhava(chart, 7) == dr.who_aspects_rasi(
        chart, (chart.lagna.rasi + 6) % 12
    )


def test_the_grahas_listed_as_aspected_really_stand_in_those_rasis():
    chart = _chart()
    for view in dr.for_chart(chart).values():
        for other in view.grahas:
            assert chart.grahas[other].position.rasi in view.rasis
            assert other != view.graha


def test_drishti_does_not_depend_on_the_lagna():
    """It is a rasi relation, so only the bhava *numbering* may rotate.

    Varied by **latitude**, at one instant. That moves the lagna a long way
    while leaving every graha exactly where it was — the isolation the claim
    needs. Varying the birth *time* instead would not test this: the Moon covers
    half a rasi in twelve hours, so its aspects would move for an honest reason
    and the test would fail while the code was right.
    """
    def view_for(latitude: float):
        chart = pos.compute(
            BirthData(
                when=datetime(1990, 5, 15, 6, 30), latitude=latitude,
                longitude=80.2707, timezone_name="Asia/Kolkata",
            ),
            ay.Ayanamsa.LAHIRI,
        )
        views = dr.for_chart(chart)
        return chart.lagna.rasi, {g: v.rasis for g, v in views.items()}

    south_lagna, south = view_for(13.0827)
    north_lagna, north = view_for(55.0)

    assert south_lagna != north_lagna, "pick latitudes that move the lagna"
    assert south == north
