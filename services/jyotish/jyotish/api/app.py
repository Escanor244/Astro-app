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

# The PWA is served from a different origin in development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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
