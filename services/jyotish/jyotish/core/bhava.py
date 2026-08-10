"""Bhavas -- the twelve houses, their lords, and what each signifies.

The layer between "which rasi" and "what about". A graha in Thulam means little
until you know Thulam is this person's 7th, and that its lord is Venus sitting
somewhere else entirely.

Whole-sign throughout, which is not a simplification but what the South Indian
square chart *is*: the lagna's rasi is the 1st bhava, the next rasi the 2nd, and
so on. There is no separate bhava chalit here, and Tamil sources are firm that
predicting from a relocated bhava is தவறான பலன்.

Every Tamil string below was sourced and then independently re-checked, and the
ones that failed are recorded in ``docs/bhava-sources.md`` rather than quietly
dropped. Two worth knowing here:

* **சந்திர லக்னம் does not appear in Tamil.** Zero hits across 99 Tamil pages.
  Tamil says **ராசிப்படி** ("by the rasi") for the Moon-based reading pass, as
  against **லக்னப்படி** for the ascendant-based one, and counts houses as
  "ராசிக்கு ஏழாம் இடம்". The obvious calque would have been an invention.
* **மாரகர் is not attested either** -- Tamil prints மாரகன் or மாரகர்கள்.
"""

from __future__ import annotations

from dataclasses import dataclass

from .zodiac import (
    GRAHAS,
    JUPITER,
    KETU,
    MARS,
    MERCURY,
    MOON,
    RASI_LORDS,
    RASIS,
    RAHU,
    SATURN,
    SUN,
    VENUS,
    Term,
)

#: The twelve, in the **ஸ்தானம்** register -- which is how Tamil sources name a
#: house by its meaning. The other register, ordinal + **பாவகம்** or **வீடு**,
#: is how Tamil names a house by its number ("இரண்டாம் பாவகம்", "6ம் வீடு"), and
#: :func:`ordinal_label` builds those.
#:
#: Note what is deliberately absent: forms like "தன பாவம்". The two registers do
#: not cross -- no Tamil source was found writing a *meaning* name with பாவம் --
#: so generating one would produce fluent-looking Tamil that nobody writes.
BHAVAS: tuple[Term, ...] = (
    Term("Lagna", "லக்னம்", "Lagnam", "1", "லக்"),
    Term("Wealth", "தன ஸ்தானம்", "Thana sthaanam", "2", "தன"),
    Term("Siblings", "சகோதர ஸ்தானம்", "Sagothara sthaanam", "3", "சகோ"),
    Term("Mother and home", "சுக ஸ்தானம்", "Suga sthaanam", "4", "சுக"),
    Term("Children", "புத்திர ஸ்தானம்", "Puththira sthaanam", "5", "புத்"),
    Term("Disease and enemies", "ரோக ஸ்தானம்", "Roga sthaanam", "6", "ரோக"),
    Term("Spouse", "களத்திர ஸ்தானம்", "Kalaththira sthaanam", "7", "களத்"),
    Term("Longevity", "ஆயுள் ஸ்தானம்", "Aayul sthaanam", "8", "ஆயு"),
    Term("Fortune and father", "பாக்கிய ஸ்தானம்", "Paakkiya sthaanam", "9", "பாக்"),
    Term("Profession", "கர்ம ஸ்தானம்", "Karma sthaanam", "10", "கர்"),
    Term("Gains", "லாப ஸ்தானம்", "Laaba sthaanam", "11", "லாப"),
    Term("Loss and liberation", "விரய ஸ்தானம்", "Viraya sthaanam", "12", "விர"),
)

#: What each bhava is asked about, as Tamil sources list it.
SIGNIFICATIONS: tuple[str, ...] = (
    "body, appearance, character, vitality",
    "wealth, family, speech, early education, food",
    "younger siblings, courage, effort, short journeys",
    "mother, home, land, vehicles, comfort, schooling",
    "children, past merit, mind, devotion, intelligence",
    "disease, enemies, debt, litigation, competition",
    "spouse, marriage, partnership, trade",
    "longevity, death, accident, chronic illness, inheritance",
    "father, fortune, dharma, guru, higher learning, pilgrimage",
    "profession, status, authority, fame, action",
    "gains, income, elder siblings, friends, fulfilled desire",
    "loss, expenditure, sleep, liberation, foreign life, confinement",
)

KENDRA: tuple[int, ...] = (1, 4, 7, 10)
TRIKONA: tuple[int, ...] = (1, 5, 9)
UPACHAYA: tuple[int, ...] = (3, 6, 10, 11)

#: **மறைவு ஸ்தானம்**, the native Tamil term and the one that dominates -- the
#: Sanskritised துர்ஸ்தானம் / துஸ்தானம் also occurs but is less common.
#:
#: Membership is genuinely disputed. Some Tamil sources count the 3rd with the
#: 6th, 8th and 12th; others give only 6, 8 and 12. This takes the narrower set,
#: because the 3rd is also an உபசயம் and counting it as simply malefic
#: contradicts that -- but the disagreement is real and recorded in
#: ``docs/bhava-sources.md``.
DUSTHANA: tuple[int, ...] = (6, 8, 12)

GROUP_NAMES: dict[str, Term] = {
    "kendra": Term("Kendra", "கேந்திரம்", "Kendhiram", "K", "கேந்"),
    "trikona": Term("Trikona", "திரிகோணம்", "Thirikonam", "T", "திரி"),
    "upachaya": Term("Upachaya", "உபசய ஸ்தானம்", "Ubasaya sthaanam", "U", "உப"),
    "dusthana": Term("Dusthana", "மறைவு ஸ்தானம்", "Maraivu sthaanam", "D", "மறை"),
}

#: Naisargika karakas -- what each graha naturally signifies, whoever's chart it
#: is. Every Tamil string here was found verbatim in a Tamil source, and the set
#: is entirely **grantha-free**, which is a good sign that it is the almanac
#: register rather than a Sanskritised one.
#:
#: The Sanskritised alternatives are real words, not errors -- மாத்ரு காரகன் for
#: the Moon is attested -- but the native forms are preferred here for the same
#: reason lexicon.py prefers வளர்பிறை over சுக்ல பக்ஷம்.
KARAKAS: dict[int, tuple[Term, ...]] = {
    SUN: (Term("Father", "பிதுர் காரகன்", "Pithur kaarakan"),),
    MOON: (
        Term("Mother", "தாய் காரகன்", "Thaay kaarakan"),
        Term("Mind", "மனோ காரகன்", "Mano kaarakan"),
    ),
    MARS: (
        Term("Siblings", "சகோதர காரகன்", "Sakothara kaarakan"),
        Term("Land", "பூமி காரகன்", "Poomi kaarakan"),
    ),
    MERCURY: (
        Term("Intellect", "புத்தி காரகன்", "Puththi kaarakan"),
        Term("Education", "கல்வி காரகன்", "Kalvi kaarakan"),
        Term("Speech", "வாக்கு காரகன்", "Vaakku kaarakan"),
    ),
    JUPITER: (
        Term("Children", "புத்திர காரகன்", "Puththira kaarakan"),
        Term("Wealth", "தன காரகன்", "Thana kaarakan"),
        Term("Family", "குடும்ப காரகன்", "Kudumba kaarakan"),
    ),
    VENUS: (
        Term("Spouse", "களத்திர காரகன்", "Kalaththira kaarakan"),
        Term("Vehicles", "வாகன காரகன்", "Vaahana kaarakan"),
    ),
    SATURN: (
        Term("Longevity", "ஆயுள் காரகன்", "Aayul kaarakan"),
        Term("Profession", "கர்ம காரகன்", "Karma kaarakan"),
    ),
    RAHU: (
        Term("Indulgence", "போக காரகன்", "Boga kaarakan"),
        Term("Paternal grandfather", "பாட்டன் காரகன்", "Paattan kaarakan"),
    ),
    KETU: (Term("Wisdom", "ஞான காரகன்", "Nyaana kaarakan"),),
}

#: **பாதக ஸ்தானம்** -- the house that obstructs, keyed to the lagna's modality
#: and nothing else. Movable lagnas take the 11th, fixed the 9th, dual the 7th.
#:
#: Verified two independent ways, because a transposition here would be silent:
#: by ordinal, and by checking that the resulting *signs* match the ones the
#: classical text names outright for movable lagnas (Kumbha, Vrishabha, Simha,
#: Vrischika). Indexed by ``rasi % 3`` -- movable 0, fixed 1, dual 2, the same
#: classification ``charts/vargas.py`` already uses.
BADHAKA_BY_MODALITY: tuple[int, ...] = (11, 9, 7)

#: **மாரக ஸ்தானம்** -- the houses that can end life. The 2nd and 7th, which is
#: what every source states and what the classical rule gives.
#:
#: One unresolved question, flagged rather than decided: some Tamil sources make
#: maraka modality-dependent like badhaka -- movable 2/7, fixed 3/8, dual 7/11 --
#: which would change the answer for eight of the twelve lagnas. That reading was
#: not confirmed on re-check, so the universal 2/7 stands and the variant is
#: recorded in ``docs/bhava-sources.md`` as a question for an astrologer.
MARAKA_HOUSES: tuple[int, ...] = (2, 7)

BHAVA_WORD = Term("House", "பாவகம்", "Paavagam", "H", "பாவ")
LORD_WORD = Term("Lord", "அதிபதி", "Athipathi", "L", "அதி")
MARAKA = Term("Maraka", "மாரகாதிபதி", "Maarakaathipathi", "Mk", "மார")
BADHAKA = Term("Badhaka", "பாதகாதிபதி", "Paathakaathipathi", "Bd", "பாத")

#: The two reading passes, in the words Tamil actually uses. **Not**
#: "சந்திர லக்னம்", which no Tamil source writes -- see the module docstring.
FROM_LAGNA = Term("From the lagna", "லக்னப்படி", "Lagnappadi", "L", "லக்")
FROM_MOON = Term("From the Moon", "ராசிப்படி", "Raasippadi", "R", "ராசி")


def ordinal_label(bhava: int, lang: str = "en") -> str:
    """"2nd house" / "2ஆம் பாவகம்" -- the numeric register, not the meaning one."""
    if lang == "ta":
        return f"{bhava}ஆம் பாவகம்"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(
        bhava if bhava < 20 else bhava % 10, "th"
    )
    return f"{bhava}{suffix} house"


def bhava_of(rasi: int, reference_rasi: int) -> int:
    """Which house a rasi is, counted from a reference rasi. 1-12, inclusive.

    ``reference_rasi`` is the lagna for the ordinary reading and the Moon's rasi
    for the ராசிப்படி pass. Passing it explicitly rather than assuming the lagna
    is what makes the second pass free.
    """
    return (rasi - reference_rasi) % 12 + 1


def rasi_of_bhava(bhava: int, reference_rasi: int) -> int:
    return (reference_rasi + bhava - 1) % 12


def lord_of(bhava: int, reference_rasi: int) -> int:
    """The graha ruling a house -- its **அதிபதி**."""
    return RASI_LORDS[rasi_of_bhava(bhava, reference_rasi)]


def badhaka_house(lagna_rasi: int) -> int:
    """The பாதக ஸ்தானம் for a lagna: 11th if movable, 9th if fixed, 7th if dual."""
    return BADHAKA_BY_MODALITY[lagna_rasi % 3]


def badhaka_lord(lagna_rasi: int) -> int:
    return lord_of(badhaka_house(lagna_rasi), lagna_rasi)


def maraka_lords(lagna_rasi: int) -> tuple[int, ...]:
    """Lords of the maraka houses, deduplicated.

    One graha can rule both -- for a Mesham lagna Venus owns the 2nd and the
    7th -- and reporting it twice would read as two separate marakas.
    """
    seen: list[int] = []
    for house in MARAKA_HOUSES:
        lord = lord_of(house, lagna_rasi)
        if lord not in seen:
            seen.append(lord)
    return tuple(seen)


def group_of(bhava: int) -> tuple[str, ...]:
    """Which classification groups a house belongs to. A house can be in two --
    the 1st is both a kendra and a trikona, the 10th both a kendra and an
    upachaya -- which is exactly why this returns a tuple."""
    groups = []
    if bhava in KENDRA:
        groups.append("kendra")
    if bhava in TRIKONA:
        groups.append("trikona")
    if bhava in UPACHAYA:
        groups.append("upachaya")
    if bhava in DUSTHANA:
        groups.append("dusthana")
    return tuple(groups)


@dataclass(frozen=True)
class Bhava:
    """One house of a chart, as read from a given reference point."""

    number: int
    name: Term
    rasi: int
    signification: str
    lord: int
    #: Grahas standing in this house.
    occupants: tuple[int, ...]
    groups: tuple[str, ...]

    @property
    def rasi_name(self) -> Term:
        return RASIS[self.rasi]

    @property
    def lord_name(self) -> Term:
        return GRAHAS[self.lord]


def for_chart(chart, from_moon: bool = False) -> tuple[Bhava, ...]:
    """The twelve bhavas of a ``ChartPositions``, in order.

    ``from_moon`` gives the **ராசிப்படி** pass -- the same twelve rasis renumbered
    from the Moon instead of the lagna. Tamil practice reads a chart both ways as
    a matter of course, and it costs nothing here because the placements do not
    move; only the numbering does.
    """
    reference = (
        chart.grahas[MOON].position.rasi if from_moon else chart.lagna.rasi
    )
    where = {gi: chart.grahas[gi].position.rasi for gi in range(9)}

    out = []
    for number in range(1, 13):
        rasi = rasi_of_bhava(number, reference)
        out.append(Bhava(
            number=number,
            name=BHAVAS[number - 1],
            rasi=rasi,
            signification=SIGNIFICATIONS[number - 1],
            lord=RASI_LORDS[rasi],
            occupants=tuple(g for g in range(9) if where[g] == rasi),
            groups=group_of(number),
        ))
    return tuple(out)
