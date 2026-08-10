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

    def carried(self, precision: int) -> "DMS":
        """This value with the sexagesimal carry applied *at display precision*.

        The carry has to happen here, not in :func:`to_dms`, because only the
        caller knows how many decimals will be shown. A value like 59.9987
        seconds is genuinely below 60 and survives any fixed-epsilon guard, but
        rendered at two decimals it becomes the string "60.00" -- a reading that
        cannot exist on a clock face. Real charts hit this about once in 1,100:
        `--time 06:50:25` at Chennai printed a lagna of 16 deg 10' 60.00".
        """
        d, m, s = self.degrees, self.minutes, self.seconds
        if round(s, precision) >= 60.0:
            s = 0.0
            m += 1
        if m >= 60:
            m = 0
            d += 1
        return DMS(self.sign, d, m, s)

    def format(self, precision: int = 2) -> str:
        c = self.carried(precision)
        sign = "-" if c.sign < 0 else ""
        return f"{sign}{c.degrees}°{c.minutes:02d}'{c.seconds:0{3 + precision}.{precision}f}\""


def to_dms(deg: float) -> DMS:
    """Split a decimal degree value into sign/deg/min/sec.

    Applies only the exact carry -- a true 60.0 arising from binary
    representation. Rounding for display is :meth:`DMS.carried`, which needs the
    precision to be meaningful.
    """
    sign = -1 if deg < 0 else 1
    x = abs(deg)
    d = int(x)
    rem = (x - d) * 60.0
    m = int(rem)
    s = (rem - m) * 60.0

    if s >= 60.0:
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
    """Format an absolute longitude as degrees-within-rasi, e.g. 14°02'11.5\".

    A longitude a hair under a rasi boundary must not round up to "30 deg".
    That would read as the *start of the next rasi* while the rasi label beside
    it still says the current one -- a display 30 degrees out. Such a graha is
    at the very end of its rasi, so it is clamped to the largest value the
    chosen precision can represent inside the rasi.
    """
    dms = to_dms(norm360(longitude) % 30.0).carried(precision)
    if dms.degrees >= 30:
        smallest = 10.0 ** -precision
        return DMS(1, 29, 59, 60.0 - smallest).format(precision)
    return dms.format(precision)
