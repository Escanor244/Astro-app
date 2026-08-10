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
