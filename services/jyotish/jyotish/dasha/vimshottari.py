"""Vimshottari dasha -- the 120-year planetary period cycle.

This is the single most-used predictive technique in Indian astrology, and in
Tamil practice it is what a consultation actually runs on: a chart says what is
possible, the dasha says *when*. A Tamil almanac prints a newborn's dasha balance
(திசை இருப்பு) alongside the birth star, and it follows the person for life.

The mechanism in one paragraph. The 27 nakshatras are assigned to the nine grahas
in a fixed repeating order, and each graha owns a fixed number of years summing
to 120. Your first mahadasha is the one belonging to the nakshatra your **Moon**
occupied at birth -- not the Sun, not the lagna -- and you are born partway
through it: the fraction of that nakshatra the Moon has yet to cross is the
fraction of the period still to run. From there the lords follow their fixed
cycle for 120 years and then repeat.

Every level below the mahadasha uses the *same* proportions applied to the level
above, which is why one recursive rule generates all five:

    mahadasha       lord's own years                      6 to 20 years
    antardasha      maha_days  x lord_years / 120         months to years
    pratyantardasha antar_days x lord_years / 120         days to months
    sookshma        pratyantar_days x lord_years / 120    hours to days
    prana           sookshma_days x lord_years / 120      minutes to hours

Each level starts with its own parent's lord and then continues around the same
cycle -- Venus mahadasha opens with Venus antardasha, whose first pratyantardasha
is Venus again.

The whole module is pure arithmetic on a single input, the Moon's sidereal
longitude, so it inherits the validated accuracy of ``core.positions`` and adds
no astronomical risk of its own. What it *does* add is a convention risk, which
is what :data:`YEAR_DAYS` is about.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from ..core.angles import norm360
from ..core.zodiac import GRAHAS, NAKSHATRA_LORDS, NAKSHATRAS, Term

#: The cyclic order of dasha lords.
#:
#: Deliberately *derived* rather than retyped. The Vimshottari order and the
#: nakshatra lord sequence are the same nine grahas in the same rotation -- that
#: identity is the whole reason a birth star selects a dasha -- so writing it
#: twice would create two things that can disagree. ``test_dasha`` pins the
#: derivation, and the table-integrity tests already pin ``NAKSHATRA_LORDS``.
ORDER: tuple[int, ...] = NAKSHATRA_LORDS[:9]

#: Years each graha owns. Keyed by graha index; sums to 120 by construction, and
#: a test asserts it, because a typo here would silently rescale every date the
#: engine ever prints.
YEARS: dict[int, int] = {
    lord: years
    for lord, years in zip(ORDER, (7, 20, 6, 10, 7, 18, 16, 19, 17), strict=True)
}

TOTAL_YEARS = 120

#: Levels, outermost first. Five is where Tamil practice stops; the arithmetic
#: would happily continue, but a prana sub-period is already minutes long and a
#: sixth level would be shorter than the uncertainty in most recorded birth
#: times.
LEVEL_NAMES: tuple[Term, ...] = (
    Term("Mahadasha", "மகா தசை", "Maha dasai", "MD", "மகா"),
    Term("Antardasha", "புத்தி", "Bhukti", "AD", "புத்தி"),
    Term("Pratyantardasha", "அந்தரம்", "Antharam", "PD", "அந்"),
    Term("Sookshma", "சூட்சுமம்", "Sookshmam", "SD", "சூட்"),
    Term("Prana", "பிராணன்", "Praanan", "PR", "பிரா"),
)

MAX_LEVEL = len(LEVEL_NAMES)

#: How many days a "dasha year" is worth.
#:
#: There is no astronomical fact to get right here -- a dasha year is a unit of
#: convention -- and the traditions genuinely differ. But the differences are not
#: all the same size, and that shapes what this setting is for:
#:
#: * The four solar variants below are **astrologically indistinguishable**. The
#:   worst-case spread between any two of them is 0.85 days at sixty dasha
#:   years, 1.7 days across a full cycle. Choosing among them is engineering
#:   taste.
#: * **Savana**, the 360-day civil year of the older sacrificial calendar, is a
#:   different question entirely: 315 days adrift at sixty years, about ten
#:   months. It is a real minority tradition rather than an error, but it is not
#:   what Tamil almanacs print, and an app that silently chose it would disagree
#:   with every one of them.
#:
#: The default is the classical 365 1/4. It is what the textbook worked examples
#: a user will check us against use, it is the value Tamil software vendors name
#: first, and it sits within half a day of Jagannatha Hora's true-sidereal
#: default even sixty years out. The classical justification for a *solar* year
#: at all is Phala Deepika's: one dasha year is the Sun's return to its natal
#: position.
YEAR_DAYS: dict[str, float] = {
    "julian": 365.25,           # the classical 365 1/4 -- our default
    "sidereal": 365.256364,     # the Sun's return to the same star; JHora's default
    "gregorian": 365.2425,      # the civil calendar's mean year
    "tropical": 365.242190,     # equinox to equinox
    "savana": 360.0,            # the sacrificial civil year; ~10 months adrift
}

DEFAULT_YEAR_LENGTH = "julian"


def year_days(name: str = DEFAULT_YEAR_LENGTH) -> float:
    try:
        return YEAR_DAYS[name]
    except KeyError:
        raise ValueError(
            f"Unknown dasha year length {name!r}. "
            f"Known: {', '.join(sorted(YEAR_DAYS))}."
        ) from None


def cycle_from(lord: int) -> tuple[int, ...]:
    """The nine lords in Vimshottari order, rotated to begin at ``lord``."""
    i = ORDER.index(lord)
    return ORDER[i:] + ORDER[:i]


@dataclass(frozen=True)
class Balance:
    """The unexpired portion of the first mahadasha, as almanacs print it.

    ``years``/``months``/``days`` are the conventional rendering, and they are
    not calendar units: a dasha month is one twelfth of a dasha year and a dasha
    day is one thirtieth of that. Rendering "3y 4m 12d" as calendar time would
    drift by days. :attr:`total_days` is the honest number and is what the period
    arithmetic actually uses.
    """

    lord: int
    nakshatra: int
    #: Fraction of the birth nakshatra still to be crossed, in [0, 1].
    remaining_fraction: float
    total_days: float
    years: int
    months: int
    days: int

    @property
    def lord_name(self) -> Term:
        return GRAHAS[self.lord]

    @property
    def nakshatra_name(self) -> Term:
        return NAKSHATRAS[self.nakshatra]

    def format(self, lang: str = "en") -> str:
        return (
            f"{self.lord_name.label(lang)} "
            f"{self.years}y {self.months}m {self.days}d"
        )


def balance_at_birth(
    moon_longitude: float, *, year_length: str = DEFAULT_YEAR_LENGTH
) -> Balance:
    """Which dasha a birth falls in, and how much of it is left.

    The Moon's position *inside* its nakshatra is the whole input. Crossed a
    third of the star, and a third of that lord's period is already spent.

    Multiply before dividing, for the same reason ``zodiac.resolve`` does: 360/27
    is not binary-representable and rounds up, so dividing by it puts an exact
    boundary longitude in the previous nakshatra. Counting in 27ths of the circle
    keeps both operands exact, and it also gives the elapsed fraction for free as
    the remainder -- one expression instead of two that could disagree about
    which nakshatra they are in.
    """
    x = norm360(moon_longitude) * 27.0 / 360.0
    nak = min(int(x), 26)
    remaining = 1.0 - (x - nak)

    lord = NAKSHATRA_LORDS[nak]
    total = remaining * YEARS[lord] * year_days(year_length)

    # The y/m/d split is taken from the *fraction of the period*, not from the
    # day count, so it cannot drift with the year-length convention.
    #
    # Rounded to a nanoyear (about 30 milliseconds) before being split, because
    # the split truncates and truncation turns a float that is one ulp short of a
    # boundary into a completely different reading: a Moon at exactly 0 degrees
    # of a Rahu star came out as 17y 11m 29d instead of the whole 18 years. The
    # rounding is far finer than any real distinction and far coarser than the
    # noise it removes.
    t = round(remaining * YEARS[lord], 9)
    years = int(t)
    months_f = (t - years) * 12.0
    months = int(months_f)
    days = round((months_f - months) * 30.0)

    # Rounding the day can carry, and an uncarried carry prints "11m 30d" --
    # a month that does not exist in a system where a month is thirty days.
    if days >= 30:
        days, months = 0, months + 1
    if months >= 12:
        months, years = 0, years + 1

    return Balance(
        lord=lord,
        nakshatra=nak,
        remaining_fraction=remaining,
        total_days=total,
        years=years,
        months=months,
        days=days,
    )


@dataclass(frozen=True)
class Period:
    """One dasha period at any of the five levels.

    ``lords`` is the full chain from the mahadasha down to this level, so a
    period always knows its own address -- ``(VENUS, SATURN, MERCURY)`` is
    "Venus / Saturn / Mercury". Rendering a breadcrumb never needs the parent.
    """

    lords: tuple[int, ...]
    start: datetime
    end: datetime

    @property
    def lord(self) -> int:
        return self.lords[-1]

    @property
    def level(self) -> int:
        """1 for mahadasha through 5 for prana."""
        return len(self.lords)

    @property
    def lord_name(self) -> Term:
        return GRAHAS[self.lord]

    @property
    def level_name(self) -> Term:
        return LEVEL_NAMES[self.level - 1]

    @property
    def days(self) -> float:
        return (self.end - self.start).total_seconds() / 86400.0

    def contains(self, when: datetime) -> bool:
        """Half-open: ``[start, end)``.

        Half-open matters. Every period's end is the next one's start, so a
        closed interval would report two active dashas at the boundary instant --
        and boundary instants are exactly what a practitioner looks up.
        """
        return self.start <= when < self.end

    def path(self, lang: str = "en", sep: str = " / ") -> str:
        return sep.join(GRAHAS[g].label(lang) for g in self.lords)


def _split(parent_start: datetime, parent_end: datetime, lords: tuple[int, ...],
           first_lord: int) -> list[Period]:
    """Divide a span into nine sub-periods in Vimshottari proportion.

    Boundaries are computed as fractions *of the whole span* rather than by
    accumulating one sub-period onto the last. Accumulating lets rounding
    compound, so the ninth sub-period would end a little before or after its
    parent -- a gap or an overlap at every level, nine times worse at each level
    down. The final end is then snapped to the parent's exactly, so the union of
    the children is precisely the parent no matter how the float lands.
    """
    span = parent_end - parent_start
    out: list[Period] = []
    elapsed = 0

    for lord in cycle_from(first_lord):
        start = parent_start + span * (elapsed / TOTAL_YEARS)
        elapsed += YEARS[lord]
        end = parent_start + span * (elapsed / TOTAL_YEARS)
        out.append(Period(lords=lords + (lord,), start=start, end=end))

    out[-1] = replace(out[-1], end=parent_end)
    return out


def mahadashas(
    birth_utc: datetime,
    moon_longitude: float,
    *,
    year_length: str = DEFAULT_YEAR_LENGTH,
    cycles: int = 2,
) -> list[Period]:
    """The mahadasha sequence, starting with the one running at birth.

    The first period's ``start`` is *before* the birth, because the person was
    born partway through it. That is the honest model and it is what makes every
    sub-period below it come out right: an antardasha of the birth dasha has to
    be measured from where the mahadasha genuinely began, not from the birth. A
    caller that wants the printed "dasha starts at birth" view clamps the first
    start to the birth instant -- but it must not clamp before subdividing.

    ``cycles`` of 2 spans 240 years from that start, which covers any lifetime
    and any progressed lookup a user will ask for.
    """
    balance = balance_at_birth(moon_longitude, year_length=year_length)
    days = year_days(year_length)

    # Wind back to where the running mahadasha actually began.
    elapsed_days = (1.0 - balance.remaining_fraction) * YEARS[balance.lord] * days
    start = birth_utc - timedelta(days=elapsed_days)

    out: list[Period] = []
    for lord in cycle_from(balance.lord) * cycles:
        end = start + timedelta(days=YEARS[lord] * days)
        out.append(Period(lords=(lord,), start=start, end=end))
        start = end
    return out


def children(parent: Period) -> list[Period]:
    """The nine sub-periods of a period, or [] at the deepest level."""
    if parent.level >= MAX_LEVEL:
        return []
    return _split(parent.start, parent.end, parent.lords, parent.lord)


def descend(parent: Period, lords: tuple[int, ...]) -> Period | None:
    """Walk down from ``parent`` following an explicit chain of sub-lords."""
    current = parent
    for lord in lords:
        for child in children(current):
            if child.lord == lord:
                current = child
                break
        else:
            return None
    return current


def chain_at(
    birth_utc: datetime,
    moon_longitude: float,
    when: datetime,
    *,
    depth: int = MAX_LEVEL,
    year_length: str = DEFAULT_YEAR_LENGTH,
    cycles: int = 2,
) -> list[Period]:
    """The nested periods running at an instant, outermost first.

    This is the question a consultation actually asks -- "what is running for
    this person today?" -- so it is a first-class operation rather than something
    the caller assembles from :func:`mahadashas` and :func:`children`.

    Returns ``[]`` when ``when`` falls outside the generated span, which means
    either before the first mahadasha began or more than ``cycles`` x 120 years
    after it. Silently clamping to the nearest period would answer a question the
    user did not ask.
    """
    depth = max(1, min(depth, MAX_LEVEL))
    levels = mahadashas(
        birth_utc, moon_longitude, year_length=year_length, cycles=cycles
    )

    out: list[Period] = []
    for _ in range(depth):
        match = next((p for p in levels if p.contains(when)), None)
        if match is None:
            return out
        out.append(match)
        levels = children(match)
        if not levels:
            break
    return out
