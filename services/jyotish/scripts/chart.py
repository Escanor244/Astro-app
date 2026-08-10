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
    from jyotish.core import dignity
    from jyotish.core import places as places_db
    from jyotish.core import positions as pos
    from jyotish.core.angles import format_dms, format_zodiacal
    from jyotish.core.birthdata import BirthData, format_time_12h, parse_time
    from jyotish.core.zodiac import GRAHAS, MOON, NAKSHATRAS, RASIS
    from jyotish.dasha import vimshottari as vd
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


def print_dasha(birth, chart, at_text: str | None, year_length: str, lang: str) -> None:
    """The Vimshottari table: balance, mahadashas, and what is running.

    Dates are printed in local time at the birth place, which is the frame a
    printed jathagam uses. The engine works in UTC throughout and converts only
    here, at the display edge.
    """
    from datetime import timezone

    zone = birth.zone
    birth_utc = birth.utc.replace(tzinfo=None)
    moon = chart.grahas[MOON].longitude

    def local(moment) -> str:
        return (
            moment.replace(tzinfo=timezone.utc).astimezone(zone).strftime("%Y-%m-%d")
        )

    def local_dt(moment) -> str:
        return (
            moment.replace(tzinfo=timezone.utc).astimezone(zone)
            .strftime("%Y-%m-%d %H:%M")
        )

    if at_text:
        try:
            at_local = datetime.fromisoformat(at_text)
        except ValueError:
            sys.exit(f"\n--at must be YYYY-MM-DD or an ISO datetime, not {at_text!r}.\n")
    else:
        at_local = datetime.now()
    at = at_local.replace(tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)

    balance = vd.balance_at_birth(moon, year_length=year_length)
    star = NAKSHATRAS[balance.nakshatra]

    print(f"\nVimshottari dasha  ({year_length} year, "
          f"{vd.year_days(year_length)} days)")
    print(f"Birth star : {star.en} ({star.ta})")
    print(f"Balance    : {balance.lord_name.en} ({balance.lord_name.ta})  "
          f"{balance.years}y {balance.months}m {balance.days}d   "
          f"[{balance.remaining_fraction * 100:.2f}% of the star still to cross]")

    periods = vd.mahadashas(birth_utc, moon, year_length=year_length)[:9]
    print(f"\n{'Mahadasha':<12}{'Tamil':<12}{'From':<12}{'To':<12}{'Years':>6}")
    print("-" * 54)
    for p in periods:
        mark = "  <" if p.contains(at) else ""
        print(f"{p.lord_name.en:<12}{p.lord_name.ta:<12}{local(p.start):<12}"
              f"{local(p.end):<12}{vd.YEARS[p.lord]:>6}{mark}")

    chain = vd.chain_at(birth_utc, moon, at, year_length=year_length)
    if not chain:
        print(f"\n{local(at)} falls outside the 120-year cycle from this birth.")
        return

    print(f"\nRunning on {local(at)}:")
    for p in chain:
        name = p.level_name
        label = f"{name.en} / {name.ta}"
        print(f"  {label:<32}{p.lord_name.en:<10}{p.lord_name.ta:<12}"
              f"{local_dt(p.start)}  ->  {local_dt(p.end)}")


def print_panchangam(birth, system, lang: str) -> None:
    """The Tamil daily almanac for the birth moment."""
    from datetime import timezone

    from jyotish.panchanga import panchangam as pg

    zone = birth.zone
    p = pg.compute(
        birth.utc.replace(tzinfo=None), birth.latitude, birth.longitude,
        zone.key, system,
    )

    def clock(moment) -> str:
        if moment is None:
            return "--"
        return moment.replace(tzinfo=timezone.utc).astimezone(zone).strftime("%H:%M")

    def stamp(moment) -> str:
        return (
            moment.replace(tzinfo=timezone.utc).astimezone(zone)
            .strftime("%d %b %H:%M")
        )

    print(f"\nPanchangam  {p.tamil_year_name.ta} ({p.tamil_year_name.en}) "
          f"{p.tamil_month_name.ta} {p.tamil_day}, {p.vaara_name.ta}")
    print(f"            {p.ayana_name.ta} · {p.ritu_name.ta}")
    print(f"Sun         {clock(p.sun.rising)} -> {clock(p.sun.setting)}"
          + ("" if p.has_daylight else f"   [{p.sun.condition}]"))
    print(f"Moon        {clock(p.moon.rising)} -> {clock(p.moon.setting)}")

    print(f"\n{'Limb':<12}{'Name':<18}{'Tamil':<18}until")
    print("-" * 62)
    for label, limb, extra in (
        ("Tithi", p.tithi, f" ({p.paksha_name.ta})"),
        ("Nakshatram", p.nakshatra, ""),
        ("Yogam", p.yoga, ""),
        ("Karanam", p.karana, ""),
    ):
        print(f"{label:<12}{limb.name.en:<18}{limb.name.ta + extra:<18}"
              f"{stamp(limb.end)}")

    if not p.has_daylight:
        print("\nNo sunrise or sunset on this date, so rahu kalam and the gowri")
        print("windows -- all fractions of the daylight interval -- are undefined.")
        return

    print()
    for window in (p.rahu_kalam, p.yamagandam, p.kuligai):
        print(f"{window.name.en:<12}{window.name.ta:<18}"
              f"{clock(window.start)} - {clock(window.end)}")

    print("\nGowri panchangam        pagal (day)                iravu (night)")
    print("-" * 70)
    for day, night in zip(p.gowri_day, p.gowri_night):
        mark = lambda w: "+" if w.auspicious else "-"  # noqa: E731
        print(f"  {mark(day)} {day.name.ta:<14}{clock(day.start)}-{clock(day.end)}"
              f"      {mark(night)} {night.name.ta:<14}"
              f"{clock(night.start)}-{clock(night.end)}")
    print("\n  + auspicious (nalla neram)   - avoid")


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
    p.add_argument("--panchangam", action="store_true",
                   help="print the Tamil almanac for the birth moment: the five "
                        "limbs, rahu kalam, and the gowri windows")
    p.add_argument("--dasha", action="store_true",
                   help="print the Vimshottari dasha: balance, the nine "
                        "mahadashas, and the five-level chain running now")
    p.add_argument("--at", default=None,
                   help="with --dasha, which moment to report as running "
                        "(YYYY-MM-DD, local to the birth place). Default: now")
    p.add_argument("--dasha-year", default=vd.DEFAULT_YEAR_LENGTH,
                   choices=sorted(vd.YEAR_DAYS),
                   help="days in a dasha year. The solar variants agree to "
                        "within two days over a whole cycle; savana is a "
                        "different tradition and lands ten months away")
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

    # The three marked states share one column because that is how a printed
    # jathagam shows them: R = vakram, C = asthangatham (combust). They are
    # independent of each other and of the dignity beside them.
    dignities = dignity.assess_chart(chart)
    print(f"\n{'Graha':<10}{'Tamil':<12}{'Rasi':<13}{'Deg':>13}  {'Nakshatra':<18}"
          f"{'Pada':>5}{'Ho':>4}  {'St':<4}{'Dignity':<14}Tamil")
    print("-" * 104)
    for gi in range(9):
        gp = chart.grahas[gi]
        z = gp.position
        d = dignities[gi]
        state = ("R" if gp.retrograde else "") + ("C" if d.combust else "")
        print(f"{GRAHAS[gi].en:<10}{GRAHAS[gi].ta:<12}{RASIS[z.rasi].en:<13}"
              f"{format_zodiacal(z.longitude):>13}  {NAKSHATRAS[z.nakshatra].en:<18}"
              f"{z.pada:>5}{chart.house_of(gi):>4}  {state:<4}"
              f"{d.name.en:<14}{d.name.ta}")
    print("\n  R = vakram (retrograde)   C = asthangatham (combust)")

    for code in requested:
        vc = vargas.compute(chart, code)
        name = vc.varga.name
        print(f"\n{vc.varga.code}  {name.en} / {name.ta} ({name.ta_latin}) "
              f"kattam -- {vc.varga.significance}")
        print(draw_south_indian(vc.lagna_rasi, vc.graha_rasis, vc.retrogrades, args.lang))

    if args.panchangam:
        print_panchangam(birth, ay.Ayanamsa(args.ayanamsa), args.lang)
    if args.dasha:
        print_dasha(birth, chart, args.at, args.dasha_year, args.lang)
    print()


if __name__ == "__main__":
    main()
