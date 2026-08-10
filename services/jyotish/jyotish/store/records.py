"""Saved birth records — the chart library.

Storage choice: **SQLite**, not PostgreSQL as `docs/ARCHITECTURE.md` originally
projected. This is a single-user tool running on one machine that the owner
controls completely; there is no concurrency to manage and no server worth
administering. SQLite gives zero configuration, a backup that is one file copy,
and no credentials to lose. PostgreSQL remains the right answer the moment this
becomes multi-user, and the schema below deliberately avoids SQLite-only
features so that migration is a data move rather than a rewrite.

**What is stored, and why it is stored this way.**

A saved record keeps the *inputs* a user typed, plus the **resolved** place
data — latitude, longitude, timezone and display name — alongside the
`geonameid` they came from.

That redundancy is deliberate and is the single most important decision here.
The obvious design stores only the `geonameid` and re-resolves it on read. But
the place index is a 100 MB build artifact, regenerated from a GeoNames download
that is not version-controlled and has no recorded vintage. Rebuild it from a
newer dump and a saved chart could silently resolve to different coordinates or
a different timezone -- the chart changes, with no user action and nothing to
diff against. Storing what was actually used makes a saved chart immutable by
construction.

Computed charts are *not* stored. They are a pure function of the inputs plus
the engine version, so caching them would only create a second thing that can
go stale. A record is re-cast on open, at whatever accuracy the engine has now.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "ASTROAPP_LIBRARY_DB",
        Path(__file__).resolve().parents[3].parent / "data" / "library.sqlite",
    )
)

SCHEMA_VERSION = 1

_lock = threading.RLock()
_connection: sqlite3.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS birth_records (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    notes         TEXT NOT NULL DEFAULT '',

    -- Inputs, exactly as entered.
    birth_date    TEXT NOT NULL,          -- YYYY-MM-DD, local to the place
    birth_time    TEXT NOT NULL,          -- HH:MM:SS, 24-hour, local
    fold          INTEGER NOT NULL DEFAULT 0,
    ayanamsa      TEXT NOT NULL DEFAULT 'lahiri',

    -- Resolved place. Kept verbatim so a rebuilt place index can never move a
    -- saved chart; geonameid is a provenance note, not the source of truth.
    geonameid     INTEGER,
    place_name    TEXT NOT NULL DEFAULT '',
    latitude      REAL NOT NULL,
    longitude     REAL NOT NULL,
    timezone_name TEXT NOT NULL,

    vargas        TEXT NOT NULL DEFAULT '["D1","D9"]',   -- JSON array
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_records_name    ON birth_records(name);
CREATE INDEX IF NOT EXISTS idx_records_updated ON birth_records(updated_at DESC);
"""


class LibraryError(RuntimeError):
    """Raised when the library cannot be opened or a record is invalid."""


@dataclass
class BirthRecord:
    """One saved birth, as stored."""

    name: str
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone_name: str
    id: int | None = None
    notes: str = ""
    fold: int = 0
    ayanamsa: str = "lahiri"
    geonameid: int | None = None
    place_name: str = ""
    vargas: list[str] = field(default_factory=lambda: ["D1", "D9"])
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise LibraryError("A saved record needs a name.")
        if not -90.0 <= self.latitude <= 90.0:
            raise LibraryError(f"latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise LibraryError(f"longitude out of range: {self.longitude}")
        if self.fold not in (0, 1):
            raise LibraryError(f"fold must be 0 or 1, got {self.fold}")


def _now() -> str:
    """Timestamp with microseconds kept.

    Truncating to seconds made records saved in the same second sort
    arbitrarily, which is visible as a library list that reshuffles itself.
    Precision here is for ordering, not display; the UI formats it.
    """
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    """Open the library, creating it on first use."""
    global _connection
    with _lock:
        if _connection is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            con.row_factory = sqlite3.Row
            # Write-ahead logging: a reader never blocks the writer, which
            # matters because FastAPI serves these from a threadpool.
            con.execute("PRAGMA journal_mode = WAL")
            con.execute("PRAGMA foreign_keys = ON")
            con.executescript(_SCHEMA)
            con.execute(
                "INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            con.commit()
            _connection = con
        return _connection


def close() -> None:
    """Close the library. Used by tests to release the file."""
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None


def _to_record(row: sqlite3.Row) -> BirthRecord:
    return BirthRecord(
        id=row["id"],
        name=row["name"],
        notes=row["notes"],
        birth_date=row["birth_date"],
        birth_time=row["birth_time"],
        fold=row["fold"],
        ayanamsa=row["ayanamsa"],
        geonameid=row["geonameid"],
        place_name=row["place_name"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        timezone_name=row["timezone_name"],
        vargas=json.loads(row["vargas"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def save(record: BirthRecord) -> BirthRecord:
    """Insert a new record, or update an existing one when ``id`` is set."""
    con = connect()
    now = _now()
    values = (
        record.name.strip(), record.notes, record.birth_date, record.birth_time,
        record.fold, record.ayanamsa, record.geonameid, record.place_name,
        record.latitude, record.longitude, record.timezone_name,
        json.dumps(record.vargas),
    )

    with _lock:
        # try/except with an explicit rollback. The "no such record" raise
        # below fires *after* the UPDATE has opened a write transaction, and
        # without a rollback that transaction stayed open on the shared
        # connection -- holding SQLite's write lock indefinitely, so any other
        # process trying to write the file blocked until the busy timeout.
        try:
            if record.id is None:
                cur = con.execute(
                    "INSERT INTO birth_records (name, notes, birth_date, birth_time,"
                    " fold, ayanamsa, geonameid, place_name, latitude, longitude,"
                    " timezone_name, vargas, created_at, updated_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (*values, now, now),
                )
                record.id = cur.lastrowid
                record.created_at = now
            else:
                cur = con.execute(
                    "UPDATE birth_records SET name=?, notes=?, birth_date=?,"
                    " birth_time=?, fold=?, ayanamsa=?, geonameid=?, place_name=?,"
                    " latitude=?, longitude=?, timezone_name=?, vargas=?,"
                    " updated_at=? WHERE id=?",
                    (*values, now, record.id),
                )
                if cur.rowcount == 0:
                    raise LibraryError(f"No saved record with id {record.id}.")
            record.updated_at = now
            con.commit()
        except Exception:
            con.rollback()
            raise

    return record


def get(record_id: int) -> BirthRecord | None:
    row = connect().execute(
        "SELECT * FROM birth_records WHERE id = ?", (record_id,)
    ).fetchone()
    return _to_record(row) if row else None


def list_records(query: str = "", limit: int = 100) -> list[BirthRecord]:
    """Most recently updated first, optionally filtered by name or place."""
    con = connect()
    limit = max(1, min(limit, 500))

    if query.strip():
        like = f"%{query.strip().lower()}%"
        rows = con.execute(
            "SELECT * FROM birth_records"
            " WHERE lower(name) LIKE ? OR lower(place_name) LIKE ?"
            # id breaks ties so the order is deterministic even if two records
            # somehow carry the same timestamp.
            " ORDER BY updated_at DESC, id DESC LIMIT ?",
            (like, like, limit),
        )
    else:
        rows = con.execute(
            "SELECT * FROM birth_records ORDER BY updated_at DESC, id DESC LIMIT ?",
            (limit,),
        )
    return [_to_record(r) for r in rows]


def delete(record_id: int) -> bool:
    con = connect()
    with _lock:
        cur = con.execute("DELETE FROM birth_records WHERE id = ?", (record_id,))
        con.commit()
    return cur.rowcount > 0


def count() -> int:
    return connect().execute("SELECT COUNT(*) FROM birth_records").fetchone()[0]
