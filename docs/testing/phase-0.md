# Testing guide

How to check that this engine is telling the truth — automatically, and by hand
against software a practising astrologer already trusts.

The guiding principle: **for our audience, a wrong chart is worse than no
chart.** A consumer app can survive a rough prediction. An astrologer who spots
one wrong nakshatra pada will never open the app again. So accuracy is tested
first, before anything is built on top of it.

---

## 1. What you can test today

| Area | Status |
|---|---|
| Ayanamsa (4 systems) | ✅ testable |
| Graha longitudes, lagna, rasi, nakshatra, pada | ✅ testable |
| Retrogradation | ✅ testable |
| Place search, incl. Tamil script | ✅ testable |
| Timezones, historical offsets, DST edge cases | ✅ testable |
| Divisional charts (D2–D60) | ⏳ Phase 1 |
| Vimshottari dasha | ⏳ Phase 2 |
| Panchangam, rahu kalam, nalla neram | ⏳ Phase 2 |
| KP sub-lords, ruling planets, horary | ⏳ Phase 3 |
| Porutham, doshams | ⏳ Phase 4 |
| Predictions | ⏳ Phase 5 |

There is no web UI yet — everything is exercised through `scripts/chart.py`.

## 2. Setup

**Activating the virtualenv is step one, not an optional nicety.** Skip it and
`python` means your *system* interpreter, which has none of the dependencies —
and the resulting `ModuleNotFoundError: No module named 'skyfield'` says nothing
about the real cause.

```bash
cd services\jyotish
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-dev.txt
```

| Shell | Activate with |
|---|---|
| cmd.exe | `.venv\Scripts\activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| Git Bash | `source .venv/Scripts/activate` |
| macOS / Linux | `source .venv/bin/activate` |

Your prompt should now begin with `(.venv)`. Confirm the environment:

```bash
python -c "import skyfield, timezonefinder; print('ok')"
```

Then build the place index — data artifacts are downloaded, never committed:

```bash
python scripts\build_places_db.py
```

That fetches GeoNames and builds `data/places.sqlite` (~98 MB, 786,101 places).
The DE440s ephemeris kernel (~31 MB) downloads automatically on first chart.

> `build_places_db.py` uses only the standard library, so it will happily run
> under the wrong interpreter and *appear* to prove your setup is fine. It is
> not evidence either way — trust the `import skyfield` check above.

## 3. Running the automated suite

```bash
python -m pytest tests\ -q
```

**Expect 164 passing, roughly 60–90 seconds.** Breakdown:

- `tests/validation/test_ayanamsa_vs_swisseph.py` — 4 ayanamsa systems × 8 epochs
- `tests/validation/test_positions_vs_swisseph.py` — 20 birth charts, every graha
- `tests/test_places.py` — search ranking, Tamil script, timezone agreement
- `tests/test_timezones.py` — historical offsets and DST edge cases

Useful variations:

```bash
python -m pytest tests\validation -q             # accuracy gate only
python -m pytest tests\ -q -k tamil              # one topic
python -m pytest tests\ -v -k chennai            # see individual fixture names
```

If `tests/test_places.py` reports **skipped**, the place index has not been
built. That is expected on a fresh clone.

## 4. What the tolerances mean

Everything is compared against **pyswisseph**, an independent implementation
used purely as an oracle. It is a dev dependency, never shipped.

| Quantity | Gate | Actual worst |
|---|---|---|
| Ayanamsa — Lahiri, KP, Raman | 1.0″ | **0.004″** |
| Ayanamsa — True Chitrapaksha | 0.5″ | 0.27″ |
| Graha longitudes (not Moon) | 1.0″ | **0.82″** |
| Moon | 3.0″ | ~2.0″ |
| Lagna | 1.0″ | **0.004″** |
| Nakshatra & pada | exact | exact |

### Why the Moon gets a looser gate

Not because our Moon is worse — because **the oracle's is**.

`pyswisseph` ships without its `.se1` data files, so it silently falls back to
Moshier's analytical theory, which is accurate to only ~1–3″ for the Moon. Our
DE440s figure is sub-arcsecond. Where the two disagree on the Moon, **we are the
more accurate source.**

This is pinned by `test_oracle_backend_is_declared`, which asserts the fallback
is in effect. If someone later installs the real Swiss ephemeris files, that
test fails loudly and `MOON_TOLERANCE_ARCSEC` should be tightened to 1.0.

For a genuine sub-arcsecond lunar check, use Jagannatha Hora — see next section.

### Putting arcseconds in perspective

A nakshatra pada is 3°20′ = 12,000″. Our worst graha deviation of 0.82″ is
**0.007% of a pada.** Birth times are recorded to the minute at best, and one
minute of clock error moves the lagna by roughly 900″. The astronomy is far
below the noise floor of the input data — which is the point.

---

## 5. Cross-checking against Jagannatha Hora

This is the real test. Jagannatha Hora is free, bundles genuine Swiss ephemeris
files, and is what serious Jyotish practitioners actually use. If our output
matches JHora, the engine is trustworthy.

**Setup (once):**

1. Download Jagannatha Hora from [vedicastrologer.org](https://www.vedicastrologer.org/jh/).
2. `Preferences → Ayanamsa` → **Lahiri (Chitrapaksha)**.
3. `Preferences → Chart style` → **South Indian**.
4. `Preferences → Node type` → **Mean node** (we use mean; see below).

**Comparing a chart:**

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1
```

Enter the same date, time and place in JHora, then compare:

| Check | Where in JHora |
|---|---|
| Lagna degree & nakshatra | main chart header |
| Each graha's degree-in-rasi | the planetary positions table |
| Nakshatra and pada for each graha | same table |
| Ayanamsa value | shown in the chart info panel |

**What counts as agreement:** degrees should match to the displayed precision
(typically arcseconds). **Padas must match exactly, with no exceptions.**

**Two settings that will produce false mismatches:**

- **True vs mean node.** We use the *mean* lunar node, as Vedic practice and KP
  both do. If JHora is set to true node, Rahu and Ketu will differ by up to
  about 1.5° — a real difference in convention, not an error.
- **Ayanamsa.** Lahiri and True Chitrapaksha differ by about 1′; KP differs from
  Lahiri by 5′49″. Confirm both sides use the same one.

Worth doing for at least two charts: one modern Indian birth, one diaspora birth
with daylight saving in play.

---

## 6. Manual checklist: place search and timezones

Run each of these and confirm the described behaviour.

### Place search

| # | Command | Expect |
|---|---|---|
| 1 | `--place "Chennai" --pick 1` | Chennai, Tamil Nadu, India — pop 4.6M, *not* a hamlet |
| 2 | `--place "மதுரை"` | Madurai — Tamil script resolves |
| 3 | `--place "கோயம்புத்தூர்"` | Coimbatore |
| 4 | `--place "Trichy" --pick 1` | Tiruchirappalli (pop 1M), not the pop-0 namesake |
| 5 | `--place "Madu"` | numbered list, **Madurai first** — not the pop-0 hamlet that matches exactly |
| 6 | `--place "Kumbakonam"` | resolves — small-town coverage |
| 7 | `--place "Zzzzqqqq"` | clean "no place matching" message, not a traceback |
| 8 | `--place "London"` | London UK ranked above London, Ontario |

### Timezone display

| # | Command | Expect in the `Offset` line |
|---|---|---|
| 9 | `--date 1990-05-15 --time 06:30 --place "Chennai" --pick 1` | `UTC+05:30`, no annotation |
| 10 | `--date 1943-03-12 --time 11:20 --place "Chennai" --pick 1` | `UTC+06:30  [wartime India, 1942-09-01 to 1945-10-15]` |
| 11 | `--date 1899-06-07 --time 09:30 --place "Chennai" --pick 1` | `UTC+05:21:10  [MMT, local mean time…]` |
| 12 | `--date 1988-07-21 --time 03:45 --place "London" --pick 1` | `UTC+01:00  [daylight saving in force…]` |
| 13 | add `--tz Asia/Singapore` to #9 | `UTC+08:00` — the override wins |

### Daylight-saving edge cases

| # | Command | Expect |
|---|---|---|
| 14 | `--date 1997-04-06 --time 02:30 --place "San Francisco" --pick 1` | ⚠ warning: **time does not exist** (clocks jumped forward) |
| 15 | `--date 2010-11-07 --time 01:30 --place "Trenton" --pick 1` | ⚠ warning: **occurs twice**, showing both offsets |
| 16 | same as #15 with `--fold 1` | uses `UTC-05:00` instead of `UTC-04:00` |

Case 15 is the one to understand: the two readings are an hour apart, which is
**about 15° of lagna** — often a different rasi entirely. The app must never
pick one silently.

### Does entering a place change the chart?

It must not — and this test proves it.

**The idea.** There are two ways to tell the app where someone was born:

```bash
--place "Chennai"                    # by name
--lat 13.0878 --lon 80.2785          # by coordinates
```

Typing a place name is only a *shortcut for looking up its coordinates*. Once
found, the engine does the identical calculation either way. So both commands
must produce exactly the same chart — same lagna, same graha degrees, same
padas.

**Why we test it.** Place search was added after the astronomy was already
validated. This test is the proof that adding it did not disturb anything. If it
ever fails, place lookup is feeding in different coordinates than it should —
which would mean charts silently changed depending on how the birth was entered.

**Run it:**

```bash
python -m pytest tests\test_places.py -q -k identical_charts
```

**A note if you compare by hand.** The CLI *displays* coordinates rounded to
four decimals, so if you copy the printed numbers into `--lat`/`--lon` you will
see a lagna about 0.04″ different. That is the rounding, not a bug: four decimal
places is about 11 metres, and 11 metres of ground is 0.04″ of ascendant. It is
a good demonstration of how little coordinate precision actually matters:

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1
python scripts\chart.py --date 1990-05-15 --time 06:30 --lat 13.0878 --lon 80.2785
```

The automated test is the authoritative one because it uses GeoNames'
full-precision coordinates, not the rounded display values.

---

## 7. Adding a birth chart to the test suite

Say you want the suite to check *your own* birth details every time it runs.
That takes one line.

### What a "fixture" is

A **fixture** here is just one birth record that the tests check. There are
currently 20 of them, listed in a Python list called `FIXTURES` in
`tests/validation/test_positions_vs_swisseph.py`.

Each one is a row of five values:

```python
("chennai-1990", datetime(1990, 5, 15, 6, 30), 13.0827, 80.2707, "Asia/Kolkata")
#      1                     2                     3         4          5
```

| # | Value | Meaning |
|---|---|---|
| 1 | `"chennai-1990"` | A short name, so you can tell which chart failed |
| 2 | `datetime(1990, 5, 15, 6, 30)` | Birth date and time: year, month, day, hour, minute — **24-hour clock** |
| 3 | `13.0827` | Latitude (negative for south) |
| 4 | `80.2707` | Longitude (negative for west) |
| 5 | `"Asia/Kolkata"` | Timezone name |

### The part that surprises people

**You do not write down what the chart should be.**

That feels wrong at first — surely a test needs an expected answer? But writing
expected degrees by hand would only test that we can copy numbers accurately.

Instead, each test takes your birth record and computes the answer **twice**:
once with our engine, and once with Swiss Ephemeris, a completely separate
implementation. Then it compares them. That is what "the oracle supplies the
expected values" means — the oracle is the second implementation, and it
produces the expected answer on the spot.

So you supply *a birth*, not *a chart*.

### Steps

1. Open `services/jyotish/tests/validation/test_positions_vs_swisseph.py`.
2. Find the list called `FIXTURES`.
3. Add a line in the same shape, before the closing `]`:

   ```python
   ("my-birth", datetime(1996, 11, 23, 14, 5), 9.9252, 78.1198, "Asia/Kolkata"),
   ```

   Note the trailing comma, and remember the hour is 24-hour — `14` is 2 PM.
4. Run the suite:

   ```bash
   python -m pytest tests\validation\test_positions_vs_swisseph.py -q
   ```

Your chart is now checked by all four tests automatically: graha longitudes, the
lagna, nakshatra and pada, and Ketu's opposition to Rahu. Nothing else to write.

To see your fixture by name:

```bash
python -m pytest tests\validation -v -k my-birth
```

### What makes a good addition

Fixtures earn their place by stressing something the others don't:

- a timezone with daylight saving, or an unusual historical offset
- a birth near midnight, where the date itself is in play
- a birth in the southern hemisphere, or at high latitude
- a graha sitting very close to a rasi or pada boundary

A twenty-first ordinary Indian daytime birth adds little; the twenty existing
ones already cover that.

## 8. Reading a failure

Four bug signatures already found in this codebase. The *shape* of an error
identifies its cause far faster than staring at the code:

| Signature | Cause |
|---|---|
| Every graha off by the **same constant** | Ayanamsa — wrong system, or wrong constant |
| Error **oscillates ±17″** across dates | Nutation — true vs mean equinox frame confusion |
| Error **scales with each body's speed** (Moon worst, Saturn least) | Time-scale error — UT1/UTC/TT, Delta-T, or timezone |
| Lagna off by **exactly 180°** | `atan2` argument signs |
| **One body** off, others fine | That body's target name or ephemeris source |
| Pada wrong but degree right | Boundary arithmetic in `zodiac.resolve()` |

The time-scale one is worth internalising: because the Moon moves ~0.55″ per
second of clock time and Saturn ~0.001″, dividing each body's error by its daily
motion should give the *same* number of seconds. When it does, you have a clock
problem, not an astronomy problem.

## 9. Known limitations

- **Date range: 1849–2150.** DE440s covers this. For charts outside it, set
  `ASTROAPP_EPHEMERIS=de440.bsp` (~114 MB, 1550–2650).
- **Mean lunar node only.** True node is not yet implemented.
- **Thirukanitham panchangam only.** Vakya is not implemented and is a research
  project in its own right — it is not derivable from a modern ephemeris.
- **Place coordinates are city-centre points.** GeoNames gives one coordinate
  per place; a birth across town differs by a few arcseconds of ascendant, far
  below birth-time precision. It does *not* matter for rectification work, where
  you should pass exact `--lat`/`--lon`.
- **The oracle is Moshier-backed** for the Moon — see §4.

---

**Next:** [phase-1a.md](phase-1a.md) covers the D9 Navamsam and divisional
charts. For anything that breaks, see
[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
