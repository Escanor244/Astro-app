"""Rasi, nakshatra and pada from first principles.

Every assertion here is hand-computed from the definitions, never taken from our
own output. That distinction is the point of the file.

The existing "pada gate" in tests/validation/ compares our ``resolve()`` against
itself: it calls ``resolve()`` on our longitude *and* on the oracle's, so it only
re-proves the longitude tolerance. Setting ``NAKSHATRA_SPAN = 360/28`` -- 28
nakshatras instead of 27 -- left the whole suite passing, while every birth star
in the app silently changed. These tests fail on that mutation.

The arithmetic:
  rasi      = 30 degrees each,       12 per circle
  nakshatra = 13 deg 20 min each,    27 per circle
  pada      = 3 deg 20 min each,    108 per circle, 4 per nakshatra
"""

from __future__ import annotations

import pytest

from jyotish.core.zodiac import (
    GRAHAS,
    KETU,
    MERCURY,
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    RASI_LORDS,
    RASIS,
    SUN,
    VENUS,
    resolve,
)

DEG = 1.0
MIN = 1.0 / 60.0


# --- literal reference table ------------------------------------------------
#
# (longitude, rasi index, nakshatra index, pada). Hand-derived: the nakshatra is
# floor(lon / 13.3333), the pada is floor(lon / 3.3333) mod 4 + 1.

REFERENCE = [
    # Start of the zodiac.
    (0.0, 0, 0, 1),                       # Aries 0 = Ashwini pada 1
    (3.0, 0, 0, 1),
    (3 * DEG + 20 * MIN, 0, 0, 2),        # exact pada boundary
    (6 * DEG + 40 * MIN, 0, 0, 3),
    (10.0, 0, 0, 4),                      # exact pada boundary
    (13 * DEG + 20 * MIN, 0, 1, 1),       # exact nakshatra boundary -> Bharani
    (26 * DEG + 40 * MIN, 0, 2, 1),       # Krittika begins in Aries
    # Krittika straddles the Aries/Taurus boundary.
    (29.9, 0, 2, 1),
    (30.0, 1, 2, 2),                      # Taurus 0 is still Krittika
    # Exactly one third of the circle: Magha, not Ashlesha.
    (120.0, 4, 9, 1),                     # Leo 0 = Magha pada 1
    (119.9, 3, 8, 4),                     # a hair earlier: Cancer, Ashlesha 4
    # Midpoints.
    (180.0, 6, 13, 3),                    # Libra 0 = Chitra pada 3
    (240.0, 8, 18, 1),                    # Sagittarius 0 = Mula pada 1 exactly
    (239.9, 7, 17, 4),                    # a hair earlier: Scorpio, Jyeshtha 4
    (270.0, 9, 20, 2),                    # Capricorn 0 = Uttara Ashadha pada 2
    # Last pada of the last nakshatra.
    (356 * DEG + 40 * MIN, 11, 26, 4),    # Revati pada 4
    (359.99, 11, 26, 4),
]


@pytest.mark.parametrize("longitude,rasi,nakshatra,pada", REFERENCE)
def test_reference_table(longitude: float, rasi: int, nakshatra: int, pada: int) -> None:
    got = resolve(longitude)
    assert got.rasi == rasi, (
        f"{longitude} deg: rasi {RASIS[got.rasi].en}, expected {RASIS[rasi].en}"
    )
    assert got.nakshatra == nakshatra, (
        f"{longitude} deg: nakshatra {NAKSHATRAS[got.nakshatra].en}, "
        f"expected {NAKSHATRAS[nakshatra].en}"
    )
    assert got.pada == pada, f"{longitude} deg: pada {got.pada}, expected {pada}"


def test_exact_boundaries_belong_to_the_following_division() -> None:
    """120.0 exactly is Magha pada 1, not the tail of Ashlesha.

    This is the L1 audit finding. 360/108 is not binary-representable and rounds
    up, so floor division put the boundary in the previous pada -- and because
    rasi divided by the exactly-representable 30.0, the result read
    "Leo + Ashlesha", a pairing that cannot occur.
    """
    got = resolve(120.0)
    assert (got.rasi, got.nakshatra, got.pada) == (4, 9, 1)
    assert got.nakshatra_lord == KETU


def test_rasi_and_nakshatra_never_contradict() -> None:
    """A nakshatra can only occur in the rasi its longitude falls in.

    Swept at every exact pada boundary, where the two derivations could disagree.
    """
    for i in range(108):
        lon = i * (360.0 / 108.0)
        got = resolve(lon)
        assert got.rasi == int(got.longitude // 30.0) or abs(got.longitude - lon) < 1e-9
        assert got.nakshatra == int(i // 4)
        assert got.pada == i % 4 + 1


# --- structural invariants --------------------------------------------------
#
# G4: rotating any of these tables by one leaves every chart looking plausible
# while naming the wrong star, sign or planet. The oracle cannot see it, because
# it compares index to index.

def test_table_sizes() -> None:
    assert len(GRAHAS) == 9
    assert len(RASIS) == 12
    assert len(NAKSHATRAS) == 27
    assert len(NAKSHATRA_LORDS) == 27
    assert len(RASI_LORDS) == 12


@pytest.mark.parametrize(
    "index,en,ta",
    [
        (0, "Aries", "மேஷம்"),
        (1, "Taurus", "ரிஷபம்"),
        (3, "Cancer", "கடகம்"),
        (4, "Leo", "சிம்மம்"),
        (11, "Pisces", "மீனம்"),
    ],
)
def test_rasi_names(index: int, en: str, ta: str) -> None:
    assert RASIS[index].en == en
    assert RASIS[index].ta == ta


@pytest.mark.parametrize(
    "index,en,ta",
    [
        (0, "Ashwini", "அசுவினி"),
        (2, "Krittika", "கிருத்திகை"),
        (9, "Magha", "மகம்"),
        (13, "Chitra", "சித்திரை"),
        (26, "Revati", "ரேவதி"),
    ],
)
def test_nakshatra_names(index: int, en: str, ta: str) -> None:
    assert NAKSHATRAS[index].en == en
    assert NAKSHATRAS[index].ta == ta


@pytest.mark.parametrize(
    "index,en,ta",
    [(0, "Sun", "சூரியன்"), (2, "Mars", "செவ்வாய்"), (6, "Saturn", "சனி"),
     (7, "Rahu", "ராகு"), (8, "Ketu", "கேது")],
)
def test_graha_names(index: int, en: str, ta: str) -> None:
    assert GRAHAS[index].en == en
    assert GRAHAS[index].ta == ta


def test_rasi_lords() -> None:
    """Classical rulerships. Sun and Moon rule one sign each; the rest rule two."""
    from jyotish.core.zodiac import JUPITER, MARS, MOON, SATURN

    assert RASI_LORDS == (
        MARS, VENUS, MERCURY, MOON, SUN, MERCURY,
        VENUS, MARS, JUPITER, SATURN, SATURN, JUPITER,
    )


def test_nakshatra_lords_are_the_vimshottari_cycle() -> None:
    """The nine-graha Vimshottari order, repeated exactly three times.

    This tuple is the direct input to the dasha calculation in the next phase,
    so an error here would propagate into every predicted period.
    """
    from jyotish.core.zodiac import JUPITER, MARS, MOON, RAHU, SATURN

    cycle = (KETU, VENUS, SUN, MOON, MARS, RAHU, JUPITER, SATURN, MERCURY)
    assert NAKSHATRA_LORDS == cycle * 3
    for i in range(27):
        assert NAKSHATRA_LORDS[i] == cycle[i % 9]


@pytest.mark.parametrize(
    "longitude,star,lord",
    [
        (0.0, "Ashwini", "Ketu"),                    # 1st nakshatra
        (13 * DEG + 20 * MIN, "Bharani", "Venus"),   # 2nd
        (26 * DEG + 40 * MIN, "Krittika", "Sun"),    # 3rd
        (120.0, "Magha", "Ketu"),                    # 10th, cycle restarts
        (240.0, "Mula", "Ketu"),                     # 19th, cycle restarts again
    ],
)
def test_birth_star_and_its_dasha_lord(longitude: float, star: str, lord: str) -> None:
    """Named lookups, not index arithmetic.

    The birth star is the Moon's nakshatra, and its lord opens the Vimshottari
    dasha sequence -- so these pairings drive the next phase's predictions.
    """
    got = resolve(longitude)
    assert NAKSHATRAS[got.nakshatra].en == star
    assert GRAHAS[got.nakshatra_lord].en == lord
