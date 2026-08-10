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

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder


def parse_time(text: str) -> tuple[int, int, int]:
    """Parse a birth time, accepting both 24-hour and AM/PM forms.

    Accepts ``18:30``, ``6:30 PM``, ``6:30pm``, ``06:30 AM``, ``18:30:45``.
    A bare time is 24-hour, so ``06:30`` means the morning.

    This matters more than it looks. Getting AM/PM wrong shifts the birth by
    twelve hours, which moves the ascendant by roughly 180 degrees -- a
    completely different lagna, a different dasha balance, and a chart that is
    wrong in every particular while looking entirely plausible. It is the same
    class of silent error as an unresolved daylight-saving ambiguity, so it is
    handled the same way: accept both notations, and refuse contradictions
    rather than guessing.

    Returns:
        (hour, minute, second) on a 24-hour clock.

    Raises:
        ValueError: if the text cannot be read, or says something like
            "13:30 PM".
    """
    raw = text.strip().lower().replace(".", "")

    meridiem = None
    for suffix in ("am", "pm"):
        if raw.endswith(suffix):
            meridiem = suffix
            raw = raw[: -len(suffix)].strip()
            break

    parts = raw.split(":")
    if not 2 <= len(parts) <= 3:
        raise ValueError(f"Cannot read time {text!r}. Use HH:MM, or 6:30 PM.")
    try:
        hour, minute = int(parts[0]), int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        raise ValueError(f"Cannot read time {text!r}. Use HH:MM, or 6:30 PM.") from None

    if meridiem:
        if not 1 <= hour <= 12:
            raise ValueError(
                f"{text!r} is contradictory: with AM/PM the hour must be 1-12. "
                f"Did you mean {hour:02d}:{minute:02d} on a 24-hour clock?"
            )
        if meridiem == "am" and hour == 12:      # 12 AM is midnight
            hour = 0
        elif meridiem == "pm" and hour != 12:    # 12 PM is already noon
            hour += 12

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ValueError(f"{text!r} is not a valid time.")
    return hour, minute, second


def format_time_12h(hour: int, minute: int, second: int = 0) -> str:
    """'6:30 AM' -- shown beside the 24-hour value so a mis-entry is obvious."""
    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    tail = f":{second:02d}" if second else ""
    return f"{display_hour}:{minute:02d}{tail} {suffix}"


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
        fold: which occurrence to use when the local time happens twice, as it
            does for the hour repeated at the end of daylight saving. 0 selects
            the first (still on summer time), 1 the second. See
            :attr:`time_is_ambiguous`.
        altitude_m: metres above sea level; affects the topocentric ascendant
            only marginally but is carried for completeness.
    """

    when: datetime
    latitude: float
    longitude: float
    timezone_name: str | None = None
    fold: int = 0
    altitude_m: float = 0.0
    name: str | None = None
    place_name: str | None = None

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
        if self.fold not in (0, 1):
            raise ValueError(f"fold must be 0 or 1, got {self.fold}")

    @property
    def offset_note(self) -> str | None:
        """A short explanation when the offset in force is not the obvious one.

        Users check the offset against what they expect (+5:30 for India), so an
        unexpected value has to explain itself or it reads as a bug. These are
        the cases where the engine is right and the expectation is wrong.
        """
        aware = self._aware

        # Specific cases first. The tz database models India's 1942-45 offset as
        # daylight saving, so the generic DST branch would otherwise label a
        # wartime measure "daylight saving" and leave the user more confused
        # than the bare number would have.
        if self.zone.key == "Asia/Kolkata" and self.utc_offset == timedelta(hours=6, minutes=30):
            return "wartime India, 1942-09-01 to 1945-10-15"
        # Local mean time, before standard zones. Detected by the offset not
        # being a whole number of minutes -- a mean-time offset is derived from
        # the meridian, so it carries odd seconds. This is more robust than
        # matching abbreviations: Chennai's pre-1906 zone is "MMT" (Madras Mean
        # Time), Kolkata's earlier one "HMT", and other cities differ again.
        if self.utc_offset.total_seconds() % 60 != 0:
            label = aware.tzname() or "local mean time"
            return f"{label}, local mean time before standard zones were adopted"

        dst = aware.dst() or timedelta(0)
        if dst:
            return f"daylight saving in force (+{int(dst.total_seconds() // 60)} min)"
        return None

    @classmethod
    def from_place(
        cls,
        place,
        when: datetime,
        *,
        timezone_name: str | None = None,
        fold: int = 0,
    ) -> "BirthData":
        """Build a birth record from a :class:`~jyotish.core.places.Place`.

        GeoNames supplies the IANA zone for every place, so no coordinate-to-zone
        inference is needed on this path; ``resolve_timezone`` remains the
        fallback for manually entered coordinates.
        """
        return cls(
            when=when,
            latitude=place.latitude,
            longitude=place.longitude,
            timezone_name=timezone_name or place.timezone,
            fold=fold,
            place_name=place.display_name,
        )

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name or resolve_timezone(self.latitude, self.longitude))

    @property
    def _aware(self) -> datetime:
        return self.when.replace(tzinfo=self.zone, fold=self.fold)

    @property
    def time_is_ambiguous(self) -> bool:
        """True when this local time occurs twice, at the end of summer time.

        The clock goes back and the hour repeats, so the same wall-clock reading
        maps to two different instants an hour apart. An hour is roughly 15
        degrees of ascendant -- frequently a different rasi -- so this must be
        surfaced to the user rather than silently resolved. Use :attr:`fold` to
        choose.
        """
        zone = self.zone
        first = self.when.replace(tzinfo=zone, fold=0).utcoffset()
        second = self.when.replace(tzinfo=zone, fold=1).utcoffset()
        return first != second and not self.time_is_nonexistent

    @property
    def time_is_nonexistent(self) -> bool:
        """True when this local time never happened, at the start of summer time.

        The clock jumps forward and skips an hour, so e.g. 02:30 on 6 April 1997
        does not exist in America/Los_Angeles. Python resolves such values
        silently, which would mean casting a chart for a moment that never
        occurred.
        """
        zone = self.zone
        naive = self.when.replace(tzinfo=None)
        round_tripped = (
            naive.replace(tzinfo=zone).astimezone(timezone.utc).astimezone(zone)
        )
        return round_tripped.replace(tzinfo=None) != naive

    @property
    def alternative(self) -> "BirthData | None":
        """The other reading of an ambiguous time, or None when unambiguous."""
        if not self.time_is_ambiguous:
            return None
        return replace(self, fold=1 - self.fold)

    @property
    def utc_offset(self) -> timedelta:
        """The offset actually in force at this place and moment."""
        return self._aware.utcoffset() or timedelta(0)

    @property
    def utc(self) -> datetime:
        """The birth moment in UTC."""
        return self._aware.astimezone(timezone.utc)

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
