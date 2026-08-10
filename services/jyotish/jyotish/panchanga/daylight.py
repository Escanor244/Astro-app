"""Sunrise, sunset, moonrise, moonset -- and why the panchangam needs them.

Almost nothing in a Tamil daily almanac is measured from midnight. The Jyotish
day begins at **sunrise** (சூரிய உதயம்), the weekday changes there rather than
at 00:00, and rahu kalam, yamagandam, kuligai and the gowri periods are all
fractions of the interval between sunrise and sunset. Get sunrise wrong by four
minutes and every one of those windows moves by half a minute; get the *day*
wrong -- which happens for any birth between midnight and sunrise -- and the
whole set is computed for the wrong weekday.

Horizon convention. Indian almanacs define sunrise as the moment the Sun's
**upper limb** first appears on the visible horizon, which is the same
convention the US Naval Observatory publishes: 34 arcminutes for atmospheric
refraction plus 16 arcminutes of solar semidiameter, so the Sun's *centre* is
50 arcminutes (0.8333 degrees) below the geometric horizon. That is exactly what
Skyfield's default horizon function supplies for the Sun, so we let Skyfield
build it rather than passing a constant of our own.

The Moon is not the same problem and must not be given the same constant. Its
semidiameter varies by about a tenth of a degree between perigee and apogee, and
its horizontal parallax -- nearly a degree -- works in the *opposite* direction
to the Sun's. Skyfield's ``build_horizon_function`` handles both from the actual
distance at each instant, which is why the Moon is passed through the same code
path with no special casing here.

Sea level, deliberately. Elevation would raise the horizon and move sunrise
earlier by roughly a minute per 500 m, but Indian almanacs are published for a
place, not for an altitude, so applying it would make us disagree with every
printed panchangam for the same town. ``BirthData.altitude_m`` stays available
for anyone who wants the other answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as DateType
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from skyfield import almanac
from skyfield.api import wgs84

from ..core.birthdata import civil_to_time, time_to_civil
from ..core.ephemeris import get_earth, get_kernel, get_timescale


@dataclass(frozen=True)
class RiseSet:
    """A rising and setting pair, in UTC, plus what happened if there wasn't one.

    ``rising`` and ``setting`` are ``None`` on days when the body never crosses
    the horizon. That is not an error and it is not rare enough to ignore: north
    of the Arctic Circle it is most of the winter, and the Tamil diaspora
    includes Norway, Sweden and Finland. Every consumer of this module has to
    decide what it means -- rahu kalam has no definition without a daylight
    interval -- so the absence is modelled explicitly rather than papered over
    with a fabricated 06:00.
    """

    rising: datetime | None
    setting: datetime | None
    #: "normal", "always_up" (midnight sun) or "always_down" (polar night).
    condition: str

    @property
    def has_daylight(self) -> bool:
        return self.rising is not None and self.setting is not None

    @property
    def day_length(self) -> timedelta | None:
        if not self.has_daylight:
            return None
        return self.setting - self.rising


def _observer(latitude: float, longitude: float):
    return get_earth() + wgs84.latlon(latitude, longitude)


def _first(times, flags) -> datetime | None:
    """The first genuine crossing in a search window, as naive UTC.

    Skyfield returns a time for every day in the window even when the body never
    reached the horizon -- the flag is False and the time is the moment of
    highest (or lowest) altitude instead. Treating that placeholder as a sunrise
    is how polar-latitude bugs get shipped, so the flag is checked, not ignored.
    """
    for t, ok in zip(times, flags):
        if ok:
            return time_to_civil(t)
    return None


def rise_and_set(
    body: str,
    latitude: float,
    longitude: float,
    window_start: datetime,
    window_hours: float = 26.0,
) -> RiseSet:
    """First rising and the setting that follows it, searching from an instant.

    ``window_start`` is a naive UTC datetime. The window runs a little over a day
    because a rising and the setting after it can straddle more than 24 hours at
    high latitude, and because a search that begins just after one sunrise must
    still find the next.
    """
    ts = get_timescale()
    t0 = civil_to_time(window_start)
    t1 = ts.tt_jd(t0.tt + window_hours / 24.0)

    observer = _observer(latitude, longitude)
    target = get_kernel()[body]

    rise_times, rise_ok = almanac.find_risings(observer, target, t0, t1)
    rising = _first(rise_times, rise_ok)

    # Search for the setting from the rising itself, not from the window start,
    # or a body already above the horizon at t0 yields the setting that belongs
    # to the *previous* rising and the pair straddles a night instead of a day.
    if rising is not None:
        s0 = civil_to_time(rising)
        s1 = ts.tt_jd(s0.tt + window_hours / 24.0)
    else:
        s0, s1 = t0, t1

    set_times, set_ok = almanac.find_settings(observer, target, s0, s1)
    setting = _first(set_times, set_ok)

    # Which polar case this is follows from *which* search came up empty, and
    # that is more reliable than sampling the altitude at one instant. A sunrise
    # with no sunset after it is the last rising before the midnight sun; a
    # sunset with no rising before it is the first day of the polar night.
    if rising is not None and setting is not None:
        condition = "normal"
    elif rising is not None:
        condition = "always_up"
    elif setting is not None:
        condition = "always_down"
    else:
        alt = observer.at(t0).observe(target).apparent().altaz()[0].degrees
        condition = "always_up" if alt > 0 else "always_down"

    return RiseSet(rising=rising, setting=setting, condition=condition)


def sun_rise_set(
    latitude: float, longitude: float, window_start: datetime
) -> RiseSet:
    return rise_and_set("sun", latitude, longitude, window_start)


def moon_rise_set(
    latitude: float, longitude: float, window_start: datetime
) -> RiseSet:
    return rise_and_set("moon", latitude, longitude, window_start)


def local_midnight_utc(day: DateType, zone: ZoneInfo) -> datetime:
    """00:00 local on ``day``, as naive UTC -- the search window's start.

    Sunrise has to be found for a *local* calendar day, so the search cannot
    start at UTC midnight: for Chennai that is 05:30 local, which is already
    within half an hour of sunrise and lands on the wrong side of it for part of
    the year.
    """
    local = datetime.combine(day, time(0, 0)).replace(tzinfo=zone)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def vaara_of(day_local: DateType) -> int:
    """Weekday index of a Jyotish day. 0 = Sunday.

    A Jyotish day is named after the **local calendar date its sunrise falls
    in**, so this takes that date rather than an instant. Which local date a
    given moment belongs to is a separate question, and a different one: the
    civil day rolls over at midnight while the Jyotish day (vaara) rolls over at
    sunrise, so a child born at 03:00 on a Tuesday is born on Monday's vaara and
    Monday's rahu kalam is the one that applied. Tamil almanacs are explicit
    about this; consumer apps routinely get it wrong.

    Splitting the two questions is not tidiness. Deriving the weekday from a UTC
    instant instead double-counts the rollover east of Greenwich: 03:00 IST is
    22:00 UTC on the *previous* UTC date, so subtracting a day for "before
    sunrise" lands two days back. It gave the right answer for India by
    coincidence and would have been wrong elsewhere.
    """
    return (day_local.weekday() + 1) % 7  # Python: Monday=0. Jyotish: Sunday=0.
