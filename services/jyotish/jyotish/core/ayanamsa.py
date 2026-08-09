"""Ayanamsa — the tropical-to-sidereal offset.

This is the single most consequential number in the engine. Sidereal longitude
is tropical longitude minus ayanamsa, so an error here moves *every* graha by
the same amount. An error of only 0.3 degrees will push a graha across a
nakshatra pada boundary, and pada is the first thing a practising astrologer
checks. It is also why KP must be computed with KP ayanamsa: using Lahiri
instead shifts every cusp by ~5'49" and silently corrupts sub-lord results.

Two families are implemented, because they are genuinely different in kind:

1. Fixed-epoch systems (Lahiri, KP, Raman). Each fixes the ayanamsa value at
   J1900.0 and accumulates general precession in longitude from there:

       ayanamsa(t) = ayan_t0 + [p_A(t) - p_A(t0)]

   The three share one precession model and differ only in ayan_t0, which is
   verifiable: their J1900 -> 2026 increments are identical to 0.01 arcsec.

2. True Chitrapaksha, which is *defined dynamically* as the tropical longitude
   of Spica (Chitra) minus 180 degrees. It cannot be expressed as a fixed
   offset because Spica has proper motion, which is exactly why its increment
   over the same span differs from the fixed-epoch family by ~6 arcsec.

The ayan_t0 constants are the published defining values of each system,
cross-checked against Swiss Ephemeris 2.10.03 in tests/validation/. Numeric
constants of a published standard are facts, not authored code.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from skyfield.api import Star
from skyfield.nutationlib import iau2000b

from .angles import norm360
from .ephemeris import get_earth, get_timescale

#: J1900.0 — the reference epoch for the fixed-epoch ayanamsa family.
T0_JD = 2415020.0

#: Julian days per Julian century.
JULIAN_CENTURY = 36525.0


class Ayanamsa(str, Enum):
    """Supported ayanamsa systems."""

    #: India's official standard (Calendar Reform Committee, 1955). The default
    #: for Parashari work and for everything a consumer sees.
    LAHIRI = "lahiri"

    #: Dynamic Spica-based definition. Diverges from Lahiri by ~1 arcmin.
    TRUE_CHITRAPAKSHA = "true_chitrapaksha"

    #: K.S. Krishnamurti's value. Mandatory for KP; wrong results without it.
    KP = "kp"

    #: B.V. Raman's value.
    RAMAN = "raman"


#: Defining ayanamsa value at J1900.0, in degrees.
#: Sources: Lahiri 22d27'37.84", KP 22d21'49.17", Raman 21d00'51.16".
_AYAN_T0: dict[Ayanamsa, float] = {
    Ayanamsa.LAHIRI: 22.0 + 27.0 / 60.0 + 37.84 / 3600.0,
    Ayanamsa.KP: 22.0 + 21.0 / 60.0 + 49.17 / 3600.0,
    Ayanamsa.RAMAN: 21.0 + 0.0 / 60.0 + 51.16 / 3600.0,
}

#: Spica (Alpha Virginis / Chitra), Hipparcos HIP 65474.
#:
#: These are the published Hipparcos astrometric parameters at epoch J1991.25.
#: We hardcode them rather than calling skyfield.data.hipparcos, which downloads
#: a ~50 MB catalogue to read a single row, and whose upstream host currently
#: presents an untrusted TLS chain. One star, five numbers, no network.
_SPICA_HIP = 65474
_SPICA_RA_DEG = 201.29824970
_SPICA_DEC_DEG = -11.16131948
_SPICA_PARALLAX_MAS = 12.44
_SPICA_PM_RA_MAS_PER_YR = -42.50
_SPICA_PM_DEC_MAS_PER_YR = -31.73
_SPICA_RADIAL_KM_PER_S = 1.0
#: Hipparcos catalogue epoch J1991.25 as a Julian date (TT).
_HIPPARCOS_EPOCH_JD = 2448349.0625


def precession_longitude(jd_tt: float) -> float:
    """General precession in longitude p_A, in arcseconds, relative to J2000.

    IAU 2006 (Capitaine et al. 2003) polynomial. T is Julian centuries TT from
    J2000.0. Negative before J2000.
    """
    t = (jd_tt - 2451545.0) / JULIAN_CENTURY
    return (
        5028.796195 * t
        + 1.1054348 * t**2
        + 0.00007964 * t**3
        - 0.000023857 * t**4
        - 0.0000000383 * t**5
    )


@lru_cache(maxsize=1)
def _spica() -> Star:
    """Spica as a Skyfield Star, carrying its proper motion."""
    return Star(
        ra_hours=_SPICA_RA_DEG / 15.0,
        dec_degrees=_SPICA_DEC_DEG,
        ra_mas_per_year=_SPICA_PM_RA_MAS_PER_YR,
        dec_mas_per_year=_SPICA_PM_DEC_MAS_PER_YR,
        parallax_mas=_SPICA_PARALLAX_MAS,
        radial_km_per_s=_SPICA_RADIAL_KM_PER_S,
        epoch=get_timescale().tt_jd(_HIPPARCOS_EPOCH_JD),
    )


def _true_chitrapaksha(t) -> float:
    """Tropical longitude of Spica minus 180 degrees.

    Two frame subtleties, both of which are silent errors if missed:

    1. 'Tropical' means referred to the equinox *of date*, so the ecliptic frame
       must be epoch='date'. The default J2000 frame would be wrong by the whole
       accumulated precession since 2000.
    2. The reference is the *mean* equinox of date, not the true one. Skyfield's
       ``.apparent()`` includes nutation, so we subtract nutation in longitude
       back out. Skipping this leaves a +/-17 arcsec oscillation in the result --
       exactly the amplitude of nutation in longitude, and the tell-tale
       signature that the wrong equinox is in use.
    """
    apparent = get_earth().at(t).observe(_spica()).apparent()
    _, lon, _ = apparent.ecliptic_latlon(epoch="date")

    # iau2000b returns (dpsi, deps) in units of 0.1 microarcsecond.
    dpsi_arcsec = iau2000b(t.tt)[0] / 1e7

    return norm360(lon.degrees - dpsi_arcsec / 3600.0 - 180.0)


def compute(t, system: Ayanamsa = Ayanamsa.LAHIRI) -> float:
    """Ayanamsa in degrees at Skyfield time ``t``.

    Args:
        t: a Skyfield Time.
        system: which ayanamsa definition to use.
    """
    if system is Ayanamsa.TRUE_CHITRAPAKSHA:
        return _true_chitrapaksha(t)

    try:
        ayan_t0 = _AYAN_T0[system]
    except KeyError:  # pragma: no cover - guarded by the enum
        raise ValueError(f"Unsupported ayanamsa system: {system!r}") from None

    delta_arcsec = precession_longitude(t.tt) - precession_longitude(T0_JD)
    return ayan_t0 + delta_arcsec / 3600.0


def to_sidereal(tropical_longitude: float, ayanamsa_degrees: float) -> float:
    """Convert a tropical longitude to sidereal."""
    return norm360(tropical_longitude - ayanamsa_degrees)


def to_tropical(sidereal_longitude: float, ayanamsa_degrees: float) -> float:
    """Convert a sidereal longitude back to tropical."""
    return norm360(sidereal_longitude + ayanamsa_degrees)
