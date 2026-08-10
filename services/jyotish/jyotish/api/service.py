"""Turning engine objects into API responses, with caching.

Kept separate from the routes so the mapping is testable without HTTP, and so
the caching policy sits in one obvious place.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from ..charts import vargas
from ..core import ayanamsa as ay
from ..core import places as places_db
from ..core import positions as pos
from ..core.angles import format_dms, format_zodiacal
from ..core.birthdata import BirthData, format_time_12h, parse_time
from ..core.zodiac import (
    GRAHA_SANSKRIT,
    GRAHAS,
    MOON,
    NAKSHATRAS,
    RASIS,
    Term,
    ZodiacPosition,
)
from ..dasha import vimshottari as vd
from . import models

#: Bumped whenever a change alters computed output. It is returned with every
#: chart and forms part of the cache key, so a correctness fix can never be
#: masked by a stale cached result -- the failure mode the pre-UI audit was run
#: to prevent.
ENGINE_VERSION = "2.0"

#: Charts are a pure function of (instant, place, ayanamsa), so they cache
#: perfectly and forever. Sized for a single-user desktop session; a
#: multi-worker deployment would move this to Redis rather than grow it.
_CACHE_SIZE = 512


def term(t: Term) -> models.TermOut:
    return models.TermOut(
        en=t.en, ta=t.ta, ta_latin=t.ta_latin,
        en_short=t.short("en"), ta_short=t.short("ta"),
    )


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
        # place_name is carried rather than looked up. A saved record supplies
        # the place it resolved to at save time, so opening it does not depend
        # on the place index still holding that id -- and the exported sheet
        # still names the birth place rather than showing bare coordinates.
        birth = BirthData(
            when=when, latitude=req.latitude, longitude=req.longitude,
            timezone_name=req.timezone, fold=req.fold, name=req.name,
            place_name=req.place_name or None,
        )
    else:
        raise ValueError("Provide either geonameid, or both latitude and longitude.")

    return birth, (hour, minute, second)


def time_warning_for(birth: BirthData) -> tuple[str | None, str | None]:
    """The daylight-saving caveats, and which kind they are.

    An hour of ambiguity is roughly 15 degrees of ascendant -- frequently a
    different rasi -- so this is surfaced rather than silently resolved.

    Returns ``(message, kind)`` where kind is ``"ambiguous"`` or
    ``"nonexistent"``. The kind matters to the client: only an *ambiguous* time
    has a second reading to offer. A nonexistent time has exactly one
    interpretation, so a UI that offers to switch it would be inviting the user
    into a choice that does not exist.

    The nonexistent message states the offset that was actually applied rather
    than assuming one. It previously hardcoded "the offset in force before the
    change", which is only true for fold=0 -- under PEP 495 a fold of 1 selects
    the offset *after* the transition, so the prose contradicted the
    ``utc_offset`` printed two rows above it.
    """
    if birth.time_is_nonexistent:
        return (
            f"{birth.when:%H:%M} on {birth.when:%d %b %Y} never occurred in "
            f"{birth.zone.key}: the clocks jumped forward over it. This chart "
            f"uses {format_offset(birth.utc_offset)}. Please check the birth "
            "record -- the recorded time may be off by an hour.",
            "nonexistent",
        )
    if birth.time_is_ambiguous:
        other = birth.alternative
        return (
            f"{birth.when:%H:%M} on {birth.when:%d %b %Y} occurred twice in "
            f"{birth.zone.key}: the clocks went back. This chart uses "
            f"{format_offset(birth.utc_offset)}; the other reading is "
            f"{format_offset(other.utc_offset)}. They give lagnas about 15 "
            "degrees apart, so confirm which applies.",
            "ambiguous",
        )
    return None, None


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

    warning, warning_kind = time_warning_for(birth)

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
        time_warning=warning,
        time_warning_kind=warning_kind,
        engine_version=ENGINE_VERSION,
    )


# --- dasha -------------------------------------------------------------------


def _local_iso(moment: datetime, zone: ZoneInfo) -> str:
    """A naive-UTC instant as local wall-clock time at the birth place.

    Dasha tables are read as dates, and a date is only meaningful in a zone. The
    birth place's zone is the conventional one -- it is what a printed jathagam
    uses -- even when the person now lives elsewhere.
    """
    return (
        moment.replace(tzinfo=timezone.utc).astimezone(zone).replace(tzinfo=None)
    ).isoformat(timespec="seconds")


def _parse_at(text: str | None, zone: ZoneInfo) -> datetime:
    """The 'what is running' moment, given as local time at the birth place."""
    if not text or not text.strip():
        local = datetime.now(zone)
    else:
        try:
            local = datetime.fromisoformat(text.strip())
        except ValueError:
            raise ValueError(
                f"Cannot read `at` value {text!r}. Use YYYY-MM-DD, or a full "
                "ISO datetime such as 2026-08-10T14:30:00."
            ) from None
        if local.tzinfo is None:
            local = local.replace(tzinfo=zone)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def period_out(period: vd.Period, zone: ZoneInfo, at: datetime) -> models.PeriodOut:
    return models.PeriodOut(
        lords=list(period.lords),
        lord_names=[term(GRAHAS[g]) for g in period.lords],
        level=period.level,
        level_name=term(period.level_name),
        start=_local_iso(period.start, zone),
        end=_local_iso(period.end, zone),
        start_utc=period.start.isoformat(timespec="seconds"),
        end_utc=period.end.isoformat(timespec="seconds"),
        days=period.days,
        running=period.contains(at),
        has_children=period.level < vd.MAX_LEVEL,
    )


def compute_dasha(req: models.DashaRequest) -> models.DashaResponse:
    """One level of the dasha tree, plus the chain running at a moment.

    Raises ValueError on invalid input, including a path that names a lord which
    is not among a node's children -- which can only happen if a client
    hand-builds one, since every path it is given comes from this endpoint.
    """
    birth, _ = build_birth(req)
    system = ay.Ayanamsa(req.ayanamsa)
    zone = birth.zone

    chart = _compute_cached(
        birth.utc.replace(tzinfo=None).isoformat(),
        birth.latitude, birth.longitude, system, ENGINE_VERSION,
    )
    moon = chart.grahas[MOON].longitude
    birth_utc = birth.utc.replace(tzinfo=None)
    at = _parse_at(req.at, zone)

    balance = vd.balance_at_birth(moon, year_length=req.year_length)

    # One cycle at the top level: 120 years from a start that precedes the
    # birth, so it spans any lifetime. `chain_at` generates two cycles
    # internally, so a lookup past that horizon still resolves even though the
    # table does not list it.
    periods = vd.mahadashas(birth_utc, moon, year_length=req.year_length)[:9]
    parent: vd.Period | None = None

    for lord in req.path:
        match = next((p for p in periods if p.lord == lord), None)
        if match is None:
            raise ValueError(
                f"{GRAHAS[lord].en} is not one of the sub-periods at that level. "
                f"Available: {', '.join(GRAHAS[p.lord].en for p in periods)}."
            )
        parent = match
        periods = vd.children(match)
        if not periods:
            raise ValueError(
                f"The dasha tree stops at {vd.MAX_LEVEL} levels; "
                f"{GRAHAS[lord].en} is already at the deepest one."
            )

    return models.DashaResponse(
        balance=models.DashaBalanceOut(
            lord=balance.lord,
            lord_name=term(GRAHAS[balance.lord]),
            nakshatra=balance.nakshatra,
            nakshatra_name=term(NAKSHATRAS[balance.nakshatra]),
            remaining_fraction=balance.remaining_fraction,
            years=balance.years,
            months=balance.months,
            days=balance.days,
            formatted=balance.format("en"),
            formatted_ta=balance.format("ta"),
        ),
        year_length=req.year_length,
        year_days=vd.year_days(req.year_length),
        path=list(req.path),
        parent=period_out(parent, zone, at) if parent else None,
        periods=[period_out(p, zone, at) for p in periods],
        running=[
            period_out(p, zone, at)
            for p in vd.chain_at(
                birth_utc, moon, at, year_length=req.year_length
            )
        ],
        at=_local_iso(at, zone),
        moon_longitude=moon,
        timezone=zone.key,
        engine_version=ENGINE_VERSION,
    )


# --- panchangam --------------------------------------------------------------


def _limb_out(limb, zone: ZoneInfo) -> models.LimbOut:
    return models.LimbOut(
        index=limb.index,
        name=term(limb.name),
        start=_local_iso(limb.start, zone),
        end=_local_iso(limb.end, zone),
        start_utc=limb.start.isoformat(timespec="seconds"),
        end_utc=limb.end.isoformat(timespec="seconds"),
        elapsed=limb.elapsed,
    )


def _window_out(window, zone: ZoneInfo) -> models.WindowOut | None:
    if window is None:
        return None
    return models.WindowOut(
        name=term(window.name),
        start=_local_iso(window.start, zone),
        end=_local_iso(window.end, zone),
        auspicious=window.auspicious,
    )


@lru_cache(maxsize=_CACHE_SIZE)
def _panchangam_cached(
    utc_iso: str, latitude: float, longitude: float, timezone_name: str,
    system: ay.Ayanamsa, _engine_version: str,
):
    """Cached like charts, and for a stronger reason.

    A panchangam costs a rising/setting search plus eight root-finds, which is
    an order of magnitude more work than a chart. The timezone *is* part of the
    key here, unlike for a chart: sunrise is found for a local calendar day, so
    the same instant at the same coordinates under a different zone genuinely
    gives a different day's windows.
    """
    from ..panchanga import panchangam as pg

    return pg.compute(
        datetime.fromisoformat(utc_iso), latitude, longitude, timezone_name, system
    )


def compute_panchangam(req: models.PanchangamRequest) -> models.PanchangamResponse:
    """The five limbs and the day's windows, for a moment at a place."""
    birth, _ = build_birth(req)
    system = ay.Ayanamsa(req.ayanamsa)
    zone = birth.zone

    p = _panchangam_cached(
        birth.utc.replace(tzinfo=None).isoformat(),
        birth.latitude, birth.longitude, zone.key, system, ENGINE_VERSION,
    )

    def when(moment) -> str | None:
        return None if moment is None else _local_iso(moment, zone)

    return models.PanchangamResponse(
        moment=_local_iso(p.moment, zone),
        timezone=zone.key,
        place_name=birth.place_name,
        latitude=birth.latitude,
        longitude=birth.longitude,
        ayanamsa=req.ayanamsa,
        sunrise=when(p.sun.rising),
        sunset=when(p.sun.setting),
        next_sunrise=when(p.next_sunrise),
        moonrise=when(p.moon.rising),
        moonset=when(p.moon.setting),
        daylight=p.sun.condition,
        vaara=p.vaara,
        vaara_name=term(p.vaara_name),
        tithi=_limb_out(p.tithi, zone),
        paksha=p.paksha,
        paksha_name=term(p.paksha_name),
        nakshatra=_limb_out(p.nakshatra, zone),
        yoga=_limb_out(p.yoga, zone),
        karana=_limb_out(p.karana, zone),
        rahu_kalam=_window_out(p.rahu_kalam, zone),
        yamagandam=_window_out(p.yamagandam, zone),
        kuligai=_window_out(p.kuligai, zone),
        gowri_day=[_window_out(w, zone) for w in p.gowri_day],
        gowri_night=[_window_out(w, zone) for w in p.gowri_night],
        nalla_neram=[_window_out(w, zone) for w in p.nalla_neram],
        tamil_month=p.tamil_month,
        tamil_month_name=term(p.tamil_month_name),
        tamil_day=p.tamil_day,
        tamil_year=p.tamil_year,
        tamil_year_name=term(p.tamil_year_name),
        ayana_name=term(p.ayana_name),
        ritu_name=term(p.ritu_name),
        engine_version=ENGINE_VERSION,
    )


def metadata() -> models.MetaResponse:
    from ..core.ephemeris import covered_years

    first_year, last_year = covered_years()
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
        # Read from the loaded kernel, not hardcoded: the kernel is
        # configurable, and a fixed string would misreport under an
        # ASTROAPP_EPHEMERIS override.
        ephemeris_range=f"{first_year}-{last_year}",
        first_year=first_year,
        last_year=last_year,
    )
