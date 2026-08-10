"""Graha dignity -- உச்சம், நீசம், ஆட்சி and the rest of the ladder.

After "which rasi is it in", the next thing any Tamil astrologer reads off a
chart is *how well placed* each graha is. A graha in its exaltation sign
(உச்சம்) delivers what it promises; the same graha in the opposite sign
(நீசம்) is held to struggle to. It is the difference between a Saturn that
builds and a Saturn that grinds, and it is visible at a glance on a printed
jathagam because the states are marked right next to the graha.

This module answers that question and nothing else. It is pure arithmetic on a
sidereal longitude plus two fixed tables, so like the vargas it inherits the
validated accuracy of ``core.positions`` and adds no astronomical risk.

Three states are marked on a chart and they are independent of one another:

* **வக்ரம் (vakram)** -- retrograde. Already computed in ``core.positions``.
* **நீசம் / உச்சம்** -- the dignity ladder here.
* **அஸ்தங்கதம் (asthangatham)** -- combust, burnt by proximity to the Sun.

A graha can be all three at once, and each says something different.

Where the classical sources genuinely disagree -- and for Rahu and Ketu they do
-- this module declines to pick. Returning a confidently wrong dignity for the
nodes would be worse than returning none, because nothing downstream could tell
the difference.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .angles import norm180, norm360
from .zodiac import (
    GRAHAS,
    JUPITER,
    KETU,
    MARS,
    MERCURY,
    MOON,
    RASI_LORDS,
    RASI_SPAN,
    RAHU,
    SATURN,
    SUN,
    VENUS,
    Term,
)


class Dignity(Enum):
    """The ladder, best to worst.

    ``value`` is the API/JSON name; the Tamil and English labels live in
    :data:`DIGNITY_NAMES`.
    """

    EXALTED = "exalted"
    MOOLATRIKONA = "moolatrikona"
    OWN = "own"
    GREAT_FRIEND = "great_friend"
    FRIEND = "friend"
    NEUTRAL = "neutral"
    ENEMY = "enemy"
    DEBILITATED = "debilitated"
    UNDEFINED = "undefined"


DIGNITY_NAMES: dict[Dignity, Term] = {
    Dignity.EXALTED: Term("Exalted", "உச்சம்", "Ucham", "Ex", "உச்"),
    Dignity.MOOLATRIKONA: Term("Moolatrikona", "மூலத்திரிகோணம்", "Moolathirikonam", "MT", "மூல"),
    Dignity.OWN: Term("Own sign", "ஆட்சி", "Aatchi", "Own", "ஆட்"),
    Dignity.GREAT_FRIEND: Term("Great friend", "அதிமித்திரம்", "Athimithiram", "GF", "அதிந"),
    Dignity.FRIEND: Term("Friend", "நட்பு", "Natpu", "Fr", "நட்"),
    Dignity.NEUTRAL: Term("Neutral", "சமம்", "Samam", "Neu", "சம"),
    Dignity.ENEMY: Term("Enemy", "பகை", "Pagai", "En", "பகை"),
    Dignity.DEBILITATED: Term("Debilitated", "நீசம்", "Neecham", "Db", "நீச"),
    Dignity.UNDEFINED: Term("Not assigned", "வரையறுக்கப்படவில்லை", "Varaiyarukkappadavillai", "--", "--"),
}

#: Deep exaltation point (paramoccha) for each graha, in absolute sidereal
#: degrees. The *sign* containing it is the exaltation sign; the exact degree is
#: where the strength peaks, and how near a graha sits to it is what separates a
#: nominally exalted graha from a spectacular one.
#:
#: Debilitation is not a second table -- it is exactly 180 degrees from
#: exaltation, by definition, so deriving it removes any chance of the two
#: disagreeing.
#:
#: Rahu and Ketu are deliberately absent. BPHS assigns them no exaltation, and
#: later practice splits between Taurus/Scorpio and Gemini/Sagittarius with no
#: settled winner. Picking one silently would hand the user a dignity that looks
#: authoritative and is a coin toss.
EXALTATION: dict[int, float] = {
    SUN: 0 * RASI_SPAN + 10.0,        # Mesha 10
    MOON: 1 * RASI_SPAN + 3.0,        # Rishabam 3
    MARS: 9 * RASI_SPAN + 28.0,       # Magaram 28
    MERCURY: 5 * RASI_SPAN + 15.0,    # Kanni 15
    JUPITER: 3 * RASI_SPAN + 5.0,     # Kadagam 5
    VENUS: 11 * RASI_SPAN + 27.0,     # Meenam 27
    SATURN: 6 * RASI_SPAN + 20.0,     # Thulam 20
}

#: Moolatrikona: a degree range a graha is especially at home in, ranked just
#: below exaltation. ``(rasi, from_degree, to_degree)``, half-open at the top, so
#: the remainder of the sign falls through to whatever it would otherwise be.
#:
#: Six of the seven lie inside the graha's **own** sign. The **Moon is the
#: exception** and it is a real one, not a typo: its moolatrikona is Rishabam
#: 4-30, which is its *exaltation* sign, while the whole of its own sign Kadagam
#: is plain own-sign. Any check that asserts "moolatrikona is always in the own
#: sign" will fail here, and the data is what is right.
#:
#: A consequence worth knowing: because Rishabam is also the Moon's exaltation
#: sign, and because :func:`assess` lets the whole exaltation sign carry that
#: label, the Moon's moolatrikona range is never reached by the dignity ladder.
#: The same is true of Mercury's, inside Kanni. Both entries stay here because
#: shadbala -- planetary strength scoring, a later phase -- weights moolatrikona
#: separately from exaltation and will need them.
MOOLATRIKONA: dict[int, tuple[int, float, float]] = {
    SUN: (4, 0.0, 20.0),        # Simmam 0-20
    MOON: (1, 4.0, 30.0),       # Rishabam 4-30
    MARS: (0, 0.0, 12.0),       # Mesham 0-12
    MERCURY: (5, 16.0, 20.0),   # Kanni 16-20
    JUPITER: (8, 0.0, 10.0),    # Dhanusu 0-10
    VENUS: (6, 0.0, 15.0),      # Thulam 0-15
    SATURN: (10, 0.0, 20.0),    # Kumbam 0-20
}

#: Natural (naisargika) friendship, per Brihat Parashara Hora. Read as
#: ``FRIENDS[graha]`` = the grahas it treats as friends. Anything neither friend
#: nor enemy is neutral.
#:
#: This relation is **not symmetric** and that is not a typo: the Moon counts the
#: Sun a friend while the Sun counts the Moon a friend too, but Mercury is an
#: enemy of the Moon while the Moon is merely neutral to Mercury. Any "fix" that
#: makes the table symmetric is wrong.
FRIENDS: dict[int, frozenset[int]] = {
    SUN: frozenset({MOON, MARS, JUPITER}),
    MOON: frozenset({SUN, MERCURY}),
    MARS: frozenset({SUN, MOON, JUPITER}),
    MERCURY: frozenset({SUN, VENUS}),
    JUPITER: frozenset({SUN, MOON, MARS}),
    VENUS: frozenset({MERCURY, SATURN}),
    SATURN: frozenset({MERCURY, VENUS}),
}

ENEMIES: dict[int, frozenset[int]] = {
    SUN: frozenset({VENUS, SATURN}),
    MOON: frozenset(),
    MARS: frozenset({MERCURY}),
    MERCURY: frozenset({MOON}),
    JUPITER: frozenset({MERCURY, VENUS}),
    VENUS: frozenset({SUN, MOON}),
    SATURN: frozenset({SUN, MOON, MARS}),
}

#: Distance from the Sun, in degrees, inside which a graha is held to be burnt
#: (அஸ்தங்கதம் / combust). Mercury and Venus take a tighter bound when
#: retrograde, which is why the retrograde flag is an argument rather than an
#: afterthought -- those two spend a good deal of their time retrograde and near
#: the Sun, which is exactly the combination this distinguishes.
COMBUSTION: dict[int, float] = {
    MOON: 12.0,
    MARS: 17.0,
    MERCURY: 14.0,
    JUPITER: 11.0,
    VENUS: 10.0,
    SATURN: 15.0,
}

COMBUSTION_RETROGRADE: dict[int, float] = {
    MERCURY: 12.0,
    VENUS: 8.0,
}

ASTHANGATHAM = Term("Combust", "அஸ்தங்கதம்", "Asthangatham", "Cb", "அஸ்")
VAKRAM = Term("Retrograde", "வக்ரம்", "Vakram", "R", "வக்")


def exaltation_point(graha: int) -> float | None:
    return EXALTATION.get(graha)


def debilitation_point(graha: int) -> float | None:
    """Exactly opposite the exaltation point, by definition rather than by table."""
    point = EXALTATION.get(graha)
    return None if point is None else norm360(point + 180.0)


def is_in_moolatrikona(graha: int, longitude: float) -> bool:
    entry = MOOLATRIKONA.get(graha)
    if entry is None:
        return False
    rasi, low, high = entry
    lon = norm360(longitude)
    return rasi * RASI_SPAN + low <= lon < rasi * RASI_SPAN + high


@dataclass(frozen=True)
class GrahaDignity:
    """How well a graha is placed, and how that was decided.

    ``reason`` names the rule that fired in plain words. This project's third
    commitment is to show its work, and a dignity is the first place a user will
    ask "why?" -- "Saturn is in Thulam, which is its exaltation sign" is a very
    different answer from "Saturn is in a sign ruled by Venus, whom it counts a
    friend", even though both are just a label on a table row.
    """

    graha: int
    dignity: Dignity
    #: Degrees from the deep exaltation point, 0-180. None for Rahu and Ketu.
    #: Zero is the peak of exaltation; 180 is the depth of debilitation.
    from_exaltation: float | None
    #: The lord of the sign the graha occupies -- its dispositor.
    dispositor: int
    combust: bool
    reason: str

    @property
    def name(self) -> Term:
        return DIGNITY_NAMES[self.dignity]

    @property
    def is_debilitated(self) -> bool:
        return self.dignity is Dignity.DEBILITATED

    @property
    def is_exalted(self) -> bool:
        return self.dignity is Dignity.EXALTED


def _relationship(graha: int, lord: int) -> tuple[Dignity, str]:
    if lord in FRIENDS.get(graha, frozenset()):
        return Dignity.FRIEND, (
            f"{GRAHAS[graha].en} is in a sign ruled by {GRAHAS[lord].en}, "
            "whom it counts a natural friend"
        )
    if lord in ENEMIES.get(graha, frozenset()):
        return Dignity.ENEMY, (
            f"{GRAHAS[graha].en} is in a sign ruled by {GRAHAS[lord].en}, "
            "its natural enemy"
        )
    return Dignity.NEUTRAL, (
        f"{GRAHAS[graha].en} is in a sign ruled by {GRAHAS[lord].en}, "
        "towards whom it is neutral"
    )


def assess(
    graha: int,
    longitude: float,
    *,
    sun_longitude: float | None = None,
    retrograde: bool = False,
) -> GrahaDignity:
    """The dignity of one graha at one sidereal longitude.

    Order of precedence, highest first: exaltation sign, debilitation sign,
    moolatrikona range, own sign, then the natural friendship of the sign's
    lord. The whole sign carries the exaltation or debilitation -- the exact
    degree only sets *how* exalted, which :attr:`GrahaDignity.from_exaltation`
    reports.

    Mercury is the awkward case worth knowing about: Kanni is at once its
    exaltation sign, its moolatrikona and its own sign. Exaltation wins here, as
    it does in most software, though some texts subdivide the sign into
    exaltation to 15 degrees, moolatrikona to 20 and own sign beyond.
    """
    lon = norm360(longitude)
    rasi = int(lon * 12.0 / 360.0) % 12
    lord = RASI_LORDS[rasi]

    combust = False
    if sun_longitude is not None and graha not in (SUN, RAHU, KETU):
        limit = COMBUSTION.get(graha)
        if limit is not None:
            if retrograde:
                limit = COMBUSTION_RETROGRADE.get(graha, limit)
            combust = abs(norm180(lon - norm360(sun_longitude))) < limit

    point = EXALTATION.get(graha)
    if point is None:
        # Rahu and Ketu. They still have a dispositor and can still be burnt,
        # but the ladder does not apply -- see the note on EXALTATION.
        return GrahaDignity(
            graha=graha,
            dignity=Dignity.UNDEFINED,
            from_exaltation=None,
            dispositor=lord,
            combust=combust,
            reason=(
                f"{GRAHAS[graha].en} is a shadow graha. The classical sources "
                "assign it no exaltation, and later practice is split between "
                "two, so no dignity is claimed here."
            ),
        )

    from_exaltation = abs(norm180(lon - point))
    exalt_rasi = int(point * 12.0 / 360.0) % 12
    debil_rasi = (exalt_rasi + 6) % 12

    def built(dignity: Dignity, reason: str) -> GrahaDignity:
        return GrahaDignity(
            graha=graha, dignity=dignity, from_exaltation=from_exaltation,
            dispositor=lord, combust=combust, reason=reason,
        )

    if rasi == exalt_rasi:
        return built(Dignity.EXALTED, (
            f"{GRAHAS[graha].en} is in its exaltation sign, "
            f"{from_exaltation:.1f} degrees from its deep exaltation point"
        ))
    if rasi == debil_rasi:
        return built(Dignity.DEBILITATED, (
            f"{GRAHAS[graha].en} is in its debilitation sign, the rasi opposite "
            f"its exaltation, {180.0 - from_exaltation:.1f} degrees from the "
            "deepest point of debilitation"
        ))
    if is_in_moolatrikona(graha, lon):
        return built(Dignity.MOOLATRIKONA, (
            f"{GRAHAS[graha].en} is in the moolatrikona portion of its own sign"
        ))
    if lord == graha:
        return built(Dignity.OWN, f"{GRAHAS[graha].en} is in its own sign")

    dignity, reason = _relationship(graha, lord)
    return built(dignity, reason)


def assess_chart(chart) -> dict[int, GrahaDignity]:
    """Dignity for all nine grahas of a :class:`~jyotish.core.positions.ChartPositions`."""
    sun = chart.grahas[SUN].longitude
    return {
        gi: assess(
            gi,
            chart.grahas[gi].longitude,
            sun_longitude=sun,
            retrograde=chart.grahas[gi].retrograde,
        )
        for gi in range(9)
    }
