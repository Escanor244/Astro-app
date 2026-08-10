"""Rasi, nakshatra and graha reference data, with the Tamil lexicon.

Tamil names are first-class here, not a translation layer bolted on later. The
app is Tamil-native by design, so every term carries `ta` (Tamil script),
`ta_latin` (romanised, for search and for users who read Tamil phonetically but
not the script) and `en`.

Boundary arithmetic note: a rasi is exactly 30 degrees, a nakshatra exactly
13 degrees 20 minutes (800 arcminutes), and a pada exactly 3 degrees 20 minutes.
These are exact rational divisions of the circle, so we compute indices by
division rather than by table lookup against float boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .angles import norm360

RASI_SPAN = 30.0
NAKSHATRA_SPAN = 360.0 / 27.0  # 13 deg 20 min exactly
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3 deg 20 min exactly


@dataclass(frozen=True)
class Term:
    """A Jyotish term in English, Tamil script, and romanised Tamil.

    ``en_short`` and ``ta_short`` are the conventional abbreviations used where
    space is tight, chiefly the cells of a square chart. They are authored here
    rather than derived by truncation, because truncating Tamil is unsafe: the
    script builds letters from a base character plus combining marks, so cutting
    at a fixed length can drop the mark and silently produce a *different*
    reading. சந்திரன் (Chandran, Moon) cut to two code points becomes சந, and
    சனி (Sani, Saturn) becomes சன -- both valid-looking Tamil, differing only in
    ந vs ன, and neither is the graha it stands for.
    """

    en: str
    ta: str
    ta_latin: str
    en_short: str = ""
    ta_short: str = ""

    def label(self, lang: str = "en") -> str:
        return {"en": self.en, "ta": self.ta, "ta_latin": self.ta_latin}.get(lang, self.en)

    def short(self, lang: str = "en") -> str:
        """Abbreviation for a chart cell, falling back to the full name."""
        if lang == "ta":
            return self.ta_short or self.ta
        return self.en_short or self.en


# --- Grahas -----------------------------------------------------------------
# Ordered by the traditional sequence (Sun through Saturn, then the chaya
# grahas Rahu and Ketu).

SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU = range(9)

#: The Tamil abbreviations are the conventional ones, and they are deliberately
#: not uniform in length: சூ (Sun) and சு (Venus) differ only by a vowel sign,
#: while சந் (Moon) and சனி (Saturn) each need their mark to stay distinct from
#: one another. Any mechanical truncation collapses at least one of these pairs.
GRAHAS: tuple[Term, ...] = (
    Term("Sun", "சூரியன்", "Suriyan", "Su", "சூ"),
    Term("Moon", "சந்திரன்", "Chandran", "Mo", "சந்"),
    Term("Mars", "செவ்வாய்", "Sevvai", "Ma", "செ"),
    Term("Mercury", "புதன்", "Budhan", "Me", "பு"),
    Term("Jupiter", "குரு", "Guru", "Ju", "கு"),
    Term("Venus", "சுக்கிரன்", "Sukkiran", "Ve", "சு"),
    Term("Saturn", "சனி", "Sani", "Sa", "சனி"),
    Term("Rahu", "ராகு", "Raagu", "Ra", "ரா"),
    Term("Ketu", "கேது", "Kethu", "Ke", "கே"),
)

# Sanskrit forms, used by classical rule citations where the source text names
# the graha in Sanskrit.
GRAHA_SANSKRIT: tuple[str, ...] = (
    "Surya", "Chandra", "Mangala", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu",
)


# --- Rasis ------------------------------------------------------------------

RASIS: tuple[Term, ...] = (
    Term("Aries", "மேஷம்", "Mesham"),
    Term("Taurus", "ரிஷபம்", "Rishabam"),
    Term("Gemini", "மிதுனம்", "Mithunam"),
    Term("Cancer", "கடகம்", "Kadagam"),
    Term("Leo", "சிம்மம்", "Simmam"),
    Term("Virgo", "கன்னி", "Kanni"),
    Term("Libra", "துலாம்", "Thulam"),
    Term("Scorpio", "விருச்சிகம்", "Viruchigam"),
    Term("Sagittarius", "தனுசு", "Dhanusu"),
    Term("Capricorn", "மகரம்", "Magaram"),
    Term("Aquarius", "கும்பம்", "Kumbam"),
    Term("Pisces", "மீனம்", "Meenam"),
)

RASI_SANSKRIT: tuple[str, ...] = (
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
)

#: Rasi lord (graha index) for each of the 12 rasis.
RASI_LORDS: tuple[int, ...] = (
    MARS, VENUS, MERCURY, MOON, SUN, MERCURY,
    VENUS, MARS, JUPITER, SATURN, SATURN, JUPITER,
)


# --- Nakshatras -------------------------------------------------------------

NAKSHATRAS: tuple[Term, ...] = (
    Term("Ashwini", "அசுவினி", "Aswini"),
    Term("Bharani", "பரணி", "Bharani"),
    Term("Krittika", "கிருத்திகை", "Krithigai"),
    Term("Rohini", "ரோகிணி", "Rohini"),
    Term("Mrigashira", "மிருகசீரிடம்", "Mirugasirisham"),
    Term("Ardra", "திருவாதிரை", "Thiruvathirai"),
    Term("Punarvasu", "புனர்பூசம்", "Punarpoosam"),
    Term("Pushya", "பூசம்", "Poosam"),
    Term("Ashlesha", "ஆயில்யம்", "Ayilyam"),
    Term("Magha", "மகம்", "Magam"),
    Term("Purva Phalguni", "பூரம்", "Pooram"),
    Term("Uttara Phalguni", "உத்திரம்", "Uthiram"),
    Term("Hasta", "அஸ்தம்", "Astham"),
    Term("Chitra", "சித்திரை", "Chithirai"),
    Term("Swati", "சுவாதி", "Swathi"),
    Term("Vishakha", "விசாகம்", "Visakam"),
    Term("Anuradha", "அனுஷம்", "Anusham"),
    Term("Jyeshtha", "கேட்டை", "Kettai"),
    Term("Mula", "மூலம்", "Moolam"),
    Term("Purva Ashadha", "பூராடம்", "Pooradam"),
    Term("Uttara Ashadha", "உத்திராடம்", "Uthiradam"),
    Term("Shravana", "திருவோணம்", "Thiruvonam"),
    Term("Dhanishta", "அவிட்டம்", "Avittam"),
    Term("Shatabhisha", "சதயம்", "Sadhayam"),
    Term("Purva Bhadrapada", "பூரட்டாதி", "Poorattathi"),
    Term("Uttara Bhadrapada", "உத்திரட்டாதி", "Uthirattathi"),
    Term("Revati", "ரேவதி", "Revathi"),
)

#: Vimshottari dasha lord of each nakshatra. The 9-graha cycle repeats three
#: times across the 27 nakshatras. This same sequence drives KP star lords.
NAKSHATRA_LORDS: tuple[int, ...] = (
    KETU, VENUS, SUN, MOON, MARS, RAHU, JUPITER, SATURN, MERCURY,
) * 3


class ZodiacPosition(NamedTuple):
    """Where a longitude falls in the sidereal zodiac."""

    longitude: float       # absolute sidereal longitude, [0, 360)
    rasi: int              # 0-11
    degrees_in_rasi: float # [0, 30)
    nakshatra: int         # 0-26
    pada: int              # 1-4
    nakshatra_lord: int    # graha index

    @property
    def rasi_term(self) -> Term:
        return RASIS[self.rasi]

    @property
    def nakshatra_term(self) -> Term:
        return NAKSHATRAS[self.nakshatra]

    @property
    def rasi_lord(self) -> int:
        return RASI_LORDS[self.rasi]


def resolve(longitude: float) -> ZodiacPosition:
    """Decompose a sidereal longitude into rasi, nakshatra and pada.

    The pada is what most consumer apps get wrong near boundaries, and it is the
    first thing a practising astrologer checks.

    Multiply before dividing. 360/27 and 360/108 are not binary-representable
    and both round *up*, so ``lon // PADA_SPAN`` puts a boundary value in the
    *previous* bucket: ``resolve(120.0)`` returned Ashlesha pada 4 instead of
    Magha pada 1. Worse, ``rasi`` divides by the exactly-representable 30.0 and
    stayed right, so the record read "Leo + Ashlesha" -- a pairing that cannot
    exist. Counting in whole parts of the circle (108 padas, 27 nakshatras)
    keeps both operands exact. This is the same trap, and the same fix, as
    :func:`jyotish.charts.vargas._split`.
    """
    lon = norm360(longitude)

    rasi = int(lon * 12.0 / 360.0)
    nak = int(lon * 27.0 / 360.0)
    pada = int(lon * 108.0 / 360.0) % 4 + 1

    # Defensive clamps: only reachable if lon is a hair under 360 after fmod.
    rasi = min(rasi, 11)
    nak = min(nak, 26)
    pada = min(pada, 4)

    return ZodiacPosition(
        longitude=lon,
        rasi=rasi,
        degrees_in_rasi=lon - rasi * RASI_SPAN,
        nakshatra=nak,
        pada=pada,
        nakshatra_lord=NAKSHATRA_LORDS[nak],
    )
