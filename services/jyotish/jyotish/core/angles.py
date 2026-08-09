"""Angle helpers.

Everything in this engine is degrees, normalised to [0, 360). Jyotish is full of
places where an off-by-360 or a sign slip silently moves a graha into the wrong
rasi, so normalisation lives in one place and is used everywhere.
"""

from __future__ import annotations

import math
from typing import NamedTuple

ARCSEC = 1.0 / 3600.0


def norm360(deg: float) -> float:
    """Normalise an angle to [0, 360)."""
    r = math.fmod(deg, 360.0)
    return r + 360.0 if r < 0 else r


def norm180(deg: float) -> float:
    """Normalise an angle to [-180, 180)."""
    return norm360(deg + 180.0) - 180.0


def sep360(a: float, b: float) -> float:
    """Smallest absolute separation between two angles, in degrees.

    Used by the validation harness: comparing 359.9999 against 0.0001 must
    report 0.0002 degrees, not 359.9998.
    """
    return abs(norm180(a - b))


class DMS(NamedTuple):
    """A degree/minute/second breakdown, with sign carried separately."""

    sign: int
    degrees: int
    minutes: int
    seconds: float

    def format(self, precision: int = 2) -> str:
        s = "-" if self.sign < 0 else ""
        return f"{s}{self.degrees}°{self.minutes:02d}'{self.seconds:0{3 + precision}.{precision}f}\""


def to_dms(deg: float) -> DMS:
    """Split a decimal degree value into sign/deg/min/sec.

    Carries the rounding upward so 29.9999999 never formats as 29 60' 00".
    """
    sign = -1 if deg < 0 else 1
    x = abs(deg)
    d = int(x)
    rem = (x - d) * 60.0
    m = int(rem)
    s = (rem - m) * 60.0

    # Guard the boundary: floating point can leave s at 59.99999999.
    if round(s, 6) >= 60.0:
        s = 0.0
        m += 1
    if m >= 60:
        m = 0
        d += 1

    return DMS(sign, d, m, s)


def format_dms(deg: float, precision: int = 2) -> str:
    """Format a decimal degree as 12°34'56.78"."""
    return to_dms(deg).format(precision)


def format_zodiacal(longitude: float, precision: int = 2) -> str:
    """Format an absolute longitude as degrees-within-rasi, e.g. 14°02'11.5\"."""
    return format_dms(norm360(longitude) % 30.0, precision)
