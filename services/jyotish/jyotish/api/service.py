"""Turning engine objects into API responses, with caching.

Kept separate from the routes so the mapping is testable without HTTP, and so
the caching policy sits in one obvious place.
"""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from ..charts import vargas
from ..core import ayanamsa as ay
from ..core import places as places_db
from ..core import positions as pos
from ..core.angles import format_dms, format_zodiacal
from ..core.birthdata import BirthData, format_time_12h, parse_time
from ..core.zodiac import (
    GRAHA_SANSKRIT,
    GRAHAS,
    NAKSHATRAS,
    RASIS,
    Term,
    ZodiacPosition,
)
from . import models

#: Bumped whenever a change alters computed output. It is returned with every
#: chart and forms part of the cache key, so a correctness fix can never be
#: masked by a stale cached result -- the failure mode the pre-UI audit was run
#: to prevent.
ENGINE_VERSION = "1a.1"

#: Charts are a pure function of (instant, place, ayanamsa), so they cache
#: perfectly and forever. Sized for a single-user desktop session; a
#: multi-worker deployment would move this to Redis rather than grow it.
_CACHE_SIZE = 512


def term(t: Term) -> models.TermOut:
    return models.TermOut(en=t.en, ta=t.ta, ta_latin=t.ta_latin)


def zodiac_out(z: ZodiacPosition) -> models.ZodiacOut:
    return models.ZodiacOut(
        longitude=z.longitude,
        formatted=format_zodiacal(z.longitude),
        rasi=z.rasi,
        rasi_name=term(RASIS[z.rasi]),
        degrees_in_rasi=z.degrees_in_rasi,
        nakshatra=z.nakshatra,
        nakshatra_name=term(NAKSHATRAS[z.nakshatra]),
        pada=z.pada,
        nakshatra_lord=z.nakshatra_lord,
        nakshatra_lord_name=term(GRAHAS[z.nakshatra_lord]),
    )


def place_out(place: places_db.Place) -> models.PlaceOut:
    return models.PlaceOut(
        geonameid=place.geonameid,
        name=place.name,
        display_name=place.display_name,
        admin1=place.admin1,
        country_code=place.country_code,
        country_name=place.country_name,
        latitude=place.latitude,
        longitude=place.longitude,
        timezone=place.timezone,
        population=place.population,
    )


def format_offset(delta) -> str:
    """'UTC+05:30', including historical offsets that are not whole hours."""
    total = int(delta.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, m, s = total // 3600, (total % 3600) // 60, total % 60
    return f"UTC{sign}{h:02d}:{m:02d}" + (f":{s:02d}" if s else "")


def build_birth(req: models.ChartRequest) -> tuple[BirthData, tuple[int, int, int]]:
    """Resolve a request into a BirthData, raising ValueError on bad input."""
    hour, minute, second = parse_time(req.time)
    when = datetime(req.date.year, req.date.month, req.date.day, hour, minute, second)

    if req.geonameid is not None:
        place = places_db.get(req.geonameid)
        if place is None:
            raise ValueError(f"No place with geonameid {req.geonameid}.")
        birth = BirthData.from_place(
            place, when, timezone_name=req.timezone, fold=req.fold
        )
    elif req.latitude is not None and req.longitude is not None:
        birth = BirthData(
            when=when, latitude=req.latitude, longitude=req.longitude,
            timezone_name=req.timezone, fold=req.fold, name=req.name,
        )
    else:
        raise ValueError("Provide either geonameid, or both latitude and longitude.")

    return birth, (hour, minute, second)


def time_warning_for(birth: BirthData) -> str | None:
    """The daylight-saving caveats, in language a user can act on.

    An hour of ambiguity is roughly 15 degrees of ascendant -- frequently a
    different rasi -- so this is surfaced rather than silently resolved.
    """
    if birth.time_is_nonexistent:
        return (
            f"{birth.when:%H:%M} on {birth.when:%d %b %Y} never occurred in "
            f"{birth.zone.key}: the clocks jumped forward over it. The chart "
            "assumes the offset in force before the change. Please check the "
            "birth record."
        )
    if birth.time_is_ambiguous:
        other = birth.alternative
        return (
            f"{birth.when:%H:%M} on {birth.when:%d %b %Y} occurred twice in "
            f"{birth.zone.key}: the clocks went back. This chart uses "
            f"{format_offset(birth.utc_offset)}; the other reading is "
            f"{format_offset(other.utc_offset)}. They give lagnas about 15 "
            "degrees apart, so confirm which applies."
        )
    return None


@lru_cache(maxsize=_CACHE_SIZE)
def _compute_cached(
    utc_iso: str, latitude: float, longitude: float, system: ay.Ayanamsa,
    _engine_version: str,
):
    """The expensive part, keyed only by what actually affects the result.

    Note what is *not* in the key: the place name, the requested vargas, the
    display language. Two users entering the same instant at the same
    coordinates get one computation.
    """
    when = datetime.fromisoformat(utc_iso)
    birth = BirthData(
        when=when.replace(tzinfo=None), latitude=latitude, longitude=longitude,
        timezone_name="UTC",
    )
    return pos.compute(birth, system)


def compute_chart(req: models.ChartRequest) -> models.ChartResponse:
    """Full chart for a request. Raises ValueError on invalid input."""
    birth, (hour, minute, second) = build_birth(req)
    system = ay.Ayanamsa(req.ayanamsa)

    codes = [c.strip().upper() for c in req.vargas if c.strip()] or ["D1"]
    unknown = [c for c in codes if c not in vargas.VARGAS]
    if unknown:
        raise ValueError(
            f"Unknown varga {', '.join(unknown)}. "
            f"Known: {', '.join(vargas.VARGA_ORDER)}."
        )

    chart = _compute_cached(
        birth.utc.replace(tzinfo=None).isoformat(),
        birth.latitude, birth.longitude, system, ENGINE_VERSION,
    )

    grahas = [
        models.GrahaOut(
            graha=gi,
            name=term(GRAHAS[gi]),
            sanskrit=GRAHA_SANSKRIT[gi],
            position=zodiac_out(chart.grahas[gi].position),
            house=chart.house_of(gi),
            retrograde=chart.grahas[gi].retrograde,
            speed_deg_per_day=chart.grahas[gi].speed_deg_per_day,
        )
        for gi in range(9)
    ]

    charts = []
    for code in codes:
        vc = vargas.compute(chart, code)
        charts.append(models.VargaOut(
            code=vc.varga.code,
            divisions=vc.varga.divisions,
            name=term(vc.varga.name),
            significance=vc.varga.significance,
            lagna_rasi=vc.lagna_rasi,
            graha_rasis={str(k): v for k, v in vc.graha_rasis.items()},
            retrogrades=sorted(vc.retrogrades),
        ))

    return models.ChartResponse(
        birth=models.BirthOut(
            local_datetime=birth.when.isoformat(),
            time_12h=format_time_12h(hour, minute, second),
            utc=birth.utc.replace(tzinfo=None).isoformat(),
            place_name=birth.place_name,
            latitude=birth.latitude,
            longitude=birth.longitude,
            timezone=birth.zone.key,
            utc_offset=format_offset(birth.utc_offset),
            offset_note=birth.offset_note,
        ),
        ayanamsa=req.ayanamsa,
        ayanamsa_value=chart.ayanamsa_value,
        ayanamsa_formatted=format_dms(chart.ayanamsa_value),
        lagna=zodiac_out(chart.lagna),
        grahas=grahas,
        charts=charts,
        time_warning=time_warning_for(birth),
        engine_version=ENGINE_VERSION,
    )


def metadata() -> models.MetaResponse:
    return models.MetaResponse(
        engine_version=ENGINE_VERSION,
        ayanamsas=models.all_ayanamsas(),
        default_ayanamsa="lahiri",
        vargas=[
            models.VargaMeta(
                code=v.code, divisions=v.divisions,
                name=term(v.name), significance=v.significance,
            )
            for v in (vargas.VARGAS[c] for c in vargas.VARGA_ORDER)
        ],
        rasis=[term(r) for r in RASIS],
        nakshatras=[term(n) for n in NAKSHATRAS],
        grahas=[term(g) for g in GRAHAS],
        ephemeris_range="1849-2150 (DE440s)",
    )
