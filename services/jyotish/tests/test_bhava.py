"""Bhavas, their lords, karakas, and the maraka/badhaka derivations.

Almost all lookup tables, so the tests are mostly about pinning them: a wrong
entry here has no arithmetic to fail, it just prints the wrong word forever.
Two Tamil transcription errors have already been caught in this project, so the
Tamil strings are checked as strings.

The badhaka mapping gets the most attention. Movable→11th, fixed→9th, dual→7th
is easy to transpose and the transposition is silent, so it is verified twice:
by ordinal, and by the resulting *signs* — which is the check that catches a
swap, because the classical text names those signs outright.
"""

from __future__ import annotations

from datetime import datetime

from jyotish.core import ayanamsa as ay
from jyotish.core import bhava as bh
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import (
    JUPITER,
    MARS,
    MERCURY,
    MOON,
    RASI_LORDS,
    SATURN,
    SUN,
    VENUS,
)

MOVABLE = (0, 3, 6, 9)      # Mesham, Kadagam, Thulam, Magaram
FIXED = (1, 4, 7, 10)       # Rishabam, Simmam, Viruchigam, Kumbam
DUAL = (2, 5, 8, 11)        # Mithunam, Kanni, Dhanusu, Meenam


def _chart(hour: int = 6):
    return pos.compute(
        BirthData(
            when=datetime(1990, 5, 15, hour, 30), latitude=13.0827,
            longitude=80.2707, timezone_name="Asia/Kolkata",
        ),
        ay.Ayanamsa.LAHIRI,
    )


# --- the tables --------------------------------------------------------------


def test_there_are_twelve_of_everything():
    assert len(bh.BHAVAS) == 12
    assert len(bh.SIGNIFICATIONS) == 12
    assert len({b.ta for b in bh.BHAVAS}) == 12


def test_every_bhava_has_a_tamil_name():
    for b in bh.BHAVAS:
        assert b.ta.strip() and b.ta_latin.strip(), b


def test_the_two_tamil_registers_are_not_mixed():
    """Tamil names a house by meaning with ஸ்தானம், by number with பாவகம்.

    No Tamil source was found writing a *meaning* name with பாவம் — "தன பாவம்"
    is fluent-looking Tamil that nobody writes. Generating it would be an
    invention of exactly the kind this project has already had to retract.
    """
    for b in bh.BHAVAS[1:]:                       # the 1st is plain லக்னம்
        assert b.ta.endswith("ஸ்தானம்"), b.ta
        assert "பாவம்" not in b.ta
    assert bh.ordinal_label(2, "ta") == "2ஆம் பாவகம்"
    assert bh.ordinal_label(2) == "2nd house"
    assert bh.ordinal_label(11) == "11th house"


def test_the_moon_pass_is_named_the_way_tamil_names_it():
    """ராசிப்படி, not "சந்திர லக்னம்" — which no Tamil source writes.

    Zero hits for சந்திர லக்னம் across 99 Tamil pages in the source audit. The
    obvious calque from English would have been an invention.
    """
    assert bh.FROM_MOON.ta == "ராசிப்படி"
    assert bh.FROM_LAGNA.ta == "லக்னப்படி"
    assert "லக்னம்" not in bh.FROM_MOON.ta


def test_the_karakas_cover_every_graha_and_carry_tamil():
    assert sorted(bh.KARAKAS) == list(range(9))
    for graha, karakas in bh.KARAKAS.items():
        assert karakas, graha
        for k in karakas:
            assert k.ta.endswith("காரகன்"), k.ta


def test_the_karaka_names_are_grantha_free():
    """The attested Tamil set uses no ஸ, ஷ, ஜ or ஹ, which is the register test.

    A Sanskritised form creeping in — மாத்ரு காரகன் for the Moon, say — would
    not be *wrong*, it is a real word, but it would break the almanac register
    this project keeps elsewhere (வளர்பிறை over சுக்ல பக்ஷம்).
    """
    grantha = set("ஸஷஜஹ")
    for karakas in bh.KARAKAS.values():
        for k in karakas:
            assert not (set(k.ta) & grantha), k.ta


def test_the_father_and_mother_karakas():
    """Sources split on these two, so they are pinned explicitly."""
    assert bh.KARAKAS[SUN][0].ta == "பிதுர் காரகன்"
    assert bh.KARAKAS[MOON][0].ta == "தாய் காரகன்"
    assert bh.KARAKAS[JUPITER][0].ta == "புத்திர காரகன்"


# --- lords and counting ------------------------------------------------------


def test_the_first_bhava_is_the_reference_rasi():
    for rasi in range(12):
        assert bh.rasi_of_bhava(1, rasi) == rasi
        assert bh.bhava_of(rasi, rasi) == 1


def test_counting_round_trips_for_every_pair():
    for reference in range(12):
        for rasi in range(12):
            assert bh.rasi_of_bhava(bh.bhava_of(rasi, reference), reference) == rasi


def test_the_lord_of_a_house_is_the_lord_of_its_rasi():
    for reference in range(12):
        for house in range(1, 13):
            assert bh.lord_of(house, reference) == RASI_LORDS[
                bh.rasi_of_bhava(house, reference)
            ]


def test_the_classification_groups():
    assert bh.group_of(1) == ("kendra", "trikona")
    assert bh.group_of(10) == ("kendra", "upachaya")
    assert bh.group_of(6) == ("upachaya", "dusthana")
    assert bh.group_of(8) == ("dusthana",)
    assert bh.group_of(2) == ()
    # The 3rd is an upachaya and deliberately NOT counted a dusthana here,
    # though some Tamil sources do count it. Recorded in the module docstring.
    assert "dusthana" not in bh.group_of(3)


# --- badhaka -----------------------------------------------------------------


def test_badhaka_is_eleventh_ninth_seventh_by_modality():
    for rasi in MOVABLE:
        assert bh.badhaka_house(rasi) == 11, rasi
    for rasi in FIXED:
        assert bh.badhaka_house(rasi) == 9, rasi
    for rasi in DUAL:
        assert bh.badhaka_house(rasi) == 7, rasi


def test_the_badhaka_signs_match_the_ones_the_texts_name():
    """The check that catches a transposition.

    Getting 11/9/7 the wrong way round is silent — every lagna still gets *a*
    badhaka. But the classical text names the movable-lagna badhaka signs
    outright, so those can be checked directly: Mesham→Kumbam, Kadagam→Rishabam,
    Thulam→Simmam, Magaram→Viruchigam.
    """
    expected = {0: 10, 3: 1, 6: 4, 9: 7}
    for lagna, sign in expected.items():
        assert bh.rasi_of_bhava(bh.badhaka_house(lagna), lagna) == sign, lagna


def test_the_badhaka_lord_for_every_lagna():
    # Spot-checks from the sourced table, one per modality.
    assert bh.badhaka_lord(0) == SATURN      # Mesham  -> Kumbam  -> Saturn
    assert bh.badhaka_lord(4) == MARS        # Simmam  -> Mesham  -> Mars
    assert bh.badhaka_lord(8) == MERCURY     # Dhanusu -> Mithunam-> Mercury
    for lagna in range(12):
        assert 0 <= bh.badhaka_lord(lagna) <= 6   # never a node


def test_no_lagna_has_its_own_lord_as_badhaka_lord():
    """A sanity property: the badhaka house is never the 1st."""
    for lagna in range(12):
        assert bh.badhaka_house(lagna) != 1


# --- maraka ------------------------------------------------------------------


def test_maraka_houses_are_the_second_and_seventh():
    assert bh.MARAKA_HOUSES == (2, 7)


def test_a_graha_ruling_both_maraka_houses_is_reported_once():
    """Mesham lagna: Venus owns the 2nd (Rishabam) and the 7th (Thulam).

    Listing it twice would read as two separate marakas.
    """
    assert bh.maraka_lords(0) == (VENUS,)
    for lagna in range(12):
        lords = bh.maraka_lords(lagna)
        assert len(lords) == len(set(lords))
        assert 1 <= len(lords) <= 2


# --- against a real chart ----------------------------------------------------


def test_a_real_chart_gives_twelve_bhavas_covering_every_rasi():
    chart = _chart()
    houses = bh.for_chart(chart)
    assert len(houses) == 12
    assert [h.number for h in houses] == list(range(1, 13))
    assert sorted(h.rasi for h in houses) == list(range(12))
    assert houses[0].rasi == chart.lagna.rasi


def test_every_graha_lands_in_exactly_one_bhava():
    chart = _chart()
    for from_moon in (False, True):
        houses = bh.for_chart(chart, from_moon=from_moon)
        placed = [g for h in houses for g in h.occupants]
        assert sorted(placed) == list(range(9)), from_moon


def test_the_bhavas_agree_with_the_charts_own_house_of():
    chart = _chart()
    for house in bh.for_chart(chart):
        for graha in house.occupants:
            assert chart.house_of(graha) == house.number


def test_the_moon_pass_renumbers_without_moving_anything():
    """ராசிப்படி is the same twelve rasis read from a different starting point.

    The placements must be identical; only the numbering rotates. If a graha
    changed rasi between the two passes, something is counting from the wrong
    place.
    """
    chart = _chart()
    from_lagna = bh.for_chart(chart)
    from_moon = bh.for_chart(chart, from_moon=True)

    assert {h.rasi: h.occupants for h in from_lagna} == {
        h.rasi: h.occupants for h in from_moon
    }
    assert from_moon[0].rasi == chart.grahas[MOON].position.rasi
    # The Moon is always in the 1st of its own pass.
    assert MOON in from_moon[0].occupants


def test_the_two_passes_differ_unless_the_moon_is_in_the_lagna():
    chart = _chart()
    if chart.grahas[MOON].position.rasi != chart.lagna.rasi:
        assert bh.for_chart(chart)[0].rasi != bh.for_chart(chart, True)[0].rasi
