"""Print a jathagam from the command line.

    python scripts/chart.py --date 1990-05-15 --time 06:30 --lat 13.0827 --lon 80.2707

This exists so the engine is inspectable before any UI exists, and so a
practising astrologer can diff our output against Jagannatha Hora directly.
"""

from __future__ import annotations

import argparse
from datetime import datetime

from jyotish.core import ayanamsa as ay
from jyotish.core import positions as pos
from jyotish.core.angles import format_dms, format_zodiacal
from jyotish.core.birthdata import BirthData
from jyotish.core.zodiac import GRAHAS, NAKSHATRAS, RASIS

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


def draw_south_indian(chart: pos.ChartPositions, lang: str = "en") -> str:
    occupants: dict[int, list[str]] = {i: [] for i in range(12)}
    for gi, gp in chart.grahas.items():
        mark = GRAHAS[gi].en[:2]
        if gp.retrograde and gi not in (7, 8):
            mark += "ʀ"
        occupants[gp.position.rasi].append(mark)

    cell_w, cell_h = 15, 4
    lines: list[str] = []

    for row in SOUTH_INDIAN_GRID:
        block = [""] * cell_h
        for rasi in row:
            if rasi is None:
                cell = [" " * cell_w] * cell_h
            else:
                label = RASIS[rasi].ta if lang == "ta" else RASIS[rasi].en[:12]
                asc = " <ASC" if rasi == chart.lagna.rasi else ""
                house = f"{(rasi - chart.lagna.rasi) % 12 + 1}"
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


def main() -> None:
    p = argparse.ArgumentParser(description="Cast a Vedic jathagam.")
    p.add_argument("--date", required=True, help="local birth date, YYYY-MM-DD")
    p.add_argument("--time", required=True, help="local birth time, HH:MM or HH:MM:SS")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--tz", default=None, help="IANA zone; derived from coordinates if omitted")
    p.add_argument("--ayanamsa", default="lahiri",
                   choices=[a.value for a in ay.Ayanamsa])
    p.add_argument("--lang", default="en", choices=["en", "ta"])
    args = p.parse_args()

    fmt = "%Y-%m-%d %H:%M:%S" if args.time.count(":") == 2 else "%Y-%m-%d %H:%M"
    birth = BirthData(
        when=datetime.strptime(f"{args.date} {args.time}", fmt),
        latitude=args.lat,
        longitude=args.lon,
        timezone_name=args.tz,
    )
    chart = pos.compute(birth, ay.Ayanamsa(args.ayanamsa))

    off = birth.utc_offset.total_seconds() / 3600.0
    print(f"\nBirth   : {birth.when}  ({birth.zone.key}, UTC{off:+.2f})")
    print(f"UTC     : {birth.utc:%Y-%m-%d %H:%M:%S}")
    print(f"Place   : {birth.latitude:.4f}, {birth.longitude:.4f}")
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

    print(f"\n{draw_south_indian(chart, args.lang)}\n")


if __name__ == "__main__":
    main()
