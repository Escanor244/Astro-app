"""Divisional charts (vargas) -- the Shodashavarga, sixteen divisions.

A varga subdivides each 30-degree rasi into N parts and maps each part onto a
rasi, producing a second chart from the same longitudes. The most important by
far is **D9 Navamsa** (நவாம்சம்), which every Tamil astrologer reads alongside
the Rasi chart -- it is treated as the chart of marriage, dharma, and the inner
strength of each graha. A Rasi chart shown without a Navamsam looks incomplete
to anyone who actually practises.

Design notes:

* Every division is a pure function of sidereal longitude. Nothing here touches
  the ephemeris, so vargas inherit the validated accuracy of ``core.positions``
  exactly, with no new astronomical risk.
* Several divisions collapse to a single expression once you notice that N parts
  per sign gives 12*N parts per circle, and 12*N is divisible by 12. D9 is the
  clearest case: ``floor(longitude / (10/3)) % 12`` reproduces the whole
  movable-from-itself / fixed-from-9th / dual-from-5th rule with no special
  cases, because that rule *is* what continuous counting produces.
* D30 is genuinely irregular -- unequal parts, ruled by five grahas -- and is
  written out longhand because there is no shortcut to find.

Classical sources differ on a few of the rarer divisions. Where they do, the
choice here is the one that agrees with jyotishganit's independent
implementation, which the test-suite cross-checks graha by graha across every
birth fixture.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.angles import norm360
from ..core.zodiac import RASI_SPAN, Term

# Sign classifications. Indices are 0-based: 0 = Mesham/Aries.
#
#   movable (chara)      Aries, Cancer, Libra, Capricorn        rasi % 3 == 0
#   fixed   (sthira)     Taurus, Leo, Scorpio, Aquarius         rasi % 3 == 1
#   dual    (dvisvabhava) Gemini, Virgo, Sagittarius, Pisces    rasi % 3 == 2
#
# "Odd" means the 1st, 3rd, 5th ... sign counting from Aries, so index 0 is odd.

ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO = 0, 1, 2, 3, 4, 5
LIBRA, SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 6, 7, 8, 9, 10, 11


def is_odd_sign(rasi: int) -> bool:
    return rasi % 2 == 0


def is_movable(rasi: int) -> bool:
    return rasi % 3 == 0


def is_fixed(rasi: int) -> bool:
    return rasi % 3 == 1


def is_dual(rasi: int) -> bool:
    return rasi % 3 == 2


@dataclass(frozen=True)
class Varga:
    """One divisional chart in the Shodashavarga."""

    code: str        # "D9"
    divisions: int   # 9
    name: Term
    significance: str

    @property
    def part_span(self) -> float:
        """Degrees per part, for the regular divisions."""
        return RASI_SPAN / self.divisions


# --- the sixteen divisions --------------------------------------------------

VARGAS: dict[str, Varga] = {
    "D1": Varga("D1", 1, Term("Rasi", "ராசி", "Raasi"),
                "the birth chart itself; body and overall life"),
    "D2": Varga("D2", 2, Term("Hora", "ஹோரை", "Horai"),
                "wealth and resources"),
    "D3": Varga("D3", 3, Term("Drekkana", "திரேக்காணம்", "Drekkanam"),
                "siblings, courage, initiative"),
    "D4": Varga("D4", 4, Term("Chaturthamsa", "சதுர்த்தாம்சம்", "Chathurthamsam"),
                "property, fixed assets, home"),
    "D7": Varga("D7", 7, Term("Saptamsa", "சப்தாம்சம்", "Sapthamsam"),
                "children and progeny"),
    "D9": Varga("D9", 9, Term("Navamsa", "நவாம்சம்", "Navamsam"),
                "marriage, dharma, and the true strength of every graha"),
    "D10": Varga("D10", 10, Term("Dasamsa", "தசாம்சம்", "Dasamsam"),
                 "career, profession, status"),
    "D12": Varga("D12", 12, Term("Dwadasamsa", "துவாதசாம்சம்", "Dhuvadhasamsam"),
                 "parents and ancestry"),
    "D16": Varga("D16", 16, Term("Shodasamsa", "ஷோடசாம்சம்", "Shodasamsam"),
                 "vehicles, comforts, happiness"),
    "D20": Varga("D20", 20, Term("Vimsamsa", "விம்சாம்சம்", "Vimsamsam"),
                 "spiritual practice and devotion"),
    "D24": Varga("D24", 24, Term("Chaturvimsamsa", "சதுர்விம்சாம்சம்", "Chathurvimsamsam"),
                 "learning and education"),
    "D27": Varga("D27", 27, Term("Bhamsa", "பாம்சம்", "Bhamsam"),
                 "strengths and weaknesses; vitality"),
    "D30": Varga("D30", 30, Term("Trimsamsa", "திரிம்சாம்சம்", "Thrimsamsam"),
                 "misfortunes and character flaws"),
    "D40": Varga("D40", 40, Term("Khavedamsa", "கவேதாம்சம்", "Kavedhamsam"),
                 "maternal legacy and auspiciousness"),
    "D45": Varga("D45", 45, Term("Akshavedamsa", "அக்ஷவேதாம்சம்", "Akshavedhamsam"),
                 "paternal legacy and general conduct"),
    "D60": Varga("D60", 60, Term("Shashtiamsa", "ஷஷ்டியம்சம்", "Shashtiyamsam"),
                 "past-life karma; the finest division"),
}

#: Canonical display order.
VARGA_ORDER = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
               "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]


def _split(longitude: float, divisions: int) -> tuple[int, int]:
    """Decompose a longitude into (rasi, part-within-rasi) for an N-part division.

    Both values come from one integer count of parts from Aries 0, so they can
    never disagree with each other. Deriving them separately -- rasi from
    ``longitude // 30`` and the part from ``(longitude % 30) // part_span`` --
    looks equivalent but is not, because ``longitude % 30`` loses precision for
    large longitudes and can land the two on opposite sides of a boundary.

    The part is counted in *degrees within the rasi*, never from the absolute
    longitude. Two reasons, and both bit us:

    * It is how the classical rules are phrased -- "the first 3 degrees 20
      minutes of the sign" -- so it is the faithful formulation.
    * It is far better conditioned. Scaling an absolute longitude introduces its
      own rounding: 93.33333333333333 * 9 rounds *up* to exactly 840.0, so
      dividing by 30 yields 28.0 and lands a graha in the next navamsa even
      though the true product is just under 840. Degrees within a rasi stay
      below 30, where that error cannot reach a boundary.

    Multiply before dividing within that domain, though. The obvious
    ``degrees // (RASI_SPAN / divisions)`` is wrong at exact boundaries: 30/9 is
    not representable in binary, so 20 degrees -- precisely the start of the 7th
    navamsa -- divides to 5.999999... and floors into the previous navamsa.
    ``degrees * divisions / RASI_SPAN`` keeps both operands exact there
    (20*9 = 180, 180/30 = 6.0).

    None of this moves a graha by a meaningful amount -- the disagreements are
    around 1e-14 degrees, or 1e-11 arcseconds -- but a chart should not depend
    on which of two equivalent-looking expressions a division happens to use.
    """
    lon = norm360(longitude)
    rasi = int(lon // RASI_SPAN)
    degrees = lon - rasi * RASI_SPAN
    part = min(int(degrees * divisions / RASI_SPAN), divisions - 1)
    return min(rasi, 11), part


def _continuous(longitude: float, divisions: int) -> int:
    """Rasi reached by counting parts continuously from Aries 0.

    Valid whenever the classical starting-sign rule is equivalent to unbroken
    counting around the zodiac -- true for D9 and D27, and proved against the
    longhand rules in the tests.
    """
    rasi, part = _split(longitude, divisions)
    return (rasi * divisions + part) % 12


def _part_index(longitude: float, divisions: int) -> int:
    """Which part of its own rasi a longitude falls in, 0-based."""
    return _split(longitude, divisions)[1]


def _trimsamsa(rasi: int, degrees: float) -> int:
    """D30: five unequal parts ruled by Mars, Saturn, Jupiter, Mercury, Venus.

    The only division with unequal parts. Per Brihat Parashara Hora Shastra, odd
    signs run Mars-Saturn-Jupiter-Mercury-Venus over 5/5/8/7/5 degrees, and even
    signs are the exact reverse: Venus-Mercury-Jupiter-Saturn-Mars over 5/7/8/5/5,
    giving boundaries at 5, 12, 20 and 25 degrees. No counting shortcut exists,
    so the boundaries are written out.

    Known deviation: jyotishganit implements the even-sign case as Saturn 12-19,
    Jupiter 19-24, Mars 24-30. That swaps Jupiter and Saturn and does not mirror
    its own odd-sign sequence, so we do not follow it. ``test_vargas.py`` pins
    this disagreement deliberately rather than silently excluding D30 from the
    cross-check.
    """
    if is_odd_sign(rasi):
        if degrees < 5:
            return ARIES        # Mars
        if degrees < 10:
            return AQUARIUS     # Saturn
        if degrees < 18:
            return SAGITTARIUS  # Jupiter
        if degrees < 25:
            return GEMINI       # Mercury
        return LIBRA            # Venus

    if degrees < 5:
        return TAURUS           # Venus
    if degrees < 12:
        return VIRGO            # Mercury
    if degrees < 20:
        return PISCES           # Jupiter
    if degrees < 25:
        return CAPRICORN        # Saturn
    return SCORPIO              # Mars


def varga_rasi(longitude: float, code: str) -> int:
    """Rasi index (0-11) occupied by ``longitude`` in the given varga.

    Args:
        longitude: sidereal longitude in degrees.
        code: varga code, e.g. ``"D9"``. Case-insensitive.
    """
    code = code.upper()
    if code not in VARGAS:
        raise ValueError(
            f"Unknown varga {code!r}. Known: {', '.join(VARGA_ORDER)}"
        )

    lon = norm360(longitude)
    # Used only by D1, D2 and D30, which key off actual degrees rather than a
    # part index. The regular divisions go through _split instead, so that the
    # rasi they classify on and the part they count are guaranteed consistent.
    rasi = int(lon // RASI_SPAN)
    degrees = lon - rasi * RASI_SPAN

    if code == "D1":
        return rasi

    if code == "D2":
        # Two horas of 15 degrees. Odd signs: Leo then Cancer.
        # Even signs: Cancer then Leo.
        first_half = degrees < 15.0
        if is_odd_sign(rasi):
            return LEO if first_half else CANCER
        return CANCER if first_half else LEO

    if code == "D3":
        # Same sign, then 5th, then 9th from it.
        return (rasi + 4 * _part_index(lon, 3)) % 12

    if code == "D4":
        # Same sign, then 4th, 7th, 10th -- i.e. the kendras.
        return (rasi + 3 * _part_index(lon, 4)) % 12

    if code == "D7":
        # Odd signs count from the sign itself; even signs from the 7th.
        start = rasi if is_odd_sign(rasi) else (rasi + 6) % 12
        return (start + _part_index(lon, 7)) % 12

    if code == "D9":
        # Movable from itself, fixed from the 9th, dual from the 5th -- which is
        # exactly continuous counting, since 108 navamsas close the circle.
        return _continuous(lon, 9)

    if code == "D10":
        # Odd signs from the sign itself; even signs from the 9th.
        start = rasi if is_odd_sign(rasi) else (rasi + 8) % 12
        return (start + _part_index(lon, 10)) % 12

    if code == "D12":
        # Always counted from the sign itself.
        return (rasi + _part_index(lon, 12)) % 12

    if code == "D16":
        # Movable from Aries, fixed from Leo, dual from Sagittarius.
        start = ARIES if is_movable(rasi) else LEO if is_fixed(rasi) else SAGITTARIUS
        return (start + _part_index(lon, 16)) % 12

    if code == "D20":
        # Movable from Aries, fixed from Sagittarius, dual from Leo.
        start = ARIES if is_movable(rasi) else SAGITTARIUS if is_fixed(rasi) else LEO
        return (start + _part_index(lon, 20)) % 12

    if code == "D24":
        # Odd signs from Leo, even signs from Cancer.
        start = LEO if is_odd_sign(rasi) else CANCER
        return (start + _part_index(lon, 24)) % 12

    if code == "D27":
        # Fire from Aries, earth from Cancer, air from Libra, water from
        # Capricorn -- again equivalent to continuous counting.
        return _continuous(lon, 27)

    if code == "D30":
        return _trimsamsa(rasi, degrees)

    if code == "D40":
        # Odd signs from Aries, even signs from Libra.
        start = ARIES if is_odd_sign(rasi) else LIBRA
        return (start + _part_index(lon, 40)) % 12

    if code == "D45":
        # Movable from Aries, fixed from Leo, dual from Sagittarius.
        start = ARIES if is_movable(rasi) else LEO if is_fixed(rasi) else SAGITTARIUS
        return (start + _part_index(lon, 45)) % 12

    if code == "D60":
        # Counted from the sign itself, in half-degree steps.
        return (rasi + _part_index(lon, 60)) % 12

    raise AssertionError(f"unhandled varga {code}")  # pragma: no cover


@dataclass(frozen=True)
class VargaChart:
    """A divisional chart, in the shape the South Indian renderer needs."""

    varga: Varga
    lagna_rasi: int
    graha_rasis: dict[int, int]     # graha index -> rasi index
    retrogrades: frozenset[int]

    def house_of(self, graha: int) -> int:
        """Whole-sign house 1-12 counted from this chart's own lagna."""
        return (self.graha_rasis[graha] - self.lagna_rasi) % 12 + 1


def compute(chart, code: str) -> VargaChart:
    """Build a divisional chart from a computed :class:`ChartPositions`.

    Args:
        chart: the result of :func:`jyotish.core.positions.compute`.
        code: varga code, e.g. ``"D9"``.
    """
    varga = VARGAS[code.upper()]
    return VargaChart(
        varga=varga,
        lagna_rasi=varga_rasi(chart.lagna.longitude, varga.code),
        graha_rasis={
            gi: varga_rasi(gp.longitude, varga.code)
            for gi, gp in chart.grahas.items()
        },
        # Retrogradation is a property of actual motion, so it carries across
        # unchanged from the Rasi chart rather than being recomputed.
        retrogrades=frozenset(
            gi for gi, gp in chart.grahas.items() if gp.retrograde
        ),
    )
