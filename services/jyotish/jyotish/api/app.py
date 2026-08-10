"""The HTTP layer.

    uvicorn jyotish.api.app:app --reload

Two deliberate choices, both from docs/ARCHITECTURE.md:

* **Every compute route is `def`, not `async def`.** Chart computation is
  CPU-bound NumPy work through Skyfield. An `async def` route runs on the event
  loop, so one chart request would block every other request for its duration.
  FastAPI runs plain `def` routes in a threadpool, which is what this workload
  wants. This is the easiest thing here to get wrong and the most expensive.
* **The ephemeris is warmed at startup.** Loading DE440s costs a second or so;
  paying it inside the first user's request makes the app feel broken.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core import places as places_db
from ..core.birthdata import parse_time
from ..store import records as store
from . import models, service

log = logging.getLogger("jyotish.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Touch both data sources now so the first request is fast and, more
    # importantly, so a missing kernel or unbuilt place index fails at startup
    # where it is obvious rather than mid-request.
    from ..core.ephemeris import get_kernel, get_timescale

    get_timescale()
    get_kernel()
    log.info("ephemeris warm")

    try:
        log.info("place index: %s places", f"{places_db.count():,}")
    except places_db.PlacesDatabaseMissing as exc:
        log.warning("place search unavailable: %s", exc)

    yield


app = FastAPI(
    title="AstroApp Jyotish API",
    version=service.ENGINE_VERSION,
    summary="Vedic astrology chart computation, Tamil-native.",
    lifespan=lifespan,
)

# The PWA is served from a different origin, so every non-simple request is
# preflighted. This list must cover every method the API actually exposes:
# PUT and DELETE were missing when the library was added, and the browser
# rejected them at the preflight with no request ever reaching a route. The
# Python tests could not see it -- TestClient is same-process and never sends
# a preflight -- so "Update saved chart" and Delete were dead in the browser
# with a fully green suite.
#
# max_age is deliberately short. Browsers cache a preflight *result* per method,
# and Starlette's 600-second default means a rejection outlives the fix for ten
# minutes -- the API answers preflights correctly while the browser keeps
# refusing from cache, which reads exactly like the fix not working.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=60,
)


@app.exception_handler(Exception)
async def unhandled(_request: Request, exc: Exception) -> JSONResponse:
    """Turn any unhandled exception into structured JSON.

    Without this, FastAPI returns a bare ``text/plain`` "Internal Server Error",
    which the web client cannot parse into anything more useful than
    "Request failed (500)". The message deliberately names the exception type
    but not its arguments, which can carry absolute paths.

    This is a backstop, not a substitute for validating at the model boundary --
    every case reachable by a real request should already be a 4xx before it
    gets here.
    """
    log.exception("unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                f"The engine hit an unexpected {type(exc).__name__}. "
                "This is a bug; the server log has the details."
            )
        },
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine_version": service.ENGINE_VERSION}


@app.get("/api/meta", response_model=models.MetaResponse)
def meta() -> models.MetaResponse:
    """Ayanamsas, vargas, and the full Tamil lexicon.

    Lets a client build its own selectors and render Tamil names without
    shipping a second copy of the lexicon that could drift from this one.
    """
    return service.metadata()


@app.get("/api/places", response_model=models.PlacesResponse)
def search_places(
    q: str = Query(min_length=1, max_length=120, description="Latin or Tamil script"),
    limit: int = Query(default=10, ge=1, le=50),
    country: str | None = Query(default=None, min_length=2, max_length=2),
) -> models.PlacesResponse:
    """Birth-place autocomplete.

    `limit` is bounded by the signature rather than trusted: it reaches SQL, and
    SQLite treats a negative LIMIT as unbounded.
    """
    try:
        results = places_db.search(q, limit=limit, country=country)
    except places_db.PlacesDatabaseMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return models.PlacesResponse(
        query=q, results=[service.place_out(p) for p in results]
    )


# --- the chart library -------------------------------------------------------
#
# Records store the birth *inputs* plus the resolved place. Computed charts are
# deliberately not stored: a chart is a pure function of its inputs and the
# engine version, so caching one would only create a second thing that can go
# stale. Opening a saved record re-casts it at whatever accuracy the engine has
# now, which means a correctness fix reaches every saved chart for free.


def _record_out(record: store.BirthRecord) -> models.RecordOut:
    return models.RecordOut(
        id=record.id,
        name=record.name,
        notes=record.notes,
        birth_date=record.birth_date,
        birth_time=record.birth_time,
        fold=record.fold,
        ayanamsa=record.ayanamsa,
        latitude=record.latitude,
        longitude=record.longitude,
        timezone_name=record.timezone_name,
        place_name=record.place_name,
        geonameid=record.geonameid,
        vargas=record.vargas,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _to_store(body: models.RecordIn, record_id: int | None = None) -> store.BirthRecord:
    return store.BirthRecord(
        id=record_id,
        name=body.name,
        notes=body.notes,
        birth_date=body.birth_date.isoformat(),
        birth_time=body.birth_time,
        fold=body.fold,
        ayanamsa=body.ayanamsa,
        latitude=body.latitude,
        longitude=body.longitude,
        timezone_name=body.timezone_name,
        place_name=body.place_name,
        geonameid=body.geonameid,
        vargas=body.vargas,
    )


@app.get("/api/records", response_model=models.RecordsResponse)
def list_records(
    q: str = Query(default="", max_length=120, description="Filter by name or place"),
    limit: int = Query(default=100, ge=1, le=500),
) -> models.RecordsResponse:
    # A row that cannot be rendered is skipped, not fatal. Belt and braces: the
    # cause of that happening -- output models re-applying input rules -- is
    # fixed at the model level, but one corrupt or future-incompatible row must
    # never hide every other saved chart behind a 500.
    out = []
    for record in store.list_records(q, limit=limit):
        try:
            out.append(_record_out(record))
        except Exception:
            log.exception("skipping unreadable record %s", record.id)
    return models.RecordsResponse(records=out, total=store.count())


@app.post("/api/records", response_model=models.RecordOut, status_code=201)
def create_record(body: models.RecordIn) -> models.RecordOut:
    try:
        # Parse the time here so a bad value is rejected on save rather than
        # becoming a record that cannot be opened.
        parse_time(body.birth_time)
        return _record_out(store.save(_to_store(body)))
    except (ValueError, store.LibraryError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/records/{record_id}", response_model=models.RecordOut)
def get_record(record_id: int) -> models.RecordOut:
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No saved record {record_id}.")
    return _record_out(record)


@app.put("/api/records/{record_id}", response_model=models.RecordOut)
def update_record(record_id: int, body: models.RecordIn) -> models.RecordOut:
    if store.get(record_id) is None:
        raise HTTPException(status_code=404, detail=f"No saved record {record_id}.")
    try:
        parse_time(body.birth_time)
        return _record_out(store.save(_to_store(body, record_id)))
    except (ValueError, store.LibraryError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/records/{record_id}", status_code=204)
def delete_record(record_id: int) -> None:
    if not store.delete(record_id):
        raise HTTPException(status_code=404, detail=f"No saved record {record_id}.")


@app.post("/api/chart", response_model=models.ChartResponse)
def compute_chart(request: models.ChartRequest) -> models.ChartResponse:
    """Cast a chart.

    `def`, not `async def` -- see the module docstring.
    """
    try:
        return service.compute_chart(request)
    except places_db.PlacesDatabaseMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        # Bad input: an unreadable time, an unknown varga, a missing place.
        # 422 keeps it distinct from a genuine server fault.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
