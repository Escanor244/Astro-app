# Troubleshooting

Common problems and what they actually mean. Not tied to any one phase — check
here first when something breaks.

---

## Setup problems

Nearly all of these are one thing wearing different hats: **the virtualenv is
not activated.**

| Symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError: No module named 'skyfield'` (or `timezonefinder`) | System Python, not the venv. Activate it. The suite detects this and prints which interpreter it is using instead of a traceback. |
| `'.venv' is not recognized as an internal or external command` | Forward slashes on cmd.exe. Use `.venv\Scripts\...` with backslashes. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell execution policy: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`, then activate again. |
| `pip install` succeeded but imports still fail | Installed with one interpreter, running with another. Check `python -c "import sys; print(sys.executable)"` — it must be under `.venv`. |
| `ModuleNotFoundError: No module named 'jyotish'` | The engine package is not on `sys.path`. `scripts/chart.py` handles this itself and runs from any directory; a *new* script needs the same bootstrap at its top. |
| `... was unexpected at this time` | You pasted the `(.venv) C:\...>` prompt prefix along with the command. Copy only the part after `>`. |
| `PlacesDatabaseMissing` when using `--place` | Place index not built: `python scripts\build_places_db.py`. |
| `tests/test_places.py` all skipped | Same as above. Expected on a fresh clone. |
| Tamil script prints as `?????` | Console font, not encoding. Use Windows Terminal. Does not affect correctness. |
| `UnicodeEncodeError` when redirecting output | Fixed — `chart.py` now forces UTF-8 on stdout. Earlier versions died mid-chart on `chart.py ... > out.txt` and left a truncated file. If you see this, you are on an old build. |

### Activating the virtualenv

| Shell | Command |
|---|---|
| cmd.exe | `.venv\Scripts\activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| Git Bash | `source .venv/Scripts/activate` |
| macOS / Linux | `source .venv/bin/activate` |

Your prompt should then begin with `(.venv)`. Confirm with:

```bash
python -c "import skyfield, timezonefinder; print('ok')"
```

> **A trap worth naming.** Installing with an explicit interpreter path
> (`.venv\Scripts\python.exe -m pip install ...`) works, but every *later* bare
> `python` is then the system one. Activating once makes all of them correct.
>
> Also: `scripts\build_places_db.py` uses only the standard library, so it runs
> fine under the wrong interpreter and makes your setup *look* correct right
> before the next command fails. Its success proves nothing.

---

## Running tests

**`-k something` selected 0 tests.** Not a failure. `-k` filters by *test name*,
so `-k english` matches nothing because no test has "english" in its name. Try
`-k tamil`, `-k chennai`, `-k navamsa`, or run `--collect-only -q` to see the
names.

**A test is skipped.** Usually a missing build artifact. Place tests skip without
`data/places.sqlite`; the varga cross-check skips without `jyotishganit`.

---

## The chart looks wrong

Work down this list before suspecting the engine. All of these have bitten
someone already.

### It's off by about half the zodiac

**Check AM/PM.** A twelve-hour error moves the ascendant roughly 180°, so the
lagna lands in the opposite rasi and everything else follows. A bare `--time
06:30` is 06:30 in the *morning*; for an evening birth use `18:30` or
`"6:30 PM"`.

The output always echoes the 12-hour reading for exactly this reason:

```
Birth   : 1990-05-15  06:30:00  (6:30 AM)
```

### It's off by about one rasi

**Check the timezone**, especially for older or overseas births. The offset that
was actually applied is always printed, and annotated when it is unusual:

```
Offset  : UTC+06:30   [wartime India, 1942-09-01 to 1945-10-15]
```

India ran UTC+06:30 from 1942 to 1945, and Madras kept local mean time
(UTC+05:21:10) until 1906. Both are correct, not bugs. Override with `--tz` if
the birth record says otherwise.

### It's off by roughly an hour

**A daylight-saving ambiguity.** If a warning appeared saying the time occurs
twice, the two readings are an hour apart — about 15° of lagna. Pick the other
one with `--fold 1`.

### It disagrees with another astrology program

Check these three before assuming anyone is wrong. All are differences of
*convention*, not accuracy:

1. **Ayanamsa.** We default to Lahiri. True Chitrapaksha differs by about 1′, KP
   by 5′49″, and Raman by 1°26′. Compare like with like: `--ayanamsa kp`. See
   [ayanamsa.md](ayanamsa.md) for which to use and why.
2. **Mean vs true node.** We use the *mean* lunar node, as Vedic practice and KP
   both do. Software set to the true node puts Rahu and Ketu up to ~1.5° away.
3. **Chart style.** Ours is South Indian: signs are fixed in the grid, houses
   rotate. A North Indian chart holds houses fixed and moves the signs. Same
   information, opposite convention.

If all three match and the charts still differ by more than an arcsecond, that
is worth investigating — see "Reading a failure" in
[testing/phase-0.md](testing/phase-0.md).

### The Navamsam disagrees but the Rasi chart matches

Some programs compute D9 from a different starting-sign rule for even signs, and
D30 in particular is implemented inconsistently across software. Ours follows
Brihat Parashara Hora Shastra and is cross-checked against an independent
implementation — see [testing/phase-1a.md](testing/phase-1a.md), which documents
the one place we knowingly differ and why.

---

## The dasha looks wrong

### The dasha dates are out by days or weeks

Work down this list. A dasha date is the Moon's position inside its nakshatra
scaled up by the length of the period — about **548 days of date per degree of
Moon** for a 20-year Venus mahadasha — so small input differences become large
date differences. That is expected, not a bug.

1. **Compare the Moon's longitude first**, to the arcsecond. If the two Moons
   differ, the dates were never going to agree, and 548 days per degree tells you
   exactly how much difference to expect.
2. **Ayanamsa.** The realistic cause. 0.1° of ayanamsa is 55 days of a Venus
   balance.
3. **Birth time.** The Moon moves 0.55° an hour, so one hour of doubt moves a
   19-year Saturn balance by about **nine months**. Check the AM/PM reading the
   app echoes back, and any daylight-saving warning it showed.

### The dasha is out by roughly ten months

The other program is using the **savana** 360-day year. Ours defaults to the
classical 365¼. Try `--dasha-year savana` and see whether it lines up. Both
traditions are real; savana is not what Tamil almanacs print. See
[02-dasha.md](02-dasha.md).

### The dasha is out by a day or less

One of the solar year-length variants — julian, sidereal, gregorian, tropical.
They differ by under two days across a whole 120-year cycle and no practitioner
distinguishes them. Neither program is wrong.

### The second column is labelled differently from my book

Tamil usage is **தசை / புத்தி / அந்தரம் / சூட்சுமம் / பிராணன்**, and
"அந்தரம்" means level *three*. North Indian books call level two "antardasha".
Same arithmetic, shifted vocabulary. The app labels the Tamil column in the Tamil
convention.

---

## The panchangam looks wrong

### The weekday is a day earlier than my calendar

That is correct if the moment is between midnight and sunrise. The Jyotish day
runs **sunrise to sunrise**, so a 03:00 Tuesday birth falls on Monday's vaara —
and Monday's rahu kalam, Monday's gowri windows. Tamil almanacs are explicit
about this.

### Rahu kalam is not 90 minutes

It never was. It is one **eighth of the interval between sunrise and sunset**,
which is 90 minutes only on a day with exactly twelve hours of light. In Chennai
the eighth runs from about 85 to 95 minutes across the year; in London, 45 to
120. The familiar "07:30–09:00" is the idealised 6-to-6 teaching version.

### The tithi or nakshatra ending time is hours off a temple almanac

Tamil Nadu has two live traditions. We compute **திருக்கணித (Thirukanitha)** —
modern ephemeris, Lahiri ayanamsa — which is what software, the Rashtriya
Panchang and most practising astrologers use. **வாக்கிய (Vakya)**, as in the
Pambu Panchangam, uses Surya-Siddhanta mnemonic tables and can differ by several
hours on a limb ending and by a day on festivals. Neither is a bug.

### The yogam is completely different but the tithi matches

That is the signature of an **ayanamsa mismatch** in the other program. Tithi and
karana are *differences* of two longitudes, so the ayanamsa cancels and they
agree in any system. Yoga is a *sum*, so the ayanamsa enters twice — a tropical
yoga is about 48° out, three and a half yogas.

### நல்ல நேரம் does not match my wall calendar

Two different things share the name. On this app it is the **auspicious gowri
windows**, which is what panchangam software universally means. A printed
tear-off Tamil calendar prints fixed one-hour bands, and they are demonstrably
not the same windows — sample a week and you will find days where the printed
band lands on Soram or Rogam. See [03-panchangam.md](03-panchangam.md).

### No rahu kalam or gowri windows are shown at all

The place and date have no sunrise or sunset — a polar summer or winter. Those
windows are fractions of the daylight interval, so with no such interval they
have no definition. The app says so rather than inventing a 06:00 sunrise. The
five limbs are still shown; they are longitudes and do not depend on the horizon.

### The Tamil month has 29 or 32 days

Correct. A Tamil month is the Sun's residence in one rasi, and the Sun's speed
varies, so month lengths genuinely run from 29 to 32 days. In 2026–27, Karthigai
is 29 days and Aani is 32.

---

## The dasha or panchangam panel says the engine is unreachable

The engine was started before Phase 2 and does not have `/api/dasha` or
`/api/panchangam`. Restart it, then check:

```bash
curl http://127.0.0.1:8000/api/health
```

It should report `"engine_version":"2.0"`. An older value means an old process is
still holding the port.

---

## Data and downloads

**The ephemeris download stalls.** Fetch it manually:

```bash
curl -o data/de440s.bsp https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp
```

**A birth date is out of range.** DE440s covers **1849–2150**. For anything
outside that, set `ASTROAPP_EPHEMERIS=de440.bsp` (~114 MB, 1550–2650).

**Rebuilding the place index.** Delete `data/places.sqlite` and re-run
`python scripts\build_places_db.py`. Downloads are cached in
`data/geonames_cache/`; delete that too to force a fresh fetch.

**A birth village is missing.** The index covers every Indian populated place
plus worldwide places over 500 people, but GeoNames is not exhaustive. Search a
nearby town instead — a few kilometres shifts the ascendant by well under an
arcsecond — or pass `--lat`/`--lon` directly.
