"""The Tamil panchangam -- the five limbs and the day's auspicious windows.

*Panchanga* means "five limbs": **tithi** (lunar day), **vaara** (weekday),
**nakshatra** (the Moon's star), **yoga** and **karana**. Everything else a
Tamil daily calendar prints -- rahu kalam, yamagandam, kuligai, gowri
panchangam, nalla neram -- is built on top of those five plus sunrise and
sunset.

Three things drive the design here.

**Nothing is measured from midnight.** The Jyotish day runs sunrise to sunrise,
so the weekday that governs rahu kalam changes at sunrise, not at 00:00. A birth
at 03:00 on a Tuesday happens on *Monday's* vaara. Consumer apps get this wrong
constantly, and it silently shifts every window in this module.

**Each limb is an angle, not a lookup.** A tithi is 12 degrees of elongation
between Moon and Sun; a yoga is 13 degrees 20 minutes of their *sum*; a karana is
half a tithi. So the index is arithmetic, and the moment a limb ends is a root of
the same expression -- which is why this module carries a small solver rather
than a table of durations. Tamil almanacs print "நட்சத்திரம் ரோகிணி வரை 14:23",
and that ending time is the part practitioners actually use.

**Ayanamsa cancels for two of them and not for the others.** Tithi and karana are
*differences* of two longitudes, so the ayanamsa subtracts out and the answer is
identical in any system. Yoga is a *sum*, so it shifts by twice the ayanamsa, and
nakshatra is a single sidereal longitude. Getting this backwards produces a
panchangam that looks right in one ayanamsa and is wrong in every other.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as DateType
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..core import ayanamsa as ay
from ..core.angles import norm180, norm360
from ..core.birthdata import civil_to_time, time_to_civil
from ..core.ephemeris import get_timescale
from ..core.positions import sidereal_longitude
from ..core.zodiac import MOON, NAKSHATRA_SPAN, NAKSHATRAS, RASI_SPAN, SUN, Term
from . import lexicon as lex
from .daylight import (
    RiseSet,
    local_midnight_utc,
    moon_rise_set,
    sun_rise_set,
    vaara_of,
)

UTC = timezone.utc

TITHI_SPAN = 12.0
KARANA_SPAN = 6.0
YOGA_SPAN = NAKSHATRA_SPAN  # 13 deg 20 min, the same division as a nakshatra

#: Mean daily rates, degrees per day. Only used to seed the solver, so they need
#: to be roughly right rather than exact -- the solver measures the local rate
#: itself and these are the fallback when that measurement is unusable.
_RATE_ELONGATION = 12.19
_RATE_MOON = 13.176
_RATE_SUM = 14.16

_SOLVER_TOLERANCE_DEG = 1e-9  # about 4 microarcseconds; far below any print
_SOLVER_MAX_STEPS = 8


# --- the solver --------------------------------------------------------------


def _crossing(value_at, target: float, t_jd: float, rate_guess: float) -> float:
    """TT Julian date at which a rising angle crosses ``target``.

    Newton's method on a function that is very nearly linear over the day or so
    it has to travel, with the derivative re-measured at every step rather than
    assumed. Re-measuring costs one extra evaluation per iteration and buys
    correctness for the Moon, whose speed swings from 11.8 to 15.4 degrees a day
    -- a fixed mean rate leaves the last iteration short by a second or two,
    which is enough to print the wrong minute.

    ``value_at`` must be increasing and is compared modulo 360, so this works
    across the zero seam without special-casing it. The caller guarantees the
    start is within one span of the target, which keeps the wrapped difference
    unambiguous.
    """
    t = t_jd
    for _ in range(_SOLVER_MAX_STEPS):
        here = value_at(t)
        diff = norm180(target - here)
        if abs(diff) < _SOLVER_TOLERANCE_DEG:
            return t

        h = 0.05
        rate = norm180(value_at(t + h) - here) / h
        if rate <= 0.0:
            rate = rate_guess

        # A step longer than a few days means the seed was wrong, not that the
        # body moved; clamp rather than fly off and return a plausible-looking
        # date from somewhere else entirely.
        t += max(-40.0, min(40.0, diff / rate))
    return t


@dataclass(frozen=True)
class Limb:
    """One of the five limbs: which one is running, and its window.

    ``start`` and ``end`` are naive civil UTC. ``end`` is what a Tamil almanac
    prints -- "Rohini until 14:23" -- and is the reason this module solves rather
    than merely divides.
    """

    index: int
    name: Term
    start: datetime
    end: datetime
    #: How far through the limb the moment sits, in [0, 1).
    elapsed: float

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


def _limb(value: float, span: float, count: int, value_at, t_jd: float,
          rate: float, names: tuple[Term, ...], index: int | None = None) -> Limb:
    """Resolve a running angle into the limb it occupies plus its boundaries."""
    x = value / span
    idx = int(x) % count if index is None else index
    elapsed = x - int(x)

    start_jd = _crossing(value_at, (int(x)) * span % 360.0, t_jd, rate)
    end_jd = _crossing(value_at, (int(x) + 1) * span % 360.0, t_jd, rate)

    ts = get_timescale()
    return Limb(
        index=idx,
        name=names[idx],
        start=time_to_civil(ts.tt_jd(start_jd)),
        end=time_to_civil(ts.tt_jd(end_jd)),
        elapsed=elapsed,
    )


# --- windows -----------------------------------------------------------------


@dataclass(frozen=True)
class Window:
    """A named span of the day, such as rahu kalam or a gowri period."""

    name: Term
    start: datetime
    end: datetime
    #: True for a period to seek out, False to avoid, None where the tradition
    #: does not classify it.
    auspicious: bool | None = None


def _eighths(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Split an interval into eight equal parts.

    Eight is not arbitrary: rahu kalam, yamagandam, kuligai and the gowri
    periods are all defined as one-eighth of the day, which is where the
    familiar 1.5-hour figure comes from -- it is only 1.5 hours on a day with
    exactly twelve hours of light. In Chennai the daylight eighth runs from about
    85 to 97 minutes across the year, and in London from about 59 to 125.
    """
    span = (end - start) / 8
    parts = [(start + span * i, start + span * (i + 1)) for i in range(8)]
    # Snap the last boundary. Eight rounded multiples of a rounded eighth do not
    # have to add back up to the whole, and they did not: the final window ran
    # three microseconds past sunset. Invisible on a clock, but it means the
    # windows do not tile the day, and every later "does this instant fall in
    # rahu kalam" question then has a gap it can fall into.
    parts[-1] = (parts[-1][0], end)
    return parts


def _kalam(name: Term, parts, index: int, auspicious: bool | None = False) -> Window:
    start, end = parts[index]
    return Window(name=name, start=start, end=end, auspicious=auspicious)


def _gowri(sequence: tuple[int, ...], parts) -> tuple[Window, ...]:
    return tuple(
        Window(
            name=lex.GOWRI[g],
            start=start,
            end=end,
            auspicious=g in lex.AUSPICIOUS_GOWRI,
        )
        for g, (start, end) in zip(sequence, parts)
    )


# --- the Tamil calendar ------------------------------------------------------


def _sun_longitude_at(jd: float, system: ay.Ayanamsa) -> float:
    t = get_timescale().tt_jd(jd)
    return sidereal_longitude(t, SUN, ay.compute(t, system))


def solar_month_first_day(
    sankranti_utc: datetime,
    latitude: float,
    longitude: float,
    zone: ZoneInfo,
) -> DateType:
    """The local date that is day 1 of the month a sankranti opens.

    A Tamil month begins when the Sun enters a sidereal rasi -- Chithirai at
    Mesha, Vaikasi at Rishabam and so on -- so the month itself is just the Sun's
    rasi. What takes work is the *date*, because a sankranti happens at an
    arbitrary instant and some day has to be numbered 1.

    Tamil Nadu uses the **sunset rule**: if the sankranti falls before sunset,
    that same day is the first of the month; if after, the next day is. This is
    one of the places regional almanacs genuinely diverge -- Kerala switches on
    aparahna (roughly mid-afternoon) and Bengal at midnight -- so a Tamil almanac
    and a Malayalam one can print different dates for the same instant and both
    be correct for their own tradition.
    """
    local_sankranti = sankranti_utc.replace(tzinfo=UTC).astimezone(zone)
    first = local_sankranti.date()

    sunset = sun_rise_set(
        latitude, longitude, local_midnight_utc(first, zone)
    ).setting
    if sunset is not None:
        if local_sankranti > sunset.replace(tzinfo=UTC).astimezone(zone):
            first = first + timedelta(days=1)

    return first


def ritu_of(month: int) -> int:
    """The saura season for a Tamil solar month. 0 = Vasanta.

    Offset by one from the obvious ``month // 2``, and deliberately so. The
    Surya-Siddhanta saura ritu that computed Tamil panchangams print pairs
    **Meena with Mesha** for Vasanta, not Mesha with Rishaba -- so Panguni and
    Chithirai are spring together, and every season straddles a year boundary in
    the same way.

    This is a real disagreement rather than a subtlety: the classical
    Tolkappiyam paruvakkaalam of Tamil literature runs a month later, and a
    panchangam that used it would print a season name one month out all year
    while looking entirely plausible.
    """
    return ((month + 1) // 2) % 6


def ayana_of(month: int) -> int:
    """0 for Uttarayana, 1 for Dakshinayana, on the sidereal definition.

    Uttarayanam begins at Makara sankranti -- Thai 1, about 14 January -- which
    is roughly 24 days after the true tropical solstice. Tamil almanacs print the
    sidereal turn, so using the astronomical solstice would put it in December
    and disagree with all of them.
    """
    return 0 if month >= 9 or month <= 2 else 1


def samvatsara(sankranti_year: int, month_index: int) -> int:
    """Index into the 60-year cycle for a Tamil solar year. 0 = Prabhava.

    The Tamil year turns at Chithirai in mid-April, not on 1 January, so the
    cycle year is named after the *Gregorian year its Chithirai fell in*. A date
    in Thai, Maasi or Panguni -- January to mid-April -- still belongs to the
    year that began the previous April, and those are exactly the months whose
    own sankranti carries the later Gregorian year.

    Taking the month's sankranti year rather than the moment's own year also
    handles Margazhi, which starts in mid-December and runs into January.
    """
    cycle_year = sankranti_year - (1 if month_index >= lex.MONTHS_INTO_NEXT_YEAR else 0)
    return (cycle_year - lex.SAMVATSARA_EPOCH_YEAR) % 60


# --- the panchangam itself ---------------------------------------------------


@dataclass(frozen=True)
class Panchangam:
    """Everything a Tamil daily almanac prints for one moment and place."""

    moment: datetime            # naive civil UTC
    timezone_name: str
    latitude: float
    longitude: float
    ayanamsa: ay.Ayanamsa

    sun: RiseSet
    moon: RiseSet
    next_sunrise: datetime | None

    vaara: int                  # 0 = Sunday, on the sunrise-to-sunrise day
    vaara_name: Term

    tithi: Limb
    paksha: int                 # 0 = Shukla (waxing), 1 = Krishna (waning)
    paksha_name: Term
    nakshatra: Limb
    yoga: Limb
    karana: Limb

    rahu_kalam: Window | None
    yamagandam: Window | None
    kuligai: Window | None
    gowri_day: tuple[Window, ...]
    gowri_night: tuple[Window, ...]
    nalla_neram: tuple[Window, ...]

    tamil_month: int
    tamil_month_name: Term
    tamil_day: int
    tamil_year: int
    tamil_year_name: Term
    ayana: int
    ayana_name: Term
    ritu: int
    ritu_name: Term

    @property
    def has_daylight(self) -> bool:
        return self.sun.has_daylight


def compute(
    moment_utc: datetime,
    latitude: float,
    longitude: float,
    timezone_name: str,
    system: ay.Ayanamsa = ay.Ayanamsa.LAHIRI,
) -> Panchangam:
    """The full panchangam for an instant at a place.

    ``moment_utc`` is naive civil UTC -- the same convention as
    ``BirthData.utc`` -- so a birth chart and its panchangam are computed from
    exactly the same instant on exactly the same time scale.
    """
    zone = ZoneInfo(timezone_name)
    ts = get_timescale()
    t = civil_to_time(moment_utc)
    ayan = ay.compute(t, system)

    sun_lon = sidereal_longitude(t, SUN, ayan)
    moon_lon = sidereal_longitude(t, MOON, ayan)

    def elongation_at(jd: float) -> float:
        """Moon minus Sun. Ayanamsa cancels, so this is frame-independent."""
        tt = ts.tt_jd(jd)
        a = ay.compute(tt, system)
        return norm360(sidereal_longitude(tt, MOON, a) - sidereal_longitude(tt, SUN, a))

    def moon_at(jd: float) -> float:
        tt = ts.tt_jd(jd)
        return sidereal_longitude(tt, MOON, ay.compute(tt, system))

    def sum_at(jd: float) -> float:
        tt = ts.tt_jd(jd)
        a = ay.compute(tt, system)
        return norm360(sidereal_longitude(tt, MOON, a) + sidereal_longitude(tt, SUN, a))

    elongation = norm360(moon_lon - sun_lon)

    tithi = _limb(elongation, TITHI_SPAN, 30, elongation_at, t.tt,
                  _RATE_ELONGATION, lex.TITHIS)
    karana_n = int(elongation / KARANA_SPAN) % 60
    karana = _limb(elongation, KARANA_SPAN, 60, elongation_at, t.tt,
                   _RATE_ELONGATION, lex.KARANAS, index=lex.karana_index(karana_n))
    nakshatra = _limb(moon_lon, NAKSHATRA_SPAN, 27, moon_at, t.tt,
                      _RATE_MOON, NAKSHATRAS)
    yoga = _limb(norm360(moon_lon + sun_lon), YOGA_SPAN, 27, sum_at, t.tt,
                 _RATE_SUM, lex.YOGAS)

    paksha = 0 if tithi.index < 15 else 1

    # --- the day, from sunrise ------------------------------------------------
    local_day = moment_utc.replace(tzinfo=UTC).astimezone(zone).date()
    sun_rs = sun_rise_set(latitude, longitude, local_midnight_utc(local_day, zone))

    # A moment before today's sunrise still belongs to yesterday's Jyotish day,
    # so the windows have to be built on yesterday's sunrise/sunset pair.
    if sun_rs.rising is not None and moment_utc < sun_rs.rising:
        local_day = local_day - timedelta(days=1)
        sun_rs = sun_rise_set(
            latitude, longitude, local_midnight_utc(local_day, zone)
        )

    moon_rs = moon_rise_set(latitude, longitude, local_midnight_utc(local_day, zone))

    next_rs = sun_rise_set(
        latitude, longitude, local_midnight_utc(local_day + timedelta(days=1), zone)
    )
    next_sunrise = next_rs.rising

    # `local_day` has already been walked back if the moment precedes sunrise,
    # so it *is* the Jyotish day, and its weekday is the vaara.
    vaara = vaara_of(local_day)

    rahu = yama = kuligai = None
    gowri_day: tuple[Window, ...] = ()
    gowri_night: tuple[Window, ...] = ()
    nalla: tuple[Window, ...] = ()

    if sun_rs.has_daylight:
        day_parts = _eighths(sun_rs.rising, sun_rs.setting)
        rahu = _kalam(lex.RAHU_KALAM, day_parts, lex.RAHU_PART[vaara])
        yama = _kalam(lex.YAMAGANDAM, day_parts, lex.YAMA_PART[vaara])
        kuligai = _kalam(lex.KULIGAI, day_parts, lex.KULIGAI_PART[vaara])

        gowri_day = _gowri(lex.GOWRI_DAY[vaara], day_parts)
        if next_sunrise is not None:
            gowri_night = _gowri(
                lex.GOWRI_NIGHT[vaara], _eighths(sun_rs.setting, next_sunrise)
            )

        # நல்ல நேரம், as panchangam software defines it: the auspicious gowri
        # windows. A printed Tamil tear-off calendar prints something else under
        # the same heading -- fixed one-hour bands, and demonstrably not a
        # readout of the good gowri slots, since two weekdays in seven land their
        # band on Soram or Rogam. We compute the software definition and say so
        # rather than trying to reproduce a quantised printed table.
        nalla = tuple(w for w in gowri_day + gowri_night if w.auspicious)

    # --- the Tamil calendar ---------------------------------------------------
    #
    # The date is a property of the *day*, not of an instant, and it is settled
    # by the sunset rule rather than by where the Sun happens to be at any
    # particular moment. So: take the Sun's rasi at the end of the Jyotish day,
    # ask when that month's day 1 falls, and step back a rasi if day 1 has not
    # arrived yet.
    #
    # Both directions are needed, and each was a real defect. Reading the rasi at
    # the *moment* gave "Aadi 0" at 03:00 on 17 July 2026 -- the Sun entered
    # Kataka at 23:39 the night before, while the running day was still the last
    # of Aani (correctly, Aani 32; that month genuinely has 32 days in 2026).
    # Reading it at *sunrise* instead lost Thai 1 of 2026 altogether: Makara
    # sankranti fell at 15:07 on 14 January, before sunset, so the sunset rule
    # makes that whole day Thai 1 even though the Sun was still in Dhanus when
    # it dawned.
    calendar_ref = next_sunrise if next_sunrise is not None else moment_utc
    t_cal = civil_to_time(calendar_ref)
    month = int(
        sidereal_longitude(t_cal, SUN, ay.compute(t_cal, system)) * 12.0 / 360.0
    ) % 12

    first = local_day
    for _ in range(2):
        sankranti = time_to_civil(ts.tt_jd(_crossing(
            lambda jd: _sun_longitude_at(jd, system),
            month * RASI_SPAN, t_cal.tt, 0.9856,
        )))
        first = solar_month_first_day(sankranti, latitude, longitude, zone)
        if first <= local_day:
            break
        month = (month - 1) % 12

    tamil_day = (local_day - first).days + 1
    year_index = samvatsara(
        sankranti.replace(tzinfo=UTC).astimezone(zone).year, month
    )

    # Ayana and ritu turn on a *different* rule from the month, and conflating
    # them is wrong on any year where a sankranti falls between sunrise and
    # sunset. They follow the Sun's rasi at the Jyotish day's daybreak, so
    # 14 January 2026 is Thai 1 by the sunset rule while still being
    # Dakshinayanam -- which is exactly what Drik Panchang prints for that day.
    daybreak = sun_rs.rising if sun_rs.rising is not None else moment_utc
    t_break = civil_to_time(daybreak)
    solar_rasi = int(
        sidereal_longitude(t_break, SUN, ay.compute(t_break, system)) * 12.0 / 360.0
    ) % 12

    return Panchangam(
        moment=moment_utc,
        timezone_name=timezone_name,
        latitude=latitude,
        longitude=longitude,
        ayanamsa=system,
        sun=sun_rs,
        moon=moon_rs,
        next_sunrise=next_sunrise,
        vaara=vaara,
        vaara_name=lex.VAARAS[vaara],
        tithi=tithi,
        paksha=paksha,
        paksha_name=lex.PAKSHAS[paksha],
        nakshatra=nakshatra,
        yoga=yoga,
        karana=karana,
        rahu_kalam=rahu,
        yamagandam=yama,
        kuligai=kuligai,
        gowri_day=gowri_day,
        gowri_night=gowri_night,
        nalla_neram=nalla,
        tamil_month=month,
        tamil_month_name=lex.TAMIL_MONTHS[month],
        tamil_day=tamil_day,
        tamil_year=year_index,
        tamil_year_name=lex.SAMVATSARAS[year_index],
        ayana=ayana_of(solar_rasi),
        ayana_name=lex.AYANAS[ayana_of(solar_rasi)],
        ritu=ritu_of(solar_rasi),
        ritu_name=lex.RITUS[ritu_of(solar_rasi)],
    )
