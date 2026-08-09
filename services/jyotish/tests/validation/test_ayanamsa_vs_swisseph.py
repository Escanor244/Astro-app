"""Accuracy gate: our ayanamsa vs the Swiss Ephemeris oracle.

This is the blocking Phase 0 test. Ayanamsa error propagates to *every* graha
equally, so a regression here silently corrupts every chart the app produces.

pyswisseph is a dev-only dependency (AGPL-3.0). It is imported here and nowhere
in the shipped package, so no AGPL obligation attaches to the distributed app.
See jyotish/core/ephemeris.py for the full reasoning.
"""

from __future__ import annotations

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core.ephemeris import get_timescale

swe = pytest.importorskip("swisseph", reason="dev-only accuracy oracle")

#: Our accuracy gate. One arcsecond is ~1/12000 of a nakshatra pada, so this is
#: far tighter than anything that could shift a pada or rasi assignment.
TOLERANCE_ARCSEC = 1.0

#: True Chitrapaksha carries a small constant residual against Swiss Ephemeris
#: (~0.27"), attributable to slightly different assumed astrometric parameters
#: for Spica. Still comfortably inside the gate, but tracked separately so a
#: real regression is not masked by a loose blanket tolerance.
CHITRA_TOLERANCE_ARCSEC = 0.5

SYSTEM_MAP = {
    ay.Ayanamsa.LAHIRI: "SIDM_LAHIRI",
    ay.Ayanamsa.KP: "SIDM_KRISHNAMURTI",
    ay.Ayanamsa.RAMAN: "SIDM_RAMAN",
    ay.Ayanamsa.TRUE_CHITRAPAKSHA: "SIDM_TRUE_CITRA",
}

#: Spread across the DE440s span, including the Indian Calendar Reform epoch
#: (1956) that defines Lahiri, and Independence (1947) as a widely-cast chart.
DATES = [
    (1900, 1, 1), (1947, 8, 15), (1956, 1, 1), (1980, 6, 21),
    (2000, 1, 1), (2025, 1, 1), (2026, 8, 10), (2100, 1, 1),
]


def _swisseph_ayanamsa(system: ay.Ayanamsa, y: int, m: int, d: int) -> float:
    swe.set_sid_mode(getattr(swe, SYSTEM_MAP[system]), 0, 0)
    return swe.get_ayanamsa_ut(swe.julday(y, m, d, 0.0))


@pytest.mark.parametrize("system", list(SYSTEM_MAP))
@pytest.mark.parametrize("date", DATES)
def test_matches_swisseph(system: ay.Ayanamsa, date: tuple[int, int, int]) -> None:
    y, m, d = date
    t = get_timescale().utc(y, m, d, 0, 0, 0)

    ours = ay.compute(t, system)
    theirs = _swisseph_ayanamsa(system, y, m, d)
    diff_arcsec = abs(ours - theirs) * 3600.0

    tolerance = (
        CHITRA_TOLERANCE_ARCSEC
        if system is ay.Ayanamsa.TRUE_CHITRAPAKSHA
        else TOLERANCE_ARCSEC
    )

    assert diff_arcsec < tolerance, (
        f"{system.value} on {y}-{m:02d}-{d:02d}: "
        f"ours={ours:.7f} swisseph={theirs:.7f} diff={diff_arcsec:.4f} arcsec"
    )


def test_kp_differs_from_lahiri_by_expected_offset() -> None:
    """KP must not silently fall back to Lahiri.

    The two differ by ~5'49". If a refactor ever wired KP to the Lahiri constant
    the charts would still look plausible while every sub-lord was wrong, so we
    assert the separation explicitly.
    """
    t = get_timescale().utc(2026, 8, 10)
    delta_arcmin = (ay.compute(t, ay.Ayanamsa.LAHIRI) - ay.compute(t, ay.Ayanamsa.KP)) * 60.0
    assert 5.0 < delta_arcmin < 6.5, f"KP/Lahiri separation {delta_arcmin:.3f}' is wrong"


def test_fixed_epoch_systems_share_one_precession_model() -> None:
    """Lahiri, KP and Raman differ only by their J1900 constant.

    Their increment over any interval must therefore be identical. This pins the
    structural claim the module docstring makes.
    """
    ts = get_timescale()
    t0, t1 = ts.utc(1900, 1, 1), ts.utc(2026, 1, 1)

    increments = [
        ay.compute(t1, s) - ay.compute(t0, s)
        for s in (ay.Ayanamsa.LAHIRI, ay.Ayanamsa.KP, ay.Ayanamsa.RAMAN)
    ]
    spread_arcsec = (max(increments) - min(increments)) * 3600.0
    assert spread_arcsec < 0.01, f"increments diverge by {spread_arcsec:.4f} arcsec"


def test_true_chitrapaksha_is_dynamic() -> None:
    """True Chitrapaksha tracks Spica, so its increment must NOT match the
    fixed-epoch family — Spica's proper motion makes it differ by ~6 arcsec."""
    ts = get_timescale()
    t0, t1 = ts.utc(1900, 1, 1), ts.utc(2026, 1, 1)

    fixed = ay.compute(t1, ay.Ayanamsa.LAHIRI) - ay.compute(t0, ay.Ayanamsa.LAHIRI)
    dynamic = (
        ay.compute(t1, ay.Ayanamsa.TRUE_CHITRAPAKSHA)
        - ay.compute(t0, ay.Ayanamsa.TRUE_CHITRAPAKSHA)
    )
    assert abs(fixed - dynamic) * 3600.0 > 1.0
