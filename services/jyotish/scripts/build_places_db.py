"""Build the offline place-search database from GeoNames.

    python scripts/build_places_db.py

Produces ``data/places.sqlite``. Run once; the artifact is gitignored, like the
ephemeris kernel.

Why offline: birth-place entry is the very first thing a user does, and making
it depend on a third-party geocoding API would mean a network round trip, an API
key, rate limits and a per-lookup cost on the core input path -- for data that
essentially never changes. GeoNames ships the IANA timezone for every place, so
one local file answers both "where is this" and "what offset applied there".

Coverage is chosen deliberately:

* ``cities500`` -- every populated place worldwide over 500 people, for the
  diaspora audience.
* ``IN`` -- *all* Indian populated places, not just those over 500. Most Tamil
  Nadu birth places are villages that fall below any population cutoff, and
  "I was born in a village you don't list" is the fastest way to lose a user.
* Tamil alternate names for IN/LK/SG/MY, so a user can type மதுரை.

Data (c) GeoNames, CC BY 4.0 -- https://www.geonames.org/
"""

from __future__ import annotations

import csv
import io
import sqlite3
import sys
import urllib.request
import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
CACHE_DIR = DATA_DIR / "geonames_cache"
DB_PATH = DATA_DIR / "places.sqlite"

BASE = "https://download.geonames.org/export/dump/"

#: Country dumps to ingest in full (all populated places, no population floor).
FULL_COUNTRIES = ["IN"]

#: Countries whose Tamil/English alternate names we index. Tamil is spoken well
#: beyond Tamil Nadu -- Sri Lanka, Singapore and Malaysia all have large Tamil
#: populations and are common diaspora birth places.
ALT_NAME_COUNTRIES = ["IN", "LK", "SG", "MY"]

#: Languages worth indexing for search.
ALT_LANGS = {"ta", "en"}

#: GeoNames feature class for populated places. The per-country dumps also
#: contain mountains, rivers and administrative areas, which must not appear in
#: a birth-place picker.
POPULATED = "P"

# Column offsets in the GeoNames main dump format.
G_ID, G_NAME, G_ASCII, G_ALT = 0, 1, 2, 3
G_LAT, G_LON, G_FCLASS, G_FCODE, G_COUNTRY = 4, 5, 6, 7, 8
G_ADMIN1, G_POP, G_TZ = 10, 14, 17


def _download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  cached  {dest.name}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "AstroApp/0.1"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def _rows_from_zip(path: Path, member: str):
    """Yield tab-separated rows from a member of a GeoNames zip."""
    with zipfile.ZipFile(path) as z, z.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        yield from csv.reader(text, delimiter="\t", quoting=csv.QUOTE_NONE)


def _rows_from_txt(path: Path, skip_comments: bool = False):
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if skip_comments and row and row[0].startswith("#"):
                continue
            if row:
                yield row


def load_admin1() -> dict[str, str]:
    """Map 'IN.25' -> 'Tamil Nadu'."""
    path = _download(BASE + "admin1CodesASCII.txt", CACHE_DIR / "admin1CodesASCII.txt")
    return {row[0]: row[1] for row in _rows_from_txt(path) if len(row) >= 2}


def load_countries() -> dict[str, str]:
    """Map 'IN' -> 'India'."""
    path = _download(BASE + "countryInfo.txt", CACHE_DIR / "countryInfo.txt")
    out: dict[str, str] = {}
    for row in _rows_from_txt(path, skip_comments=True):
        if len(row) >= 5 and len(row[0]) == 2:
            out[row[0]] = row[4]
    return out


def load_places() -> dict[int, list]:
    """All places, keyed by geonameid so the sources deduplicate naturally."""
    places: dict[int, list] = {}

    sources: list[tuple[Path, str, bool]] = []
    p = _download(BASE + "cities500.zip", CACHE_DIR / "cities500.zip")
    sources.append((p, "cities500.txt", False))
    for cc in FULL_COUNTRIES:
        p = _download(f"{BASE}{cc}.zip", CACHE_DIR / f"{cc}.zip")
        sources.append((p, f"{cc}.txt", True))

    for path, member, filter_populated in sources:
        before = len(places)
        for row in _rows_from_zip(path, member):
            if len(row) < 18:
                continue
            if filter_populated and row[G_FCLASS] != POPULATED:
                continue
            try:
                gid = int(row[G_ID])
                lat, lon = float(row[G_LAT]), float(row[G_LON])
                pop = int(row[G_POP] or 0)
            except ValueError:
                continue
            if not row[G_TZ]:
                continue
            # The dump's inline `alternatenames` column is deliberately NOT
            # kept. It is untagged and carries every script on earth -- Chinese,
            # Cyrillic and Arabic transliterations of Tamil hamlets -- which
            # quadrupled the index size while adding nothing searchable for our
            # users. Language-tagged Tamil/English names are loaded separately.
            places[gid] = [
                gid, row[G_NAME], row[G_ASCII], row[G_COUNTRY],
                row[G_ADMIN1], lat, lon, row[G_TZ], pop, row[G_FCODE],
            ]
        print(f"  {member}: +{len(places) - before:,} (total {len(places):,})")

    return places


def load_alt_names(known: set[int]) -> dict[int, set[str]]:
    """Tamil and English alternate names for places we actually keep."""
    alt: dict[int, set[str]] = {}
    for cc in ALT_NAME_COUNTRIES:
        path = _download(f"{BASE}alternatenames/{cc}.zip", CACHE_DIR / f"alt_{cc}.zip")
        kept = 0
        for row in _rows_from_zip(path, f"{cc}.txt"):
            if len(row) < 4:
                continue
            try:
                gid = int(row[1])
            except ValueError:
                continue
            if gid not in known or row[2] not in ALT_LANGS or not row[3].strip():
                continue
            alt.setdefault(gid, set()).add(row[3].strip())
            kept += 1
        print(f"  alt/{cc}: +{kept:,} names")
    return alt


def build(places: dict[int, list], alt: dict[int, set[str]],
          admin1: dict[str, str], countries: dict[str, str]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)
    con.executescript(
        """
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;

        CREATE TABLE places (
            geonameid    INTEGER PRIMARY KEY,
            name         TEXT NOT NULL,
            ascii_name   TEXT NOT NULL,
            admin1       TEXT,
            country_code TEXT,
            country_name TEXT,
            latitude     REAL NOT NULL,
            longitude    REAL NOT NULL,
            timezone     TEXT NOT NULL,
            population   INTEGER NOT NULL DEFAULT 0,
            feature_code TEXT,
            search_key   TEXT NOT NULL   -- lowercased ascii name
        );

        -- Language-tagged alternate names only: Tamil script, plus English
        -- variants such as "Trichy". Small enough (a few thousand rows) that a
        -- plain indexed table beats an FTS5 index on both size and simplicity,
        -- and prefix search works the same way for both tables.
        CREATE TABLE place_names (
            geonameid INTEGER NOT NULL,
            name      TEXT NOT NULL,
            name_key  TEXT NOT NULL      -- lowercased; identity for Tamil
        );
        """
    )

    rows = []
    name_rows = []
    for gid, r in places.items():
        (_gid, name, ascii_name, cc, admin1_code, lat, lon, tz, pop, fcode) = r
        admin1_name = admin1.get(f"{cc}.{admin1_code}", "")

        rows.append((
            gid, name, ascii_name, admin1_name, cc, countries.get(cc, cc),
            lat, lon, tz, pop, fcode, ascii_name.lower(),
        ))
        for alt_name in alt.get(gid, ()):  # already Tamil/English only
            if alt_name.lower() != ascii_name.lower():
                name_rows.append((gid, alt_name, alt_name.lower()))

    con.executemany("INSERT INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.executemany("INSERT INTO place_names VALUES (?,?,?)", name_rows)
    con.executescript(
        """
        CREATE INDEX idx_search_key ON places(search_key);
        CREATE INDEX idx_population ON places(population DESC);
        CREATE INDEX idx_place_names_key ON place_names(name_key);
        CREATE INDEX idx_place_names_gid ON place_names(geonameid);
        """
    )
    print(f"  {len(rows):,} places, {len(name_rows):,} alternate names")
    con.commit()
    con.execute("VACUUM")
    con.close()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading reference tables...")
    admin1, countries = load_admin1(), load_countries()
    print("Loading places...")
    places = load_places()
    print("Loading Tamil/English alternate names...")
    alt = load_alt_names(set(places))
    print("Building SQLite index...")
    build(places, alt, admin1, countries)

    size_mb = DB_PATH.stat().st_size / 1024 / 1024
    print(f"\nWrote {DB_PATH}  ({len(places):,} places, {size_mb:.1f} MB)")
    print("Data (c) GeoNames, CC BY 4.0 -- https://www.geonames.org/")


if __name__ == "__main__":
    sys.exit(main())
