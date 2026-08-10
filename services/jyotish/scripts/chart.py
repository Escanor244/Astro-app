"""Print a jathagam from the command line.

    python scripts/chart.py --date 1990-05-15 --time 06:30 --place "Chennai"

This exists so the engine is inspectable before any UI exists, and so a
practising astrologer can diff our output against Jagannatha Hora directly.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Put services/jyotish on the path before importing the engine.
#
# Running `python scripts/chart.py` puts *scripts/* on sys.path, not the project
# root, so `import jyotish` would otherwise fail no matter which interpreter is
# used. pytest does not need this because pytest.ini sets `pythonpath = .`.
# Do not remove: without it the documented command only works when PYTHONPATH
# happens to be set.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _env  # noqa: E402  -- must follow the path bootstrap above

try:
    from jyotish.charts import vargas
    from jyotish.core import ayanamsa as ay
    from jyotish.core import places as places_db
    from jyotish.core import positions as pos
    from jyotish.core.angles import format_dms, format_zodiacal
    from jyotish.core.birthdata import BirthData, format_time_12h, parse_time
    from jyotish.core.zodiac import GRAHAS, NAKSHATRAS, RASIS
except ImportError:
    # Almost always the system Python rather than the project venv.
    _env.ensure_dependencies()
    raise

#: South Indian chart layout. Rasis are FIXED in this grid -- Mesham always sits
#: at row 0, column 1 -- and it is the houses that rotate with the lagna. That
#: is the opposite of the North Indian diamond, where houses are fixed and signs
#: move, and it is why this app treats the square chart as primary.
SOUTH_INDIAN_GRID = [
    [11, 0, 1, 2],
    [10, None, None, 3],
    [9, None, None, 4],
    [8, 7, 6, 5],
]


def draw_south_indian(
    lagna_rasi: int,
    graha_rasis: dict[int, int],
    retrogrades: set[int] | frozenset[int],
    lang: str = "en",
) -> str:
    """Render a South Indian square chart.

    Takes placements rather than a birth record, so the same renderer draws the
    Rasi chart and every varga -- a divisional chart is the same fixed grid with
    grahas mapped to different rasis.
    """
    occupants: dict[int, list[str]] = {i: [] for i in range(12)}
    for gi, rasi in graha_rasis.items():
        mark = GRAHAS[gi].en[:2]
        if gi in retrogrades and gi not in (7, 8):
            mark += "ʀ"
        occupants[rasi].append(mark)

    cell_w, cell_h = 15, 4
    lines: list[str] = []

    for row in SOUTH_INDIAN_GRID:
        block = [""] * cell_h
        for rasi in row:
            if rasi is None:
                cell = [" " * cell_w] * cell_h
            else:
                label = RASIS[rasi].ta if lang == "ta" else RASIS[rasi].en[:12]
                asc = " <ASC" if rasi == lagna_rasi else ""
                house = f"{(rasi - lagna_rasi) % 12 + 1}"
                cell = [
                    f" {label}{asc}".ljust(cell_w),
                    f" [{house}]".ljust(cell_w),
                    f" {' '.join(occupants[rasi][:3])}".ljust(cell_w),
                    f" {' '.join(occupants[rasi][3:])}".ljust(cell_w),
                ]
            for i in range(cell_h):
                block[i] += "|" + cell[i]
        lines.append("+" + "+".join("-" * cell_w for _ in row) + "+")
        lines.extend(b + "|" for b in block)
    lines.append("+" + "+".join("-" * cell_w for _ in SOUTH_INDIAN_GRID[0]) + "+")
    return "\n".join(lines)


def format_offset(delta) -> str:
    """'UTC+06:30' -- including the odd historical offsets that are not whole hours."""
    total = int(delta.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, m, s = total // 3600, (total % 3600) // 60, total % 60
    return f"UTC{sign}{h:02d}:{m:02d}" + (f":{s:02d}" if s else "")


def resolve_place(query: str, pick: int | None):
    """Turn a place query into a single Place, or exit with the candidate list."""
    try:
        matches = places_db.search(query, limit=10)
    except places_db.PlacesDatabaseMissing as exc:
        sys.exit(f"\n{exc}\n")

    if not matches:
        sys.exit(f"\nNo place matching {query!r}. Try fewer letters, or use --lat/--lon.\n")

    if pick is not None:
        if not 1 <= pick <= len(matches):
            sys.exit(f"\n--pick must be between 1 and {len(matches)}.\n")
        return matches[pick - 1]

    if len(matches) > 1:
        print(f"\n{len(matches)} places match {query!r}. Re-run with --pick N:\n")
        for i, m in enumerate(matches, 1):
            print(f"  {i:>2}. {m.display_name:<48} {m.latitude:8.4f} {m.longitude:9.4f}"
                  f"  {m.timezone:<18} pop {m.population:,}")
        print()
        sys.exit(0)

    return matches[0]


def main() -> None:
    # Tamil is printed unconditionally, but a redirected stdout on Windows
    # defaults to the ANSI code page (cp1252 here), which cannot encode it. That
    # made `chart.py ... > chart.txt` die with UnicodeEncodeError after six
    # lines and leave a truncated file -- precisely the redirect-and-diff
    # workflow this script exists to support.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="Cast a Vedic jathagam.")
    p.add_argument("--date", required=True, help="local birth date, YYYY-MM-DD")
    p.add_argument("--time", required=True,
                   help='local birth time: 24-hour "18:30", or "6:30 PM"')
    p.add_argument("--place", help='birth place, e.g. "Madurai" (Tamil script works too)')
    p.add_argument("--pick", type=int, help="choose the Nth place when several match")
    p.add_argument("--lat", type=float, help="latitude, if entering coordinates directly")
    p.add_argument("--lon", type=float, help="longitude, if entering coordinates directly")
    p.add_argument("--tz", default=None, help="IANA zone override, e.g. Asia/Kolkata")
    p.add_argument("--fold", type=int, default=0, choices=[0, 1],
                   help="for a repeated hour at the end of summer time: 0=first, 1=second")
    p.add_argument("--ayanamsa", default="lahiri",
                   choices=[a.value for a in ay.Ayanamsa])
    p.add_argument("--lang", default="en", choices=["en", "ta"])
    p.add_argument("--varga", default="d1",
                   help="divisional charts to draw, comma-separated, "
                        'e.g. "d1,d9" for Rasi plus Navamsam. Use "all" for the '
                        f"full Shodashavarga. Known: {','.join(v.lower() for v in vargas.VARGA_ORDER)}")
    args = p.parse_args()

    if not args.place and (args.lat is None or args.lon is None):
        p.error("give either --place, or both --lat and --lon")

    requested = (
        list(vargas.VARGA_ORDER) if args.varga.strip().lower() == "all"
        else [v.strip().upper() for v in args.varga.split(",") if v.strip()]
    )
    for code in requested:
        if code not in vargas.VARGAS:
            p.error(f"unknown varga {code!r}; known: "
                    f"{', '.join(v.lower() for v in vargas.VARGA_ORDER)}")

    try:
        hour, minute, second = parse_time(args.time)
        birth_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError as exc:
        p.error(str(exc))
    when = datetime(birth_date.year, birth_date.month, birth_date.day,
                    hour, minute, second)

    if args.place:
        place = resolve_place(args.place, args.pick)
        birth = BirthData.from_place(place, when, timezone_name=args.tz, fold=args.fold)
        place_line = f"{place.display_name}  ({place.latitude:.4f}, {place.longitude:.4f})"
    else:
        birth = BirthData(when=when, latitude=args.lat, longitude=args.lon,
                          timezone_name=args.tz, fold=args.fold)
        place_line = f"{birth.latitude:.4f}, {birth.longitude:.4f}"

    # Surface time-zone edge cases before showing any chart. An hour of doubt is
    # about 15 degrees of ascendant, so a silently-chosen interpretation could
    # hand the user a chart with the wrong lagna and no hint anything was wrong.
    if birth.time_is_nonexistent:
        print(f"\n  !! {when:%Y-%m-%d %H:%M} does not exist in {birth.zone.key} -- "
              "the clocks jumped forward over it.\n     Check the birth record; the "
              "chart below assumes the pre-transition offset.")
    elif birth.time_is_ambiguous:
        other = birth.alternative
        print(f"\n  !! {when:%Y-%m-%d %H:%M} occurs twice in {birth.zone.key} "
              "(clocks went back).\n     Using --fold "
              f"{birth.fold} = {format_offset(birth.utc_offset)}; the other reading is "
              f"{format_offset(other.utc_offset)}.\n     These give lagnas about 15 "
              "degrees apart, so confirm which one applies.")

    chart = pos.compute(birth, ay.Ayanamsa(args.ayanamsa))

    note = birth.offset_note
    # Always echo the 12-hour reading. Someone who meant an evening birth and
    # typed "06:30" should see "6:30 AM" here and catch it before reading a
    # chart whose lagna is half a zodiac out.
    print(f"\nBirth   : {birth.when:%Y-%m-%d}  {birth.when:%H:%M:%S}  "
          f"({format_time_12h(hour, minute, second)})")
    print(f"Place   : {place_line}")
    print(f"Zone    : {birth.zone.key}")
    print(f"Offset  : {format_offset(birth.utc_offset)}"
          + (f"   [{note}]" if note else ""))
    print(f"UTC     : {birth.utc:%Y-%m-%d %H:%M:%S}")
    print(f"Ayanamsa: {chart.ayanamsa_system.value}  {format_dms(chart.ayanamsa_value)}")

    lagna = chart.lagna
    print(f"\nLagna   : {RASIS[lagna.rasi].en} ({RASIS[lagna.rasi].ta}) "
          f"{format_zodiacal(lagna.longitude)}  "
          f"{NAKSHATRAS[lagna.nakshatra].en} pada {lagna.pada}")

    print(f"\n{'Graha':<10}{'Tamil':<12}{'Rasi':<13}{'Deg':>13}  {'Nakshatra':<18}{'Pada':>5}{'Ho':>4}  R")
    print("-" * 82)
    for gi in range(9):
        gp = chart.grahas[gi]
        z = gp.position
        print(f"{GRAHAS[gi].en:<10}{GRAHAS[gi].ta:<12}{RASIS[z.rasi].en:<13}"
              f"{format_zodiacal(z.longitude):>13}  {NAKSHATRAS[z.nakshatra].en:<18}"
              f"{z.pada:>5}{chart.house_of(gi):>4}  {'R' if gp.retrograde else ''}")

    for code in requested:
        vc = vargas.compute(chart, code)
        name = vc.varga.name
        print(f"\n{vc.varga.code}  {name.en} / {name.ta} ({name.ta_latin}) "
              f"kattam -- {vc.varga.significance}")
        print(draw_south_indian(vc.lagna_rasi, vc.graha_rasis, vc.retrogrades, args.lang))
    print()


if __name__ == "__main__":
    main()
