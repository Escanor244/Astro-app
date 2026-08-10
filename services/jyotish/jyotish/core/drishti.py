"""Graha drishti -- கிரக பார்வை, which grahas look at which rasis.

A graha does not only act where it sits. It also *looks* at other places in the
chart, and what it looks at, it affects. This is the layer between "where is
everything" and any actual reading: செவ்வாய் தோஷம் is defined by which houses
Mars looks at, the pancha mahapurusha and raja yogas need who looks at whom, and
நீச பங்கம் turns on whether a debilitated graha is looked at by its dispositor.
Almost nothing predictive can be built before this exists.

The rule, in full:

* **Every graha looks at the 7th rasi from itself.** Directly opposite.
* **செவ்வாய் (Mars)** also looks at the **4th and 8th**.
* **குரு (Jupiter)** also looks at the **5th and 9th**.
* **சனி (Saturn)** also looks at the **3rd and 10th**.

Counting is inclusive, as it always is in Jyotish: the graha's own rasi is the
1st, so the 7th from it is five rasis further on. Writing ``+ 7`` instead of
``+ 6`` is the single easiest way to get this wrong, and it would be wrong by one
house everywhere at once.

**Rahu and Ketu are contested** -- see :class:`NodeDrishti`, which is why that is
a setting rather than a hardcoded answer.

Two things this module deliberately does not do, both stated carefully because
earlier versions of this docstring overstated them. See ``docs/drishti-sources.md``
for the sources.

**Whole-sign, not degree-based.** A graha looks at the whole rasi, not at a point
within it. Every popular Tamil source states drishti in whole houses, and both
Jagannatha Hora and jyotishganit compute it as integer rasi arithmetic. But this
is the mainstream reading, not the only one: BPHS Ch. 26 gives *longitude*
arithmetic and calls the house-only method the "ordinary" one, and at least one
Tamil authority holds that a full aspect needs the bodies within 15 degrees --
"there is no wall in the sky" at a sign boundary.

**Binary, not graded.** The same BPHS verse that grants the three special aspects
also grants *every* graha a quarter aspect on the 3rd and 10th, a half on the
5th and 9th and three-quarters on the 4th and 8th -- so this module ships the
exception without the scale. That is faithful rather than lazy: no Tamil source
found uses graded aspects in ordinary chart reading, and both reference
implementations keep chart-level drishti binary and put virupas in shadbala.
Grading arrives with shadbala or not at all. Note the texts disagree about the
middle of that scale anyway -- Saravali swaps the 4/8 and 5/9 fractions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .zodiac import GRAHAS, JUPITER, KETU, MARS, RAHU, SATURN, Term

DRISHTI = Term("Aspect", "பார்வை", "Paarvai", "Dr", "பார்")


class NodeDrishti(Enum):
    """What Rahu and Ketu look at. Genuinely contested, so it is a setting.

    Tamil practice has not settled this. Ask the question in Tamil -- "ராகு கேது
    கிரகங்களுக்கு பார்வை பலம் உள்ளதா இல்லையா?" -- and you get three answers,
    each with practitioners behind it:

    ``SEVENTH``
        The 7th only -- the universal rule applied to the நவகிரகங்கள் without an
        exception. What Jagannatha Hora computes, and the plain reading of BPHS,
        whose aspect chapter says "all Grahas" while BPHS 3.10 counts nine of
        them. **The default here**, on those grounds and not on a finding.
    ``THREE_SEVEN_ELEVEN``
        3, 7 and 11. **The most commonly printed Tamil answer** -- three
        independent Tamil sources including Daily Thanthi. This position exists
        in Tamil material and essentially nowhere else, which is exactly why an
        app for Tamil practice has to be able to express it.
    ``NONE``
        No aspect at all: a நிழல் கிரகம் has no light to cast a look with. The
        plurality on the Tamil web, and it has the strongest classical
        counterweight behind it -- BPHS Ch. 27 confines Shadbala, of which Drik
        Bala is one of the six, to the seven grahas from Surya to Sani.
    ``FIVE_SEVEN_NINE``
        5, 7 and 9, as Jupiter has. V.K. Choudhry's Systems Approach. **Not**
        classical: nobody quoting BPHS for it has produced a verse. Note also
        that the widely repeated claim that *KP* teaches this appears to be
        fabricated -- KP replaces Parashari drishti with degree aspects
        altogether and treats the nodes as agents of their conjoined and
        aspecting planets.

    A fifth position exists that this enum cannot express: Sanjay Rath gives
    Ketu no drishti while giving Rahu the 7th, the 5th/9th and uniquely the 2nd.
    It is not offered because nothing in the app needs asymmetric nodes yet, and
    a setting nobody selects is a setting nobody maintains.

    This is deliberately *not* resolved the way node exaltation was. There the
    app shows a dash and claims nothing, because a missing dignity is a visible
    blank the reader can judge. Drishti is load-bearing -- sevvai dosham, the
    yogas and neechabhanga all consume it -- so "nothing" is itself a strong
    claim that silently changes results downstream. A default is unavoidable;
    what is avoidable is pretending there was no choice.

    One consequence worth knowing under ``SEVENTH``: Rahu and Ketu are always
    exactly opposite each other, so Rahu's 7th aspect always lands on Ketu's
    rasi and Ketu's on Rahu's. Node drishti therefore adds exactly one thing to
    a chart -- each node looking at the other -- and never reaches a third rasi.
    """

    SEVENTH = "seventh"
    THREE_SEVEN_ELEVEN = "3_7_11"
    NONE = "none"
    FIVE_SEVEN_NINE = "5_7_9"


DEFAULT_NODE_DRISHTI = NodeDrishti.SEVENTH

#: Houses each graha looks at, counted inclusively from its own rasi. The 7th is
#: universal; Mars, Jupiter and Saturn add two more each.
#:
#: The pairing is checkable and was checked: Mars 4/8 and Saturn 3/10 are mirror
#: images, so a swap would be an easy error to inherit, but the Sanskrit of
#: Brihat Jataka 2.13 locks the order by word sequence plus *kramaśaḥ*
#: ("respectively"). No credible source gives the Sun, Moon, Mercury or Venus a
#: special aspect.
#:
#: The nodes are not here because their answer is a policy, not a table --
#: :func:`houses_aspected` applies :class:`NodeDrishti` for them.
ASPECTS: dict[int, tuple[int, ...]] = {
    MARS: (4, 7, 8),
    JUPITER: (5, 7, 9),
    SATURN: (3, 7, 10),
}

#: The one aspect every non-node graha has.
FULL_ASPECT_HOUSE = 7

NODES: frozenset[int] = frozenset({RAHU, KETU})

_NODE_HOUSES: dict[NodeDrishti, tuple[int, ...]] = {
    NodeDrishti.SEVENTH: (7,),
    NodeDrishti.THREE_SEVEN_ELEVEN: (3, 7, 11),
    NodeDrishti.NONE: (),
    NodeDrishti.FIVE_SEVEN_NINE: (5, 7, 9),
}


def houses_aspected(
    graha: int, nodes: NodeDrishti = DEFAULT_NODE_DRISHTI
) -> tuple[int, ...]:
    """Which houses from itself a graha looks at, ascending."""
    if graha in NODES:
        return _NODE_HOUSES[nodes]
    return ASPECTS.get(graha, (FULL_ASPECT_HOUSE,))


def rasis_aspected(
    graha: int, from_rasi: int, nodes: NodeDrishti = DEFAULT_NODE_DRISHTI
) -> tuple[int, ...]:
    """The rasis a graha in ``from_rasi`` looks at.

    Inclusive counting: house N from a rasi is ``(rasi + N - 1) % 12``, so the
    7th is five signs further round, not seven.
    """
    return tuple(
        (from_rasi + house - 1) % 12 for house in houses_aspected(graha, nodes)
    )


def aspects_rasi(
    graha: int, from_rasi: int, target_rasi: int,
    nodes: NodeDrishti = DEFAULT_NODE_DRISHTI,
) -> bool:
    """Does a graha in ``from_rasi`` look at ``target_rasi``?"""
    return target_rasi % 12 in rasis_aspected(graha, from_rasi, nodes)


@dataclass(frozen=True)
class Drishti:
    """One graha's view of the chart."""

    graha: int
    from_rasi: int
    #: Rasis looked at, ascending by house number.
    rasis: tuple[int, ...]
    #: Houses from the lagna those rasis are, so a reader can say "Saturn
    #: aspects the 7th" without recounting.
    bhavas: tuple[int, ...]
    #: Other grahas standing in those rasis.
    grahas: tuple[int, ...]

    @property
    def name(self) -> Term:
        return GRAHAS[self.graha]


def for_chart(
    chart, nodes: NodeDrishti = DEFAULT_NODE_DRISHTI
) -> dict[int, Drishti]:
    """Drishti for all nine grahas of a ``ChartPositions``.

    Always returns an entry per graha, even when the convention gives the nodes
    nothing. An absent key would make every caller write the same guard, and a
    caller that forgot would silently drop the nodes from a table rather than
    showing them with nothing to show.
    """
    where = {gi: chart.grahas[gi].position.rasi for gi in range(9)}
    out: dict[int, Drishti] = {}

    for graha in range(9):
        rasis = rasis_aspected(graha, where[graha], nodes)
        out[graha] = Drishti(
            graha=graha,
            from_rasi=where[graha],
            rasis=rasis,
            bhavas=tuple((r - chart.lagna.rasi) % 12 + 1 for r in rasis),
            grahas=tuple(
                other for other in range(9)
                if other != graha and where[other] in rasis
            ),
        )
    return out


def who_aspects_rasi(
    chart, rasi: int, nodes: NodeDrishti = DEFAULT_NODE_DRISHTI
) -> tuple[int, ...]:
    """Every graha looking at a rasi. The question doshas and yogas actually ask."""
    return tuple(
        graha for graha in range(9)
        if aspects_rasi(graha, chart.grahas[graha].position.rasi, rasi, nodes)
    )


def who_aspects_bhava(
    chart, bhava: int, nodes: NodeDrishti = DEFAULT_NODE_DRISHTI
) -> tuple[int, ...]:
    """Every graha looking at a bhava, numbered 1-12 from the lagna."""
    return who_aspects_rasi(chart, (chart.lagna.rasi + bhava - 1) % 12, nodes)
