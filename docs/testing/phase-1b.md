# Phase 1b testing — the API and the web UI

What Phase 1b added:

- A **FastAPI service** exposing the engine as JSON.
- A **Next.js PWA** with the South Indian chart drawn as SVG, Tamil-native
  labels, and place autocomplete.

Prerequisite: [phase-0.md](phase-0.md) setup, with the virtualenv activated and
the place index built.

---

## 1. Running both halves

Two processes. The engine serves JSON on 8000; the web app serves the UI on 3000
and talks to the engine.

**Terminal one — the engine:**

```bash
cd services\jyotish
.venv\Scripts\activate
python -m uvicorn jyotish.api.app:app --reload
```

**Terminal two — the web app:**

```bash
cd apps\web
npm install
npm run dev
```

Then open <http://localhost:3000>.

If the UI reports "Cannot reach the engine", the first terminal is not running.
The message names the exact command to fix it.

Interactive API docs, generated from the code, are at
<http://127.0.0.1:8000/docs>.

## 2. Automated tests

```bash
cd services\jyotish
python -m pytest tests\ -q            # 475 tests, ~10 seconds
```

```bash
cd apps\web
npm test                              # 12 tests, under a second
npm run build                          # also type-checks the whole app
```

`npm run build` matters as a test: `next dev` tolerates type errors that a
production build rejects, so a green dev server is not evidence the app compiles.

### What the new tests cover

`tests/test_api.py` (34 tests) checks the contract, and the load-bearing one is
**`test_api_and_engine_agree_exactly`** — the API and a direct engine call must
produce bit-identical longitudes. They share the engine but reach it by
different routes (the API caches on a reconstructed UTC instant), and a
divergence would mean the web UI quietly showed a different chart from the one
you validated on the command line.

`apps/web/lib/chart-layout.test.ts` covers the chart geometry, which is the one
part of the UI that can be wrong *silently*: a South Indian chart with a rasi in
the wrong cell still looks like a perfectly good chart. The strongest assertion
there is that consecutive rasis are always in adjacent cells — an off-by-one
anywhere in the ring breaks adjacency somewhere, which a uniqueness check alone
would miss.

## 3. Manual checklist

### Place entry

| # | Action | Expect |
|---|---|---|
| 1 | Type `Madurai` | Dropdown appears; first hit is the city, with coordinates and timezone |
| 2 | Type `மதுரை` | Same result — Tamil script is a first-class input |
| 3 | Type `Hosur` | Displays `Hosūr`; retyping that accented name still finds it |
| 4 | Type quickly, then delete back | No stale list from a superseded request |
| 5 | Type a place, then edit the text | The **Cast chart** button reverts to "Choose a birth place" |
| 6 | Arrow keys, then Enter | Selects without touching the mouse |
| 7 | Type `Zzzzqqqq` | "No place matches" — not a spinner that never stops |

Item 5 is a correctness guard, not polish: a chart must never be cast against a
place the user has since typed away from.

### Charts

| # | Action | Expect |
|---|---|---|
| 8 | 1990-05-15, 06:30, Chennai, D1+D9 | Lagna Taurus 11°09'21.84", Rohini pada 1 |
| 9 | Same, check the grid | Mesham is always the second cell of the top row; the cell holding the lagna shows **ASC** and house 1 |
| 10 | Switch to **தமிழ்** | Rasi names, graha abbreviations and the lagna label all become Tamil |
| 11 | Select **Show all 16** | Sixteen charts, each with its Tamil name and meaning |
| 12 | Hover a graha row in the table | That graha highlights in the chart grid |
| 13 | Switch ayanamsa to **KP** | Every longitude shifts by the same ~5'49" |

Item 9 is the defining property of the South Indian chart: **the rasis never
move; the houses rotate.** That is the opposite of the North Indian diamond.

### Timezone and time

| # | Action | Expect |
|---|---|---|
| 14 | 1943-03-12, 11:20, Chennai | `UTC+06:30` with a "wartime India" note |
| 15 | 1899-06-07, 09:30, Chennai | `UTC+05:21:10` with a local-mean-time note |
| 16 | 2010-11-07, 01:30, Trenton NJ | Amber warning: the time occurred twice, with **Use the other reading** |
| 17 | Click **Use the other reading** | Chart recomputes an hour apart; the lagna moves ~15° |
| 18 | 1997-04-06, 02:30, San Francisco | Warning that the time never occurred |
| 19 | Any chart, check the header | Time echoed in 12-hour form, e.g. `06:30:00 (6:30 AM)` |

Item 19 exists because a 12-hour slip moves the lagna about 180°. The web form
uses a 24-hour picker, which removes the ambiguity at source, but the echo is
the user's confirmation that the engine read what they meant.

### Failure modes

| # | Action | Expect |
|---|---|---|
| 20 | Stop the engine, reload the page | Clear "Cannot reach the engine" with the command to start it — not a blank page |
| 21 | Stop the engine mid-session, cast a chart | Same, and the previous chart is not replaced by a broken one |
| 22 | Narrow the window to phone width | Form and charts stack; the graha table scrolls horizontally rather than overflowing |

## 4. Cross-checking the UI against the CLI

The UI and CLI must agree exactly. Cast the same birth both ways:

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1 --varga d1,d9
```

Compare every degree, nakshatra and pada. They share one engine, so a mismatch
means a bug in the API layer — which is exactly what
`test_api_and_engine_agree_exactly` exists to catch first.

## 5. Known limitations

- **Nothing is saved.** Phase 1b is stateless by decision; storage is Phase 1c.
- **No offline mode yet.** The PWA manifest is in place, but there is no service
  worker, so the app needs the engine running. Phase 6.
- **Desktop and Android are not packaged.** Browser only for now.
- **The engine binds to localhost.** It is a single-user local tool; there is no
  auth, and it should not be exposed to a network.
