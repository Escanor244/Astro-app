# Phase 2 testing — dasha and panchangam

What Phase 2 added:

- **Vimshottari dasha** to five levels, with drill-down and a "what is running
  now" lookup.
- **The Tamil panchangam** — the five limbs with their ending times, rahu kalam,
  yamagandam, kuligai, the gowri windows, nalla neram, and the Tamil calendar
  date.
- **Learning docs**: [02-dasha.md](../02-dasha.md) and
  [03-panchangam.md](../03-panchangam.md), both from zero.

Prerequisite: [phase-1b.md](phase-1b.md) setup, both processes running.

> **Restart the engine.** Phase 2 adds `/api/dasha` and `/api/panchangam`, and an
> engine left running from an earlier session will 404 them while the page still
> loads. `/api/health` should report `engine_version: 2.0`.

---

## 1. Automated tests

```bash
cd services\jyotish && python -m pytest tests\ -q
```

```bash
cd apps\web && npm test && npm run build
```

**647 Python tests, 69 TypeScript tests, zero skips.**

Four deserve naming, because they cover things a green suite would otherwise
hide:

- `test_bhadra_falls_exactly_where_the_classical_rule_says` — the 60-slot karana
  map is irregular, and an offset of one slot is invisible everywhere except in
  where Bhadra lands.
- `test_every_gowri_sequence_is_a_rotation_of_its_declared_wheel` — re-derives
  all 112 gowri cells from the underlying rule. The table is stored literally so
  a Tamil reader can check it against an almanac; this is what catches a
  transcription slip in any one cell.
- `test_tithi_and_karana_do_not_depend_on_the_ayanamsa` and its complement — the
  algebra, asserted. Yoga is a *sum* of longitudes, so a tropical yoga is 48°
  wrong while looking entirely plausible.
- `test_the_vaara_takes_a_local_date_not_an_instant` — guards a bug that gave the
  right answer for India by coincidence and would have been wrong elsewhere.

## 2. Dasha

| # | Action | Expect |
|---|---|---|
| 1 | Cast a chart and scroll to **விம்சோத்தரி தசை** | Balance box, a running chain, and nine mahadashas |
| 2 | Check the balance against your own arithmetic | `(1 − fraction of the birth star crossed) × the lord's years` |
| 3 | Click any mahadasha row | Opens its nine antardashas; the breadcrumb gains a level |
| 4 | Keep clicking down | Five levels, then the arrow disappears |
| 5 | Click a breadcrumb entry | Walks back to that level |
| 6 | Check the first sub-period of any period | It is ruled by that period's **own** lord |
| 7 | Change the **Running on** date | The amber `now` row moves; the level you drilled to is kept |
| 8 | Set the date beyond 120 years from birth | "That date falls outside the 120-year cycle", not a wrong answer |

**Item 6 is the structural check.** Venus mahadasha opens with Venus–Venus. If
the first sub-period is Sun, the cycle has been rotated wrongly and every date
below it is wrong.

### Cross-checking against another program

Dates will differ from Jagannatha Hora or a Tamil site for reasons that are
mostly *not* bugs. Work down this list in order — it is repeated in
[02-dasha.md](../02-dasha.md) with the arithmetic:

1. **Ayanamsa** must match. Biggest single cause.
2. **Birth time**, including AM/PM and the offset actually applied. One hour of
   doubt moves a Saturn balance by about nine months.
3. **Dasha year length.** Out by ~10 months → the other program uses savana 360.
   Out by a day or less → one of the solar variants, and neither is wrong.
4. **Compare the Moon's longitude first.** A dasha date amplifies Moon error by
   about 548 days per degree, so if the Moons differ the dates were never going
   to agree.

## 3. Panchangam

| # | Action | Expect |
|---|---|---|
| 9 | Look at the **பஞ்சாங்கம்** panel | Tamil year, month, date, weekday; five limbs each with an "until" |
| 10 | Compare sunrise and sunset with a Tamil calendar for that place | Within a minute |
| 11 | Compare the eight **கௌரி பஞ்சாங்கம்** day windows | Names in the same order; times within a minute |
| 12 | Check rahu kalam against the weekday | Monday ≈ 07:30, Tuesday ≈ 15:00, Saturday ≈ 09:00 on a 6-to-6 day |
| 13 | Cast a birth between **midnight and sunrise** | The vaara is the **previous** day's, and every window follows it |
| 14 | Cast a birth above the Arctic Circle in June or December | An explanation, and no rahu kalam or gowri windows |
| 15 | Switch labels to **தமிழ்** | Limb names, gowri names and the kalams all in Tamil |

**Item 13 is the one to actually check.** The Jyotish day runs sunrise to
sunrise, so a 03:00 Tuesday birth is on Monday's vaara. Consumer apps get this
wrong constantly, and it shifts every window on the panel.

**Item 14 is the honest-failure check.** Rahu kalam is a fraction of the daylight
interval. During a polar night there is no such interval, so the correct output
is an explanation, not a fabricated 06:00 sunrise.

### The reference day

Monday 10 August 2026 at Chennai is checked automatically against Drik
Panchang's published values for all sixteen gowri windows. You can reproduce it:

```bash
python scripts\chart.py --date 2026-08-10 --time 12:00 --place "Chennai" --pick 1 --panchangam
```

Expect sunrise 05:55, sunset 18:32, ஆடி 25, பராபவ year, and the day windows
running அமிர்தம் · விஷம் · ரோகம் · லாபம் · தனம் · சுகம் · சோரம் · உத்தியோகம்.

## 4. CLI

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1 --dasha --panchangam
```

Useful flags: `--at 2030-01-01` for the running chain on another date,
`--dasha-year savana` to see the 360-day tradition, `--ayanamsa kp` to watch the
yoga and nakshatra move while the tithi and karana do not.

## 5. Known limitations

- **Only Vimshottari.** Ashtottari, Yogini and the conditional dashas are not
  implemented.
- **Thirukanitha only.** The Vakya (Pambu Panchangam) tradition is not computed;
  it can differ by hours on a limb ending and by a day on festivals. See
  [03-panchangam.md](../03-panchangam.md).
- **நல்ல நேரம் is the software definition** — the auspicious gowri windows. A
  printed tear-off calendar prints different bands under the same heading, and
  the panel says so.
- **No festivals, no muhurta search, no chandrashtamam.** The panchangam reports
  the day; it does not yet recommend one.
- **Sunrise is computed at sea level**, matching printed almanacs, which are
  published for a place rather than an altitude.
- **Dasha dates are not exported to the A4 sheet yet** — the sheet is still one
  chart per page.
