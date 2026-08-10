# AstroApp — Tamil-native Vedic astrology

A Jyotish engine and (soon) PWA built around three commitments:

1. **Vedic, not Western.** Sidereal zodiac, grahas, nakshatras, dashas, and the
   South Indian square chart as the *primary* view — not a display toggle.
2. **Tamil-native.** Tamil terminology is first-class in the data model, not a
   translation layer added later.
3. **Show your work.** Every future prediction will cite the classical rule and
   the exact placement that triggered it. No unsourced assertions.

**Status: Phase 0 complete.** The astronomy is built and validated. There is no
UI yet — that is Phase 1. See [the build plan](#build-phases) below.

---

## Quick start

**Activate the virtualenv first.** Every command below assumes it — without it,
`python` is your system interpreter, which does not have the dependencies.

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

If PowerShell refuses to run the activation script:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

**Check it worked** — your prompt should now start with `(.venv)`:

```bash
python -c "import skyfield, timezonefinder; print('ok')"
```

Build the place index once (~98 MB, 786,101 places):

```bash
python scripts\build_places_db.py
```

Cast a chart:

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1
```

Add the Navamsam (நவாம்சம்) beside the Rasi chart:

```bash
python scripts\chart.py --date 1990-05-15 --time "6:30 AM" --place "Chennai" --pick 1 --varga d1,d9
```

Tamil script works as input — `--place "மதுரை"` resolves to Madurai. The first
chart also downloads the DE440s ephemeris kernel (~31 MB) into `data/`. If your
network blocks NASA's host, fetch it manually:

```bash
curl -o data/de440s.bsp https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp
```

### Or use the web app

Two processes — the engine serves JSON, the web app serves the UI.

```bash
cd services\jyotish && .venv\Scripts\activate && python -m uvicorn jyotish.api.app:app --reload
```

```bash
cd apps\web && npm install && npm run dev
```

Then open <http://localhost:3000>. Interactive API docs are at
<http://127.0.0.1:8000/docs>.

### CLI flags

Useful flags: `--varga d1,d9` or `--varga all` for divisional charts,
`--ayanamsa {lahiri,true_chitrapaksha,kp,raman}`, `--lang {en,ta}`,
`--tz Asia/Kolkata` to override the zone, `--fold 1` for the second occurrence of
a repeated hour, and `--lat`/`--lon` for exact coordinates instead of a place.

**Birth time is 24-hour by default**, so `06:30` is the morning and `18:30` the
evening. `"6:30 PM"` works too, and the output always echoes back which one it
understood — an AM/PM slip moves the lagna about 180°.

### Place entry and timezones

Birth data is entered by place name, because nobody knows the latitude of the
village they were born in. Coverage is GeoNames `cities500` worldwide *plus every
Indian populated place*, so Tamil Nadu villages resolve rather than forcing users
back to coordinates. It is fully offline: no API key, no network on the input
path, and GeoNames supplies the IANA timezone for each place directly.

The offset actually applied is always shown, and annotated when it is not the one
you would expect:

```
Offset  : UTC+06:30   [wartime India, 1942-09-01 to 1945-10-15]
Offset  : UTC+05:21:10 [MMT, local mean time before standard zones were adopted]
```

Daylight-saving edge cases are surfaced rather than guessed. A local time that
never happened (clocks jumped forward) or happened twice (clocks went back) both
raise a warning — an hour of ambiguity is roughly **15° of lagna**, frequently a
different rasi.

## Running the accuracy gate

With the venv activated (see [Quick start](#quick-start)):

```bash
python -m pytest tests\ -q
```

441 tests, about 10 seconds. These are not smoke tests — they compare every
graha longitude, the lagna, and every nakshatra pada against an independent
Swiss Ephemeris oracle across 23 birth charts, cross-check all sixteen
divisional charts against a second implementation, and verify the lagna is
genuinely *rising* by computing its altitude a minute later rather than trusting
any reference. **If these fail, do not ship.** The target audience includes
practising astrologers, for whom one wrong pada is disqualifying.

**[docs/testing/](docs/testing/)** holds a testing guide per phase — what the
tolerances mean, manual checklists, and how to cross-check against Jagannatha
Hora. **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** is the place to
look when something breaks.

---

## Why not Swiss Ephemeris?

It is the obvious choice and we deliberately did not take it.

Swiss Ephemeris is dual-licensed AGPL-3.0 or commercial. Under AGPL §13,
serving it over a network obliges you to publish the full source of the
surrounding application — self-hosting does not avoid this. The commercial
escape is a Professional Licence at **CHF 750** (~₹78,000), one-time.

So the engine is built on **Skyfield (MIT)** with **NASA JPL DE440s** kernels
(public domain): equivalent sub-arcsecond accuracy, no licence encumbrance, no
cost. `pyswisseph` appears only in `requirements-dev.txt` and is imported only
by tests, which are never distributed.

## How accurate is it, really?

Measured against the oracle across 20 charts spanning 1899–2018:

| Quantity | Worst deviation |
|---|---|
| Ayanamsa (Lahiri / KP / Raman) | **0.004 arcsec** |
| Ayanamsa (True Chitrapaksha) | 0.27 arcsec |
| Graha longitudes (excluding Moon) | **0.82 arcsec** |
| Lagna | **0.004 arcsec** |
| Nakshatra & pada | exact match, 100% |

One caveat stated plainly: `pyswisseph` ships without its `.se1` data files, so
it silently falls back to Moshier's analytical theory, which is only ~1–3 arcsec
accurate for the Moon. Where our Moon disagrees with it by ~2 arcsec, **we are
the more accurate source** — DE440s is sub-arcsecond. A test
(`test_oracle_backend_is_declared`) pins this fact so it can never quietly
change. A true sub-arcsecond lunar cross-check needs Jagannatha Hora, which
bundles genuine Swiss ephemeris files.

### Four bugs the accuracy gate caught

Worth recording, because each is invisible without a reference implementation:

- **Historical civil time is UT1, not UTC.** Feeding a pre-1972 birth time
  through the TAI leap-second chain misdates it by 16 s in 1943 and **44 s in
  1900** — about 4 arcminutes of lagna, enough to change the rising sign near a
  boundary.
- **Ayanamsa is defined against the *mean* equinox.** Computing graha longitudes
  in the true (nutated) frame leaves a ±17 arcsec oscillation — exactly the
  amplitude of nutation in longitude.
- **The ascendant needs both frames.** Compute it in the true frame (which
  reproduces Swiss Ephemeris exactly), *then* rotate to the mean frame. Doing it
  directly in the mean frame leaves a few arcseconds, because obliquity enters
  the geometry rather than as an additive term.
- **`atan2` argument signs.** A plain arctangent puts the ascendant 180° out for
  half of all birth times.

---

## Architecture

```
AstroApp/
├─ apps/web/                  Next.js PWA
│  ├─ app/page.tsx            birth form + chart view
│  ├─ components/             SouthIndianChart (SVG), PlaceSearch, GrahaTable
│  └─ lib/                    typed API client, chart geometry + its tests
├─ services/jyotish/          Python engine
│  ├─ jyotish/api/            FastAPI service (models, service, app)
│  ├─ jyotish/core/
│  │  ├─ ephemeris.py         Skyfield/DE440s loading, licence rationale
│  │  ├─ ayanamsa.py          Lahiri, True Chitrapaksha, KP, Raman
│  │  ├─ birthdata.py         UT1 handling, historical timezones, DST folds
│  │  ├─ places.py            offline place search, Tamil script
│  │  ├─ positions.py         grahas, lagna, retrogradation
│  │  ├─ zodiac.py            rasi/nakshatra data + Tamil lexicon
│  │  └─ angles.py            normalisation, DMS formatting
│  ├─ jyotish/charts/vargas.py    D9 Navamsam + the Shodashavarga
│  ├─ scripts/chart.py        CLI jathagam
│  ├─ scripts/build_places_db.py   GeoNames -> SQLite index
│  └─ tests/                  accuracy gate, vargas, places, timezones
├─ docs/
│  ├─ 00-orientation.md       learning path
│  ├─ ARCHITECTURE.md         stack decisions and rationale
│  ├─ TROUBLESHOOTING.md      when something breaks
│  └─ testing/                one testing guide per phase
└─ data/                      DE440s kernel, places index (both gitignored)
```

Two languages is deliberate: Python owns the astronomy (Skyfield and
`jyotishganit` have no serious JS equivalent), Next.js will own the PWA.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full reasoning.

## Build phases

- [x] **Phase 0 — Accuracy foundation.** Ephemeris, ayanamsa, grahas, lagna,
      pada, and the validation harness. *Gate met.*
- [x] **Phase 0.5 — Place search & timezones.** Offline GeoNames index with
      Tamil script, historical offsets, DST edge cases.
- [x] **Phase 1a — Divisional charts.** D9 Navamsam and the full
      Shodashavarga; AM/PM birth-time entry.
- [x] **Phase 1b — API and web UI.** FastAPI service, Next.js PWA, South
      Indian chart as SVG, Tamil place autocomplete.
- [ ] **Phase 1c — Storage.** PostgreSQL, saved birth records, chart library.
- [ ] **Phase 2 — Dasha & Panchangam.** Vimshottari to 5 levels; Tamil
      panchangam, rahu kalam, nalla neram.
- [ ] **Phase 3 — KP module.** 249 sub-lords, Placidus cusps, significators,
      ruling planets, horary. Paired with `docs/04-kp-system.md`.
- [ ] **Phase 4 — Tamil compatibility.** 10 poruthams, doshams with parihara.
- [ ] **Phase 5 — Explainable predictions.** YAML rule base, "why" panel.
- [ ] **Phase 6 — PWA polish.** Offline, Tamil fonts, PDF export.

## Learning path

You are learning Jyotish while building this, so `docs/` is a deliverable, not
an afterthought. Start at [docs/00-orientation.md](docs/00-orientation.md), then
read [docs/ayanamsa.md](docs/ayanamsa.md) — the four ayanamsa systems, what they
are, and which to choose. It is the one setting where the wrong value produces a
chart that looks entirely normal and is wrong throughout.

Reference texts worth having alongside: B.V. Raman, *Hindu Predictive
Astrology*; K.S. Krishnamurti, *Readers 1–6* (the primary KP source); and
Jagannatha Hora's bundled help, which is excellent and free.

## Credits

Place data © [GeoNames](https://www.geonames.org/), licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Planetary ephemeris: NASA JPL DE440s (public domain).
Astronomy: [Skyfield](https://rhodesmill.org/skyfield/) (MIT).
