"""Birth data and the conversion from local civil time to UTC.

This is where a surprising share of real-world chart errors come from, and it
matters more for us than for a domestic-only app because the audience includes
the global Tamil diaspora. Three cases have to be right:

* Pre-1906 Tamil Nadu, when Madras kept local mean time at UTC+5:21:10.
* 1941-1945, when India ran UTC+6:30 for the war.
* Diaspora births in Singapore, Malaysia, the UK and the US, where DST and
  historical offset changes both apply.

We therefore never hardcode +5:30. The IANA tz database, via zoneinfo, carries
the full history, so we resolve the zone from coordinates (or an explicit zone)
and let it compute the offset that was actually in force on that date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder


@lru_cache(maxsize=1)
def _tz_finder() -> TimezoneFinder:
    return TimezoneFinder()


def resolve_timezone(latitude: float, longitude: float) -> str:
    """IANA timezone name for a coordinate pair."""
    name = _tz_finder().timezone_at(lat=latitude, lng=longitude)
    if name is None:
        # Ocean or unmapped territory; fall back to nautical time by longitude.
        offset_hours = round(longitude / 15.0)
        return f"Etc/GMT{-offset_hours:+d}"
    return name


@dataclass(frozen=True)
class BirthData:
    """A birth record.

    Args:
        when: local civil date and time at the birth place. Must be naive --
            passing an aware datetime is rejected, because it would silently
            bypass the historical-offset resolution that is the whole point of
            this class.
        latitude: degrees north, negative south.
        longitude: degrees east, negative west.
        timezone_name: optional IANA zone override. When omitted it is derived
            from the coordinates. Supply it when the birth certificate names a
            zone, or for places near a zone boundary.
        altitude_m: metres above sea level; affects the topocentric ascendant
            only marginally but is carried for completeness.
    """

    when: datetime
    latitude: float
    longitude: float
    timezone_name: str | None = None
    altitude_m: float = 0.0
    name: str | None = None

    def __post_init__(self) -> None:
        if self.when.tzinfo is not None:
            raise ValueError(
                "BirthData.when must be a naive local datetime; the zone is "
                "resolved from coordinates or timezone_name."
            )
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"longitude out of range: {self.longitude}")

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name or resolve_timezone(self.latitude, self.longitude))

    @property
    def utc_offset(self) -> timedelta:
        """The offset actually in force at this place and moment."""
        return self.when.replace(tzinfo=self.zone).utcoffset() or timedelta(0)

    @property
    def utc(self) -> datetime:
        """The birth moment in UTC."""
        return self.when.replace(tzinfo=self.zone).astimezone(timezone.utc)

    def skyfield_time(self):
        """This birth moment as a Skyfield Time.

        Deliberately built with ``ts.ut1`` rather than ``ts.utc``. Civil clock
        time is Universal Time; UTC with leap seconds only came into existence
        in 1972, so feeding a historical birth time through the TAI leap-second
        chain misdates it -- by 16 seconds for a 1943 birth and 44 seconds for a
        1900 one. That is 4 arcminutes of ascendant in the 1900 case, which is
        enough to change the lagna near a rasi boundary.

        Every Jyotish and astronomy package treats historical civil time as UT,
        so this also keeps us consistent with the Swiss Ephemeris oracle and
        with Jagannatha Hora.
        """
        from .ephemeris import get_timescale

        u = self.utc
        return get_timescale().ut1(
            u.year, u.month, u.day, u.hour, u.minute, u.second + u.microsecond / 1e6
        )
