"""Graha positions and the lagna (ascendant).

Everything returned here is *sidereal* longitude in degrees, for the ayanamsa
requested by the caller. Nothing in this module hardcodes an ayanamsa, because
KP work must run on KP ayanamsa while Parashari work runs on Lahiri, from the
same birth record.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from skyfield.framelib import mean_equator_and_equinox_of_date
from skyfield.functions import mxv, rot_x
from skyfield.nutationlib import iau2000b

from . import ayanamsa as ay
from .angles import norm360
from .birthdata import BirthData
from .ephemeris import get_earth, get_kernel
from .zodiac import (
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
    ZodiacPosition,
    resolve,
)

#: Skyfield body names for the seven visible grahas.
#:
#: DE440s exposes planet centres only for Mercury, Venus, Earth and the Moon;
#: from Mars outward it carries system barycentres. The barycentre offset is
#: metres for Mars and a few thousand km for Jupiter and Saturn, which is far
#: below an arcsecond of geocentric longitude, so the barycentres are the
#: correct targets rather than an approximation we are settling for.
_TARGETS: dict[int, str] = {
    SUN: "sun",
    MOON: "moon",
    MERCURY: "mercury",
    VENUS: "venus",
    MARS: "mars barycenter",
    JUPITER: "jupiter barycenter",
    SATURN: "saturn barycenter",
}

#: Interval used for the retrogradation test, in days.
_MOTION_DT = 0.5


def mean_lunar_node(jd_tt: float) -> float:
    """Mean longitude of the Moon's ascending node, degrees, mean equinox of date.

    Meeus, *Astronomical Algorithms*, chapter 47. Rahu is the ascending node and
    Ketu is exactly opposite it.

    Vedic practice — and KP in particular — uses the *mean* node rather than the
    osculating true node, so that is what we implement as the default.
    """
    t = (jd_tt - 2451545.0) / 36525.0
    return norm360(
        125.0445479
        - 1934.1362891 * t
        + 0.0020754 * t**2
        + t**3 / 467441.0
        - t**4 / 60616000.0
    )


def mean_obliquity(t) -> float:
    """Mean obliquity of the ecliptic, degrees. IAU 2006 (Capitaine et al.)."""
    u = (t.tt - 2451545.0) / 3652500.0
    arcsec = (
        84381.406
        - 4680.93 * u
        - 1.55 * u**2
        + 1999.25 * u**3
        - 51.38 * u**4
        - 249.67 * u**5
        - 39.05 * u**6
        + 7.12 * u**7
        + 27.87 * u**8
        + 5.79 * u**9
        + 2.45 * u**10
    )
    return arcsec / 3600.0


def true_obliquity(t) -> float:
    """True obliquity: mean obliquity plus nutation in obliquity, degrees."""
    return mean_obliquity(t) + iau2000b(t.tt)[1] / 1e7 / 3600.0


def _mean_ecliptic_longitude(apparent, t) -> float:
    """Ecliptic longitude referred to the MEAN equinox and ecliptic of date.

    Ayanamsa is defined against the mean equinox, so graha longitudes must be
    expressed in the same frame before subtracting it. Skyfield's convenient
    ``ecliptic_latlon(epoch='date')`` returns the *true* (nutated) frame.

    Subtracting nutation in longitude from that result is only a first-order
    correction: it ignores the nutation-in-obliquity term, whose effect scales
    with the body's ecliptic latitude. That is invisible for the Sun (latitude
    ~0) but reaches several arcseconds for the Moon (latitude up to 5.3 deg),
    which is precisely the error signature we measured. So we do the frame
    transformation properly instead of patching the longitude afterwards:
    rotate into the mean equator and equinox of date (precession only), then
    tilt by the mean obliquity.
    """
    v = apparent.frame_xyz(mean_equator_and_equinox_of_date).au
    # Negative angle: rot_x(-eps) is the equatorial-to-ecliptic rotation in
    # Skyfield's convention. Verified by the north-celestial-pole identity --
    # the NCP must land at ecliptic longitude 90 deg, and rot_x(+eps) puts it
    # at 270 deg.
    x, y, _z = mxv(rot_x(-math.radians(mean_obliquity(t))), v)
    return norm360(math.degrees(math.atan2(y, x)))


def _tropical_longitude(t, target: str) -> float:
    """Apparent geocentric longitude on the mean ecliptic of date, degrees."""
    apparent = get_earth().at(t).observe(get_kernel()[target]).apparent()
    return _mean_ecliptic_longitude(apparent, t)


def ascendant(t, latitude: float, longitude: float, ayanamsa_deg: float) -> float:
    """Sidereal ascendant (lagna) in degrees.

    The ascendant is the ecliptic point rising on the eastern horizon. With
    theta the local apparent sidereal time expressed in degrees, epsilon the
    true obliquity and phi the geographic latitude:

        Asc = atan2( -cos(theta),  sin(theta) cos(eps) + tan(phi) sin(eps) )

    The atan2 form matters: writing this with a plain arctangent puts the result
    in the wrong quadrant for half of all birth times, which is the classic
    "ascendant is exactly 180 degrees out" bug.

    Frame handling is a two-step, and both steps are needed:

    1. Compute in the *true* equinox frame, from apparent sidereal time and true
       obliquity. This reproduces the Swiss Ephemeris tropical ascendant to
       0.000 arcsec, so it is the geometry every Jyotish program agrees on.
    2. Rotate that result into the *mean* equinox frame by removing nutation in
       longitude, because ayanamsa is defined against the mean equinox.

    Skipping step 2 leaves a systematic error equal to nutation in longitude
    (up to 17 arcsec). Trying to shortcut it by computing directly from mean
    sidereal time and mean obliquity does *not* work either: the obliquity
    enters the geometry itself, not just as an additive longitude term, which
    leaves a few arcseconds of residual.
    """
    # Greenwich apparent sidereal time (hours) -> local, in degrees.
    theta = math.radians(norm360(t.gast * 15.0 + longitude))
    eps = math.radians(true_obliquity(t))
    phi = math.radians(latitude)

    # Guard the poles, where tan(phi) diverges and no ecliptic point rises.
    if abs(latitude) > 89.9:
        phi = math.radians(math.copysign(89.9, latitude))

    asc_true_frame = math.degrees(
        math.atan2(math.cos(theta), -(math.sin(theta) * math.cos(eps) + math.tan(phi) * math.sin(eps)))
    )

    # Step 2: true equinox -> mean equinox, to match the ayanamsa's frame.
    dpsi_deg = iau2000b(t.tt)[0] / 1e7 / 3600.0
    return ay.to_sidereal(norm360(asc_true_frame - dpsi_deg), ayanamsa_deg)


@dataclass(frozen=True)
class GrahaPosition:
    """A graha's placement in the sidereal zodiac."""

    graha: int
    position: ZodiacPosition
    speed_deg_per_day: float
    retrograde: bool

    @property
    def name(self) -> str:
        return GRAHAS[self.graha].en

    @property
    def name_tamil(self) -> str:
        return GRAHAS[self.graha].ta

    @property
    def longitude(self) -> float:
        return self.position.longitude


@dataclass(frozen=True)
class ChartPositions:
    """Everything Phase 1 needs to draw a rasi chart."""

    birth: BirthData
    ayanamsa_system: ay.Ayanamsa
    ayanamsa_value: float
    lagna: ZodiacPosition
    grahas: dict[int, GrahaPosition]

    @property
    def lagna_rasi(self) -> int:
        return self.lagna.rasi

    def house_of(self, graha: int) -> int:
        """Whole-sign house (bhava) number 1-12 occupied by a graha.

        Parashari practice counts houses as whole rasis from the lagna rasi,
        which is also exactly what the South Indian square chart displays.
        """
        return (self.grahas[graha].position.rasi - self.lagna.rasi) % 12 + 1


def _sidereal_with_speed(t, ts, target: str, ayanamsa_deg: float) -> tuple[float, float]:
    """Sidereal longitude and apparent daily motion for a body."""
    lon_now = _tropical_longitude(t, target)

    t_before = ts.tt_jd(t.tt - _MOTION_DT)
    t_after = ts.tt_jd(t.tt + _MOTION_DT)
    lon_before = _tropical_longitude(t_before, target)
    lon_after = _tropical_longitude(t_after, target)

    # Unwrap across the 0/360 seam before differencing.
    delta = (lon_after - lon_before + 180.0) % 360.0 - 180.0
    speed = delta / (2.0 * _MOTION_DT)

    return ay.to_sidereal(norm360(lon_now), ayanamsa_deg), speed


def compute(
    birth: BirthData,
    system: ay.Ayanamsa = ay.Ayanamsa.LAHIRI,
) -> ChartPositions:
    """Compute lagna and all nine grahas for a birth record."""
    from .ephemeris import get_timescale

    ts = get_timescale()
    t = birth.skyfield_time()
    ayan = ay.compute(t, system)

    grahas: dict[int, GrahaPosition] = {}

    for graha, target in _TARGETS.items():
        sidereal, speed = _sidereal_with_speed(t, ts, target, ayan)
        grahas[graha] = GrahaPosition(
            graha=graha,
            position=resolve(sidereal),
            speed_deg_per_day=speed,
            retrograde=speed < 0.0,
        )

    # Rahu and Ketu: the mean node is always retrograde, and Ketu is exactly
    # 180 degrees from Rahu by definition rather than by separate computation.
    rahu_tropical = mean_lunar_node(t.tt)
    node_speed = (
        mean_lunar_node(t.tt + _MOTION_DT) - mean_lunar_node(t.tt - _MOTION_DT) + 180.0
    ) % 360.0 - 180.0
    node_speed /= 2.0 * _MOTION_DT

    rahu_sidereal = ay.to_sidereal(rahu_tropical, ayan)
    for graha, lon in ((RAHU, rahu_sidereal), (KETU, norm360(rahu_sidereal + 180.0))):
        grahas[graha] = GrahaPosition(
            graha=graha,
            position=resolve(lon),
            speed_deg_per_day=node_speed,
            retrograde=True,
        )

    return ChartPositions(
        birth=birth,
        ayanamsa_system=system,
        ayanamsa_value=ayan,
        lagna=resolve(ascendant(t, birth.latitude, birth.longitude, ayan)),
        grahas=grahas,
    )
