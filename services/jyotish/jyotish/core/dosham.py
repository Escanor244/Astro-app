"""செவ்வாய் தோஷம் -- computed, reported, and deliberately not decided.

This module answers "where is Mars, and which conventions flag it" and stops
there. It has no ``present`` boolean, no percentage and no verdict, and that is
a decision taken on evidence rather than out of squeamishness.

**Why there is no verdict.** A source audit found three incompatible Tamil house
sets in mainstream use -- {2,4,7,8,12}, {1,2,4,7,8,12} and the classical
{1,4,7,8,12} -- so roughly a sixth of all charts change status on that choice
alone, before a single cancellation rule runs. It then found four mutually
incompatible Tamil formulations of the cancellation stack, disagreeing on
ordinary charts. And a Tamil practitioner states that applying the exception list
takes a hundred dosham-positives down to three survivors.

A boolean under those conditions does not report the chart. It reports the
implementer's choice of exception list, with the app's name on it, to someone
asking about their marriage. Putting it behind a setting does not fix that: a
setting still ships a default, the default still decides, and the user still
reads a yes.

So: the geometry, which every Tamil source agrees on, and the exemptions as named
line items an astrologer can weigh. See ``docs/dosham-sources.md``.

Three findings worth carrying in your head, because each contradicts something
widely repeated:

* **The lagna reading is primary, not the Moon.** The Tamil sources that rank the
  three references put லக்னம் first. The "Moon-heavy" framing is not Tamil.
* **Debilitation cancels.** நீச்ச செவ்வாய்க்கு பலம் இல்லை -- a debilitated Mars
  has no strength to do harm. So Kadagam exempts for the same reason Mesham and
  Magaram do, which is the most counterintuitive rule here.
* **Venus as a third reference is not a Tamil signature.** It is used
  pan-Indially. It is here because Tamil sources use it, not because it
  distinguishes Tamil practice.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bhava import bhava_of
from .zodiac import GRAHAS, MARS, MOON, VENUS, Term

SEVVAI = Term("Sevvai dosham", "செவ்வாய் தோஷம்", "Sevvai dosham", "SD", "செவ்")

#: The Tamil headline noun for the exemptions. **விதிவிலக்குகள்**, not
#: நிவர்த்தி -- which is attested only as a tag and collides with பரிகாரம்
#: (remedy), a different thing entirely.
EXEMPTIONS = Term("Exemptions", "விதிவிலக்குகள்", "Vithivilakkugal", "Ex", "விதி")


class Reference(Enum):
    """Where Mars is counted from. Ordered by the weight Tamil sources give.

    All three are checked, and a flag from any one counts -- Tamil sources treat
    them as alternatives, not as conditions that must agree.
    """

    LAGNA = "lagna"
    MOON = "moon"
    VENUS = "venus"


REFERENCE_NAMES: dict[Reference, Term] = {
    Reference.LAGNA: Term("From the lagna", "லக்னத்திலிருந்து", "Lagnaththilirunthu"),
    Reference.MOON: Term("From the Moon", "ராசியிலிருந்து", "Raasiyilirunthu"),
    Reference.VENUS: Term("From Venus", "சுக்கிரனிலிருந்து", "Sukkiranilirunthu"),
}

#: The three house sets in mainstream Tamil use, and the classical one.
#:
#: Reported side by side rather than chosen between. A chart with Mars in the
#: lagna is flagged by ``tamil_traditional`` and clean under ``tamil_common``;
#: Mars in the 2nd is the reverse. Showing which conventions flag a chart is both
#: honest and computable; picking one and printing a yes is neither.
HOUSE_SETS: dict[str, frozenset[int]] = {
    # The plurality across Tamil sources -- the 2nd in, the 1st out.
    "tamil_common": frozenset({2, 4, 7, 8, 12}),
    # Dinakaran calls this பாரம்பரிய முறை, the traditional method.
    "tamil_traditional": frozenset({1, 2, 4, 7, 8, 12}),
    # The Sanskrit verse: lagne vyaye ca patale jamitre castame kuje.
    # No 2nd house -- that is the South Indian addition.
    "classical": frozenset({1, 4, 7, 8, 12}),
}

DEFAULT_HOUSE_SET = "tamil_common"

#: The 7th and the 8th are கடுமையான, the rest மிதமான. No Tamil source found
#: ranks the 7th against the 8th, so this module does not either -- they are one
#: tier, and claiming an order between them would be inventing a distinction.
SEVERE_HOUSES: frozenset[int] = frozenset({7, 8})


@dataclass(frozen=True)
class Exemption:
    """One cancellation condition, named and attributed rather than totalled.

    ``provenance`` says how well attested the condition is, because they are not
    equal: some are stated by many Tamil sources, others by one, and at least one
    candidate is so broad it would cancel most charts. An astrologer weighing
    these needs to see which is which.
    """

    key: str
    name: Term
    applies: bool
    detail: str
    provenance: str


@dataclass(frozen=True)
class Reading:
    """Mars's placement from one reference point."""

    reference: Reference
    house: int
    #: Which of the named conventions include this house.
    flagged_by: tuple[str, ...]
    severe: bool

    @property
    def reference_name(self) -> Term:
        return REFERENCE_NAMES[self.reference]


@dataclass(frozen=True)
class SevvaiReport:
    """The inputs an astrologer needs, and no conclusion.

    Note what is absent and will stay absent: ``present``, ``cancelled``, a
    percentage, and any sentence about marriage. ``flagged_count`` is a count of
    *conventions*, not a severity score.
    """

    readings: tuple[Reading, ...]
    exemptions: tuple[Exemption, ...]
    mars_rasi: int

    @property
    def flagged_conventions(self) -> tuple[str, ...]:
        """Which house-set conventions flag this chart from at least one point."""
        out: list[str] = []
        for reading in self.readings:
            for name in reading.flagged_by:
                if name not in out:
                    out.append(name)
        return tuple(out)

    @property
    def active_exemptions(self) -> tuple[Exemption, ...]:
        return tuple(e for e in self.exemptions if e.applies)


def _exemptions(chart, mars_rasi: int) -> tuple[Exemption, ...]:
    """The cancellation conditions, evaluated but never summed.

    Only the layers no Tamil source disputes the *direction* of are computed
    here. The broad ones -- "Mars conjunct any malefic", which would cancel most
    charts -- are deliberately not included: an exemption that fires almost
    always is not information.
    """
    from . import dignity, drishti

    lagna = chart.lagna.rasi
    jupiter_rasi = chart.grahas[4].position.rasi
    mars_dignity = dignity.assess(MARS, chart.grahas[MARS].longitude)

    jupiter_linked = (
        jupiter_rasi == mars_rasi
        or drishti.aspects_rasi(4, jupiter_rasi, mars_rasi)
    )

    return (
        Exemption(
            key="mars_dignity",
            name=Term("Mars in own, exalted or debilitated sign",
                      "செவ்வாய் ஆட்சி, உச்சம் அல்லது நீச்சம்",
                      "Sevvai aatchi, ucham allathu neecham"),
            applies=mars_dignity.dignity in (
                dignity.Dignity.OWN, dignity.Dignity.MOOLATRIKONA,
                dignity.Dignity.EXALTED, dignity.Dignity.DEBILITATED,
            ),
            detail=(
                f"Mars is {mars_dignity.name.en.lower()} in "
                f"{GRAHAS[MARS].en}'s placement. Debilitation counts here as "
                "well as strength: நீச்ச செவ்வாய்க்கு பலம் இல்லை -- a "
                "debilitated Mars has no force with which to harm."
            ),
            provenance="widely attested in Tamil sources",
        ),
        Exemption(
            key="lagna_yogakaraka",
            name=Term("Mars is yogakaraka for this lagna",
                      "செவ்வாய் யோககாரகன்", "Sevvai yogakaarakan"),
            applies=lagna in (3, 4),          # Kadagam, Simmam
            detail=(
                "Mars owns a kendra and a kona from Kadagam and Simmam lagnas, "
                "so it acts as yogakaraka. A wider variant also exempts Mesham "
                "and Viruchigam, which Mars rules."
            ),
            provenance="attested (Sakthi Vikatan); the wider variant differs",
        ),
        Exemption(
            key="jupiter_link",
            name=Term("Jupiter conjunct or aspecting Mars",
                      "குரு சேர்க்கை அல்லது பார்வை", "Guru serkkai allathu paarvai"),
            applies=jupiter_linked,
            detail=(
                "Jupiter is with Mars or looks at it."
                if jupiter_linked else "Jupiter neither joins nor aspects Mars."
            ),
            provenance="attested in Tamil, in a broad three-limb form",
        ),
        Exemption(
            key="venus_signs",
            name=Term("Mars in Rishabam or Thulam",
                      "செவ்வாய் ரிஷபம் அல்லது துலாம்",
                      "Sevvai rishabam allathu thulaam"),
            applies=mars_rasi in (1, 6),
            detail="Mars stands in one of Venus's own signs.",
            provenance="attested (Maalaimalar), corroborated once",
        ),
    )


def sevvai(chart, house_set: str = DEFAULT_HOUSE_SET) -> SevvaiReport:
    """Mars's placement from all three reference points, and the exemptions.

    ``house_set`` selects which convention is treated as primary for the
    ``severe`` flag, but every convention's verdict is reported on every reading,
    so the choice changes emphasis rather than outcome.
    """
    if house_set not in HOUSE_SETS:
        raise ValueError(
            f"Unknown house set {house_set!r}. "
            f"Known: {', '.join(sorted(HOUSE_SETS))}."
        )

    mars_rasi = chart.grahas[MARS].position.rasi
    points = {
        Reference.LAGNA: chart.lagna.rasi,
        Reference.MOON: chart.grahas[MOON].position.rasi,
        Reference.VENUS: chart.grahas[VENUS].position.rasi,
    }

    readings = []
    for reference, rasi in points.items():
        house = bhava_of(mars_rasi, rasi)
        flagged = tuple(
            name for name, houses in HOUSE_SETS.items() if house in houses
        )
        readings.append(Reading(
            reference=reference,
            house=house,
            flagged_by=flagged,
            severe=house in SEVERE_HOUSES and house in HOUSE_SETS[house_set],
        ))

    return SevvaiReport(
        readings=tuple(readings),
        exemptions=_exemptions(chart, mars_rasi),
        mars_rasi=mars_rasi,
    )
