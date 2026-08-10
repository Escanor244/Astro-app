"""Skyfield ephemeris loading.

Licensing note — this is the reason this module exists at all:

Swiss Ephemeris is the usual choice for Jyotish software, but it is dual-licensed
AGPL-3.0 / commercial. Under AGPL section 13, serving it over a network obliges
you to publish the full source of the surrounding application. Self-hosting does
not avoid that. The commercial escape is a Professional Licence at CHF 750.

We therefore build on Skyfield (MIT) plus NASA JPL DE kernels (public domain),
which gives equivalent sub-arcsecond accuracy with no licence encumbrance.
pyswisseph appears only in requirements-dev.txt and is imported only by the
validation tests, which are never distributed.

Kernel choice: DE440s covers 1849-2150 in ~32 MB and spans every realistic birth
date. Set ASTROAPP_EPHEMERIS=de440.bsp (~114 MB, 1550-2650) if you need to cast
historical charts outside that window.
"""

from __future__ import annotations

import functools
import os
import threading
from pathlib import Path

from skyfield.api import Loader

#: Repo-root/data — kernels are gitignored and fetched on first use.
DATA_DIR = Path(
    os.environ.get(
        "ASTROAPP_DATA_DIR",
        Path(__file__).resolve().parents[3].parent / "data",
    )
)

DEFAULT_KERNEL = os.environ.get("ASTROAPP_EPHEMERIS", "de440s.bsp")

# Reentrant: get_timescale() and get_kernel() hold this lock and then call
# get_loader(), which acquires it again. A plain Lock deadlocks here.
_lock = threading.RLock()
_loader: Loader | None = None
_timescale = None
_kernels: dict[str, object] = {}


def get_loader() -> Loader:
    global _loader
    with _lock:
        if _loader is None:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            _loader = Loader(str(DATA_DIR), verbose=False)
        return _loader


def get_timescale():
    """Shared Skyfield timescale.

    Uses the builtin leap-second/Delta-T tables so a first run works offline and
    so results are reproducible rather than drifting with a downloaded file.
    """
    global _timescale
    with _lock:
        if _timescale is None:
            _timescale = get_loader().timescale(builtin=True)
        return _timescale


def get_kernel(name: str | None = None):
    """Load (downloading once if needed) a JPL SPK kernel."""
    name = name or DEFAULT_KERNEL
    with _lock:
        if name not in _kernels:
            _kernels[name] = get_loader()(name)
        return _kernels[name]


def get_earth(kernel_name: str | None = None):
    """The Earth barycentric position object used as our observer origin."""
    return get_kernel(kernel_name)["earth"]


@functools.lru_cache(maxsize=4)
def covered_years(kernel_name: str | None = None) -> tuple[int, int]:
    """First and last year the loaded kernel can actually compute.

    Read from the kernel's own segments rather than hardcoded, because the
    kernel is configurable: DE440s spans 1849-2150 in 32 MB, while
    ``ASTROAPP_EPHEMERIS=de440.bsp`` swaps in 1550-2650. A hardcoded range would
    reject dates the user has deliberately made available, or accept dates that
    then fail deep inside Skyfield.

    The bounds are pulled inward by a year so a date near the edge cannot fail
    once a time zone offset and Delta-T are applied.
    """
    segments = get_kernel(kernel_name).spk.segments
    start_jd = max(s.start_jd for s in segments)
    end_jd = min(s.end_jd for s in segments)

    # JD 2451545.0 is 2000-01-01; 365.25 days a year is close enough to place
    # a boundary year, and the inward margin absorbs the imprecision.
    start_year = int(2000 + (start_jd - 2451545.0) / 365.25) + 1
    end_year = int(2000 + (end_jd - 2451545.0) / 365.25) - 1
    return start_year, end_year
