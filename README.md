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

```bash
cd services/jyotish
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

Cast a chart:

```bash
python scripts/chart.py --date 1990-05-15 --time 06:30 --lat 13.0827 --lon 80.2707
```

The first run downloads the DE440s ephemeris kernel (~31 MB) into `data/`.
If your network blocks NASA's host, fetch it manually:

```bash
curl -o data/de440s.bsp https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp
```

Useful flags: `--ayanamsa {lahiri,true_chitrapaksha,kp,raman}`, `--lang {en,ta}`,
`--tz Asia/Kolkata` (otherwise derived from the coordinates).

## Running the accuracy gate

```bash
cd services/jyotish
.venv/Scripts/python.exe -m pytest tests/ -q
```

121 tests. These are not smoke tests — they compare every graha longitude,
the lagna, and every nakshatra pada against an independent Swiss Ephemeris
oracle across 20 birth charts. **If these fail, do not ship.** The target
audience includes practising astrologers, for whom one wrong pada is
disqualifying.

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
├─ services/jyotish/          Python engine
│  ├─ jyotish/core/
│  │  ├─ ephemeris.py         Skyfield/DE440s loading, licence rationale
│  │  ├─ ayanamsa.py          Lahiri, True Chitrapaksha, KP, Raman
│  │  ├─ birthdata.py         UT1 handling, historical timezones
│  │  ├─ positions.py         grahas, lagna, retrogradation
│  │  ├─ zodiac.py            rasi/nakshatra data + Tamil lexicon
│  │  └─ angles.py            normalisation, DMS formatting
│  ├─ scripts/chart.py        CLI jathagam
│  └─ tests/validation/       the accuracy gate
├─ docs/                      learning path (start at 00-orientation.md)
└─ data/                      DE440s kernel (gitignored)
```

Two languages is deliberate: Python owns the astronomy (Skyfield and
`jyotishganit` have no serious JS equivalent), Next.js will own the PWA.

## Build phases

- [x] **Phase 0 — Accuracy foundation.** Ephemeris, ayanamsa, grahas, lagna,
      pada, and the validation harness. *Gate met.*
- [ ] **Phase 1 — Core jathagam.** South Indian SVG chart, D1–D60 vargas,
      dignity, combustion, geocoding UI.
- [ ] **Phase 2 — Dasha & Panchangam.** Vimshottari to 5 levels; Tamil
      panchangam, rahu kalam, nalla neram.
- [ ] **Phase 3 — KP module.** 249 sub-lords, Placidus cusps, significators,
      ruling planets, horary. Paired with `docs/04-kp-system.md`.
- [ ] **Phase 4 — Tamil compatibility.** 10 poruthams, doshams with parihara.
- [ ] **Phase 5 — Explainable predictions.** YAML rule base, "why" panel.
- [ ] **Phase 6 — PWA polish.** Offline, Tamil fonts, PDF export.

## Learning path

You are learning Jyotish while building this, so `docs/` is a deliverable, not
an afterthought. Start at [docs/00-orientation.md](docs/00-orientation.md).

Reference texts worth having alongside: B.V. Raman, *Hindu Predictive
Astrology*; K.S. Krishnamurti, *Readers 1–6* (the primary KP source); and
Jagannatha Hora's bundled help, which is excellent and free.
