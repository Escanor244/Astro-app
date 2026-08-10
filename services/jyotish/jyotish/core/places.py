"""Offline place search, backed by the GeoNames SQLite index.

Birth data is entered by place name, never by coordinates -- nobody knows the
latitude of the village they were born in. This module turns "Madurai" or
"மதுரை" into coordinates *and* an IANA timezone, which is everything
:class:`~jyotish.core.birthdata.BirthData` needs.

Build the index first::

    python scripts/build_places_db.py

Data (c) GeoNames, CC BY 4.0 -- https://www.geonames.org/
"""

from __future__ import annotations

import os
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "ASTROAPP_PLACES_DB",
        Path(__file__).resolve().parents[3].parent / "data" / "places.sqlite",
    )
)

_lock = threading.RLock()
_connection: sqlite3.Connection | None = None

_COLUMNS = (
    "geonameid, name, ascii_name, admin1, country_code, country_name, "
    "latitude, longitude, timezone, population, feature_code"
)


class PlacesDatabaseMissing(RuntimeError):
    """Raised when the index has not been built yet."""


@dataclass(frozen=True)
class Place:
    """A populated place from GeoNames."""

    geonameid: int
    name: str
    ascii_name: str
    admin1: str
    country_code: str
    country_name: str
    latitude: float
    longitude: float
    timezone: str
    population: int
    feature_code: str

    @property
    def display_name(self) -> str:
        """'Madurai, Tamil Nadu, India'."""
        parts = [self.name]
        if self.admin1 and self.admin1 != self.name:
            parts.append(self.admin1)
        if self.country_name:
            parts.append(self.country_name)
        return ", ".join(parts)


def _connect() -> sqlite3.Connection:
    global _connection
    with _lock:
        if _connection is None:
            if not DB_PATH.exists():
                raise PlacesDatabaseMissing(
                    f"Place index not found at {DB_PATH}.\n"
                    "Build it once with:  python scripts/build_places_db.py"
                )
            _connection = sqlite3.connect(
                f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False
            )
            _connection.row_factory = sqlite3.Row
        return _connection


def _to_place(row: sqlite3.Row) -> Place:
    return Place(
        geonameid=row["geonameid"],
        name=row["name"],
        ascii_name=row["ascii_name"],
        admin1=row["admin1"] or "",
        country_code=row["country_code"] or "",
        country_name=row["country_name"] or "",
        latitude=row["latitude"],
        longitude=row["longitude"],
        timezone=row["timezone"],
        population=row["population"],
        feature_code=row["feature_code"] or "",
    )


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so a place called 'St. John%' cannot match everything."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search(query: str, limit: int = 10, country: str | None = None) -> list[Place]:
    """Search places by name, best match first.

    Results are ranked in four tiers -- exact name, exact alternate name,
    name prefix, alternate-name prefix -- and by population within each tier.

    The tiering is the important part. A bare "Chennai" must return the city of
    four million ahead of every minor place whose name merely begins with the
    same letters, and sorting by population alone would not do that: a hamlet
    named exactly "Chennai" should still lose to the city, but a place called
    "Chennaimalai" should never outrank an exact hit.

    Tamil script works through the alternate-name tiers, which is why they are
    interleaved with the Latin ones rather than appended after them.

    Args:
        query: place name, in Latin or Tamil script.
        limit: maximum results.
        country: optional ISO country code filter, e.g. ``"IN"``.
    """
    q = query.strip()
    if not q:
        return []

    con = _connect()
    key = q.lower()
    prefix = _escape_like(key) + "%"

    p_cols = ", ".join(f"p.{c}" for c in _COLUMNS.split(", "))
    cc_sql = " AND p.country_code = ?" if country else ""
    cc_args: tuple = (country,) if country else ()

    found: dict[int, tuple[int, Place]] = {}

    def collect(rank: int, sql: str, args: tuple) -> None:
        for row in con.execute(sql, args):
            place = _to_place(row)
            # The first tier to claim a place wins; never demote it later.
            found.setdefault(place.geonameid, (rank, place))

    # Rank is by *exactness*, not by which column matched. A primary-name hit
    # and an alternate-name hit are equally exact, so they share rank 0 and are
    # separated by population. Without this, searching "Trichy" returns a
    # population-zero hamlet named exactly Trichy ahead of Tiruchirappalli, the
    # city of a million that the name actually refers to.
    queries = (
        # Exact romanised name.
        (0, f"SELECT {p_cols} FROM places p WHERE p.search_key = ?{cc_sql} "
            "ORDER BY p.population DESC LIMIT ?", (key,)),
        # Exact alternate name -- this is how Tamil script matches.
        (0, f"SELECT {p_cols} FROM place_names n JOIN places p "
            f"ON p.geonameid = n.geonameid WHERE n.name_key = ?{cc_sql} "
            "ORDER BY p.population DESC LIMIT ?", (key,)),
        # Name prefix ("Madu" -> "Madurai").
        (1, f"SELECT {p_cols} FROM places p "
            f"WHERE p.search_key LIKE ? ESCAPE '\\'{cc_sql} "
            "ORDER BY p.population DESC LIMIT ?", (prefix,)),
        # Alternate-name prefix, for partial Tamil input.
        (1, f"SELECT {p_cols} FROM place_names n JOIN places p "
            f"ON p.geonameid = n.geonameid WHERE n.name_key LIKE ? ESCAPE '\\'{cc_sql} "
            "ORDER BY p.population DESC LIMIT ?", (prefix,)),
    )

    for rank, sql, args in queries:
        collect(rank, sql, (*args, *cc_args, limit * 4))

    # Demote places GeoNames records with no population by one tier.
    #
    # Village-level coverage is deliberate -- most Tamil birth places are small
    # -- so unpopulated entries must stay findable, and a village with a unique
    # name still ranks first because nothing competes with it. But without this,
    # typing "Madu" returns a population-zero hamlet ahead of Madurai, because
    # an exact match on a hamlet outranks a prefix match on a city of 1.4
    # million. Demoting by exactly one tier makes them tie, and population
    # settles it.
    def sort_key(entry: tuple[int, Place]) -> tuple[int, int]:
        rank, place = entry
        return (rank + (1 if place.population == 0 else 0), -place.population)

    return [place for _rank, place in sorted(found.values(), key=sort_key)[:limit]]


def get(geonameid: int) -> Place | None:
    """Fetch one place by its GeoNames id."""
    row = _connect().execute(
        f"SELECT {_COLUMNS} FROM places WHERE geonameid = ?", (geonameid,)
    ).fetchone()
    return _to_place(row) if row else None


def count() -> int:
    """Number of indexed places. Useful as a build sanity check."""
    return _connect().execute("SELECT COUNT(*) FROM places").fetchone()[0]
