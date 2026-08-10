# Testing guides, by phase

Each build phase gets its own testing guide, so you always know what is testable
now and what is still ahead. Start with the phase you just finished.

| Phase | Guide | What it verifies | Status |
|---|---|---|---|
| 0 + 0.5 | [phase-0.md](phase-0.md) | Ephemeris, ayanamsa, grahas, lagna, nakshatra & pada, place search, timezones | ✅ done |
| 1a | [phase-1a.md](phase-1a.md) | Divisional charts (D9 Navamsam and the Shodashavarga), AM/PM birth-time entry | ✅ done |
| 1b | [phase-1b.md](phase-1b.md) | FastAPI service, Next.js PWA, South Indian chart as SVG, place autocomplete | ✅ done |
| 1c | [phase-1c.md](phase-1c.md) | Saved chart library, A4 export, light/dark theme | ✅ done |
| 2 | [phase-2.md](phase-2.md) | Vimshottari dasha to five levels, Tamil panchangam, rahu kalam, gowri windows, nalla neram | ✅ done |
| 3 | *not yet built* | KP: 249 sub-lords, Placidus cusps, significators, ruling planets, horary | ⏳ |
| 4 | *not yet built* | 10 poruthams, 36-guna comparison, doshams and parihara | ⏳ |
| 5 | *not yet built* | Explainable predictions: the YAML rule base and the "why" panel | ⏳ |
| 6 | *not yet built* | PWA: offline, installability, Tamil fonts, PDF export | ⏳ |

## Not phase-specific

- **[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** — setup problems, common
  errors, and what to check when a chart disagrees with another program. Look
  here first when something breaks.
- **[../ARCHITECTURE.md](../ARCHITECTURE.md)** — why the stack is what it is.

## How to run everything at once

The engine, from `services/jyotish` with the virtualenv activated:

```bash
python -m pytest tests\ -q
```

The web app, from `apps/web`:

```bash
npm test
npm run build
```

`npm run build` counts as a test: `next dev` tolerates type errors that a
production build rejects.

**621 Python tests (~15s) and 69 TypeScript tests (<1s).** Every phase's automated tests live in the same
suite and all of them must pass — a later phase is never allowed to break an
earlier one. The Phase 0 accuracy gate in particular is load-bearing: if those
fail, nothing built on top of them can be trusted.

There should be **zero skips**. A skipped test is a test that is not protecting
you: `jyotishganit` once went undeclared, and the resulting module-level skip
quietly removed 73 varga tests while the suite still reported success. `-ra` is
on by default so skips can never be invisible again.
