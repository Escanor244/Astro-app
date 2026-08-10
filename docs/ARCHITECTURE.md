# Architecture and stack decisions

Why the pieces are what they are. Written down once so the reasoning survives.

---

## Shape

```
Next.js PWA  ──HTTP/JSON──►  FastAPI  ──►  jyotish engine (Python)
  (Phase 1b)                              ├─ Skyfield + DE440s   (astronomy)
                                          └─ SQLite places index (geography)
```

One JSON API serves the web app now and any mobile client later. That is the
main reason for a standalone backend rather than putting the logic in Next.js
API routes: the astronomy is Python, and it should be written once.

## Python for the engine, TypeScript for the UI

Not a preference — a constraint. Skyfield and the JPL ephemeris tooling have no
serious JavaScript equivalent, and the accuracy work in Phase 0 depends on them.
Next.js owns the UI because that is where the UI ecosystem is.

The seam between them is a JSON API, so neither language leaks into the other.

## Backend: FastAPI

Already a dependency. Async-capable, Pydantic validation for free, and automatic
OpenAPI docs — which matter when a second client (mobile) arrives and needs to
know the contract.

Three optimisations specific to this workload:

**1. Chart endpoints must be `def`, not `async def`.**

This is the easiest thing to get wrong and the most expensive. Chart computation
is CPU-bound NumPy work. An `async def` endpoint runs on the event loop, so a
single chart request would block *every* other request for its duration. FastAPI
runs plain `def` endpoints in a threadpool automatically, which is what we want.

```python
@app.post("/chart")
def compute_chart(req: ChartRequest) -> ChartResponse:   # def, deliberately
    ...
```

**2. Warm the ephemeris at startup.**

Loading DE440s takes a second or so. Do it in a lifespan hook so the first user
request does not pay for it. `core/ephemeris.py` already caches at module level,
so this is one call at boot.

**3. Cache computed charts.**

Chart computation is a pure function of (UTC instant, latitude, longitude,
ayanamsa) — the same inputs always give the same chart, forever. That makes it
trivially cacheable. `functools.lru_cache` is enough to start; Redis only once
there are multiple worker processes worth sharing between.

Deploy with roughly one uvicorn worker per core. Each loads its own ephemeris,
but the kernel file is memory-mapped, so the OS page cache shares it.

## Databases

### SQLite for the place index — and it is the right tool, not a compromise

786,101 places, ~98 MB, **static and read-only**. It is rebuilt by
`scripts/build_places_db.py`, never written at runtime, and queried through
indexed prefix lookups that return in well under a millisecond.

Putting that in PostgreSQL would add a network round trip and a migration step
to gain nothing. SQLite here is an embedded index file, closer to a data asset
than a database.

### PostgreSQL when persistence arrives

Not yet needed — Phase 1 computes charts and stores nothing, by decision. When
saved charts, users and history do arrive, PostgreSQL over MySQL for one
concrete reason: **JSONB**. A computed chart is naturally a document (grahas,
lagna, sixteen vargas, later the dashas), and JSONB lets us store it whole,
index into it, and query fields without a migration every time the engine gains
a field.

The likely shape:

| Table | Holds |
|---|---|
| `users` | account records |
| `birth_records` | the *inputs*: name, datetime, place, timezone, fold |
| `charts` | computed output as JSONB, keyed by input hash + engine version |

Storing the input separately from the computed chart matters: when the engine
improves, charts can be recomputed from inputs that never change. And keying the
cache on an engine version means a fix like the navamsa boundary bug invalidates
stale results instead of silently serving them.

## What is deliberately not here yet

- **No auth.** Phase 1 is stateless.
- **No Redis.** Premature until there is measured contention.
- **No ORM.** Nothing to map yet; the choice can wait for a real schema.
- **No Docker.** Local development works with a venv and a script. Containers
  when there is somewhere to deploy to.

## Fixed decisions

These are settled and should not be relitigated without a specific reason:

| Decision | Why | Where |
|---|---|---|
| Skyfield + DE440s, not Swiss Ephemeris | Swiss Ephemeris is AGPL or CHF 750; serving AGPL over a network obliges publishing all source | [../README.md](../README.md) |
| Mean lunar node, not true | Vedic practice and KP both use mean | `core/positions.py` |
| Lahiri ayanamsa by default | India's official standard since 1955 | `core/ayanamsa.py` |
| South Indian chart is primary | The audience is Tamil; signs fixed, houses rotate | `scripts/chart.py` |
| Tamil is first-class in the data model | Not a translation layer bolted on later | `core/zodiac.py` |
| BPHS for D30, against the reference implementation | Even signs mirror odd signs; jyotishganit does not | [testing/phase-1a.md](testing/phase-1a.md) |
