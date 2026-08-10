"""The JSON API.

The load-bearing test here is that the API and the CLI produce *identical*
numbers. They share the engine, but they reach it by different paths -- the API
caches on a UTC instant reconstructed from the birth record -- and a divergence
would mean the web UI quietly showed a different chart from the one the user
validated on the command line.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jyotish.api import service
from jyotish.api.app import app
from jyotish.core import ayanamsa as ay
from jyotish.core import places as places_db
from jyotish.core import positions as pos

#: GeoNames' Chennai, deliberately -- these are the coordinates `--place
#: "Chennai"` resolves to, so the pinned chart below is exactly the one the user
#: verified against an online Tamil source. The commonly-quoted 13.0827/80.2707
#: is a different point ~800 m away and gives a lagna 35 arcsec earlier.
CHENNAI = {"latitude": 13.0878, "longitude": 80.2785, "timezone": "Asia/Kolkata"}

needs_places = pytest.mark.skipif(
    not places_db.DB_PATH.exists(),
    reason="place index not built; run scripts/build_places_db.py",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def chart(client, **overrides):
    body = {"date": "1990-05-15", "time": "06:30", **CHENNAI, **overrides}
    r = client.post("/api/chart", json=body)
    assert r.status_code == 200, r.text
    return r.json()


# --- the contract with the engine -------------------------------------------

def test_api_and_engine_agree_exactly(client) -> None:
    """Same birth, same numbers, to the last bit.

    Not an approximate comparison: the API must not introduce rounding or a
    different instant on its way through the cache.
    """
    from datetime import datetime

    from jyotish.core.birthdata import BirthData

    body = chart(client)
    direct = pos.compute(
        BirthData(
            when=datetime(1990, 5, 15, 6, 30),
            latitude=CHENNAI["latitude"], longitude=CHENNAI["longitude"],
            timezone_name=CHENNAI["timezone"],
        ),
        ay.Ayanamsa.LAHIRI,
    )

    assert body["lagna"]["longitude"] == direct.lagna.longitude
    for g in body["grahas"]:
        assert g["position"]["longitude"] == direct.grahas[g["graha"]].longitude
        assert g["retrograde"] == direct.grahas[g["graha"]].retrograde
        assert g["house"] == direct.house_of(g["graha"])


@needs_places
def test_the_verified_chart_is_unchanged(client) -> None:
    """The chart the user checked against an online Tamil source.

    Resolved through the place index rather than typed coordinates, because
    that is exactly how it was run (`--place "Chennai" --pick 1`). Typing the
    displayed 13.0878/80.2785 instead gives a lagna 0.04 arcsec different --
    four decimal places is about 11 metres of ground, and 11 metres is 0.04
    arcsec of ascendant. Harmless, but it would make an exact pin meaningless.
    """
    place = client.get("/api/places", params={"q": "Chennai", "limit": 1}).json()
    body = chart(
        client, geonameid=place["results"][0]["geonameid"],
        latitude=None, longitude=None, timezone=None, vargas=["D1", "D9"],
    )
    assert body["lagna"]["formatted"] == "11°09'21.84\""
    assert body["lagna"]["rasi_name"]["en"] == "Taurus"
    assert body["lagna"]["rasi_name"]["ta"] == "ரிஷபம்"
    assert body["lagna"]["nakshatra_name"]["en"] == "Rohini"
    assert body["lagna"]["pada"] == 1
    assert body["ayanamsa_formatted"] == "23°43'21.12\""

    moon = next(g for g in body["grahas"] if g["graha"] == 1)
    assert moon["position"]["rasi_name"]["en"] == "Sagittarius"
    assert moon["position"]["nakshatra_name"]["en"] == "Uttara Ashadha"
    assert moon["position"]["pada"] == 1


def test_caching_does_not_leak_between_requests(client) -> None:
    """Different ayanamsas must not collide in the chart cache."""
    lahiri = chart(client, ayanamsa="lahiri")
    kp = chart(client, ayanamsa="kp")

    shift = (kp["lagna"]["longitude"] - lahiri["lagna"]["longitude"]) % 360.0
    assert 0.08 < shift < 0.11, "KP/Lahiri separation is ~5'49\""
    assert lahiri["ayanamsa"] == "lahiri" and kp["ayanamsa"] == "kp"


def test_repeated_requests_are_identical(client) -> None:
    assert chart(client) == chart(client)


# --- birth data round-trip --------------------------------------------------

def test_birth_is_echoed_as_interpreted(client) -> None:
    body = chart(client)["birth"]
    assert body["time_12h"] == "6:30 AM"
    assert body["timezone"] == "Asia/Kolkata"
    assert body["utc_offset"] == "UTC+05:30"
    assert body["utc"].startswith("1990-05-15T01:00")
    assert body["offset_note"] is None


def test_twelve_hour_time_is_accepted(client) -> None:
    assert chart(client, time="6:30 AM") == chart(client, time="06:30")
    evening = chart(client, time="6:30 PM")
    assert evening["birth"]["time_12h"] == "6:30 PM"
    assert evening["lagna"]["rasi_name"]["en"] == "Scorpio"


def test_wartime_india_offset_is_reported(client) -> None:
    body = chart(client, date="1943-03-12", time="11:20")["birth"]
    assert body["utc_offset"] == "UTC+06:30"
    assert "wartime" in (body["offset_note"] or "")


def test_madras_local_mean_time_is_reported(client) -> None:
    body = chart(client, date="1899-06-07", time="09:30")["birth"]
    assert body["utc_offset"] == "UTC+05:21:10"
    assert "local mean time" in (body["offset_note"] or "")


# --- daylight-saving warnings must reach the client -------------------------

def test_nonexistent_time_warns(client) -> None:
    body = chart(
        client, date="1997-04-06", time="02:30",
        latitude=37.7749, longitude=-122.4194, timezone="America/Los_Angeles",
    )
    assert body["time_warning"] and "never occurred" in body["time_warning"]
    assert body["time_warning_kind"] == "nonexistent"


@pytest.mark.parametrize("fold", [0, 1])
def test_nonexistent_warning_states_the_offset_actually_used(client, fold: int) -> None:
    """The prose must not contradict the offset two rows above it.

    The message used to hardcode "the offset in force before the change", which
    is only true for fold=0. Under PEP 495 a fold of 1 in a gap selects the
    offset *after* the transition, so the same sentence was attached to two
    charts an hour apart, one of them falsely.
    """
    body = chart(
        client, date="1997-04-06", time="02:30", fold=fold,
        latitude=37.7749, longitude=-122.4194, timezone="America/Los_Angeles",
    )
    assert body["birth"]["utc_offset"] in body["time_warning"]
    assert "before the change" not in body["time_warning"]


def test_nonexistent_time_offers_no_second_reading(client) -> None:
    """A time that never happened has exactly one interpretation.

    The UI keys its "Use the other reading" button off this field, so labelling
    a gap time "ambiguous" would invite the user into a choice that is not real.
    """
    args = dict(date="1997-04-06", time="02:30", latitude=37.7749,
                longitude=-122.4194, timezone="America/Los_Angeles")
    assert chart(client, **args, fold=0)["time_warning_kind"] == "nonexistent"
    assert chart(client, **args, fold=1)["time_warning_kind"] == "nonexistent"


def test_ambiguous_time_warns_and_fold_switches_it(client) -> None:
    args = dict(date="2010-11-07", time="01:30", latitude=40.2171,
                longitude=-74.7429, timezone="America/New_York")
    first = chart(client, **args, fold=0)
    second = chart(client, **args, fold=1)

    assert first["time_warning"] and "occurred twice" in first["time_warning"]
    assert first["time_warning_kind"] == "ambiguous"
    assert first["birth"]["utc_offset"] == "UTC-04:00"
    assert second["birth"]["utc_offset"] == "UTC-05:00"
    assert first["lagna"]["longitude"] != second["lagna"]["longitude"]


def test_ordinary_birth_has_no_warning(client) -> None:
    assert chart(client)["time_warning"] is None


# --- vargas -----------------------------------------------------------------

def test_default_is_the_rasi_chart_only(client) -> None:
    charts = chart(client)["charts"]
    assert [c["code"] for c in charts] == ["D1"]


def test_navamsam_is_returned_with_tamil_name(client) -> None:
    d9 = next(c for c in chart(client, vargas=["D1", "D9"])["charts"] if c["code"] == "D9")
    assert d9["name"]["ta"] == "நவாம்சம்"
    assert d9["divisions"] == 9
    assert len(d9["graha_rasis"]) == 9
    assert 0 <= d9["lagna_rasi"] <= 11


def test_all_sixteen_vargas(client) -> None:
    from jyotish.charts import vargas

    body = chart(client, vargas=list(vargas.VARGA_ORDER))
    assert [c["code"] for c in body["charts"]] == list(vargas.VARGA_ORDER)


def test_varga_codes_are_case_insensitive(client) -> None:
    assert [c["code"] for c in chart(client, vargas=["d9"])["charts"]] == ["D9"]


def test_d1_varga_matches_the_graha_table(client) -> None:
    """The chart grid and the table must not disagree with each other."""
    body = chart(client)
    d1 = body["charts"][0]
    assert d1["lagna_rasi"] == body["lagna"]["rasi"]
    for g in body["grahas"]:
        assert d1["graha_rasis"][str(g["graha"])] == g["position"]["rasi"]


# --- validation -------------------------------------------------------------

@pytest.mark.parametrize("bad_time", ["13:30 PM", "25:00", "six thirty", "630", ""])
def test_bad_time_is_422(client, bad_time: str) -> None:
    r = client.post("/api/chart",
                    json={"date": "1990-05-15", "time": bad_time, **CHENNAI})
    assert r.status_code == 422


def test_unknown_varga_is_422(client) -> None:
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30",
                                        **CHENNAI, "vargas": ["D5"]})
    assert r.status_code == 422
    assert "D5" in r.json()["detail"]


def test_missing_location_is_422(client) -> None:
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30"})
    assert r.status_code == 422


def test_out_of_range_latitude_is_rejected(client) -> None:
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30",
                                        "latitude": 95.0, "longitude": 80.0})
    assert r.status_code == 422


@pytest.mark.parametrize(
    "zone", ["Not/AZone", "IST", "asia/kolkata", "Asia/Chennai", "GMT+5:30"]
)
def test_unknown_timezone_is_422_not_500(client, zone: str) -> None:
    """ZoneInfoNotFoundError subclasses KeyError, not ValueError.

    So the route's `except ValueError` missed it entirely and a typo produced a
    bare 500 with a text/plain body the client could only render as
    "Request failed (500)".
    """
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30",
                                        "latitude": 13.0, "longitude": 80.0,
                                        "timezone": zone})
    assert r.status_code == 422, f"{zone!r} gave {r.status_code}"


def test_empty_timezone_falls_back_to_coordinates(client) -> None:
    """An empty string is not a typo; it means "you decide"."""
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30",
                                        "latitude": 13.0827, "longitude": 80.2707,
                                        "timezone": ""})
    assert r.status_code == 200
    assert r.json()["birth"]["timezone"] == "Asia/Kolkata"


def test_unexpected_errors_return_structured_json() -> None:
    """A 500 must still be parseable, or the UI can only say "failed (500)".

    Needs its own client: TestClient re-raises server exceptions by default,
    which would bypass the very handler under test.
    """
    from jyotish.api import service

    def boom(_req):
        raise RuntimeError("simulated failure with C:/a/private/path")

    original = service.compute_chart
    service.compute_chart = boom
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.post("/api/chart",
                       json={"date": "1990-05-15", "time": "06:30", **CHENNAI})
        assert r.status_code == 500
        detail = r.json()["detail"]
        assert "RuntimeError" in detail
        # The exception's own message can carry paths; it must not be echoed.
        assert "private" not in detail
    finally:
        service.compute_chart = original


def test_unknown_ayanamsa_is_rejected(client) -> None:
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30",
                                        **CHENNAI, "ayanamsa": "placidus"})
    assert r.status_code == 422


# --- places -----------------------------------------------------------------

@needs_places
def test_place_search(client) -> None:
    r = client.get("/api/places", params={"q": "Madurai", "limit": 5})
    assert r.status_code == 200
    results = r.json()["results"]
    assert results and results[0]["name"] == "Madurai"
    assert results[0]["timezone"] == "Asia/Kolkata"
    assert "Tamil Nadu" in results[0]["display_name"]


@needs_places
def test_place_search_in_tamil(client) -> None:
    r = client.get("/api/places", params={"q": "மதுரை"})
    assert r.json()["results"][0]["name"] == "Madurai"


@needs_places
def test_place_limit_is_bounded(client) -> None:
    """`limit` reaches SQL, and SQLite reads a negative LIMIT as unbounded."""
    assert client.get("/api/places", params={"q": "a", "limit": -1}).status_code == 422
    assert client.get("/api/places", params={"q": "a", "limit": 9999}).status_code == 422


def test_empty_query_is_rejected(client) -> None:
    assert client.get("/api/places", params={"q": ""}).status_code == 422


@needs_places
def test_chart_by_geonameid_matches_coordinates(client) -> None:
    place = client.get("/api/places", params={"q": "Chennai", "limit": 1}).json()["results"][0]
    by_id = chart(client, geonameid=place["geonameid"],
                  latitude=None, longitude=None, timezone=None)
    by_coords = chart(client, latitude=place["latitude"],
                      longitude=place["longitude"], timezone=place["timezone"])

    assert by_id["lagna"]["longitude"] == by_coords["lagna"]["longitude"]
    assert by_id["birth"]["place_name"] is not None


@needs_places
def test_unknown_geonameid_is_422(client) -> None:
    r = client.post("/api/chart", json={"date": "1990-05-15", "time": "06:30",
                                        "geonameid": 999999999})
    assert r.status_code == 422


# --- metadata ---------------------------------------------------------------

def test_graha_abbreviations_are_distinct_and_grapheme_safe(client) -> None:
    """Tamil short forms are authored, not truncated.

    Slicing Tamil at a fixed length can drop a combining mark: சந்திரன் (Moon)
    became சந and சனி (Saturn) became சன — two plausible-looking words that are
    neither graha, differing only in ந vs ன, one of the most confusable pairs in
    the script. Both must survive, and no abbreviation may end on a bare mark.
    """
    import unicodedata

    grahas = client.get("/api/meta").json()["grahas"]
    assert len(grahas) == 9

    for field in ("en_short", "ta_short"):
        shorts = [g[field] for g in grahas]
        assert all(shorts), f"{field} must always be populated"
        assert len(set(shorts)) == 9, f"{field} collides: {shorts}"

    by_name = {g["en"]: g for g in grahas}
    assert by_name["Moon"]["ta_short"] == "சந்"
    assert by_name["Saturn"]["ta_short"] == "சனி"
    assert by_name["Sun"]["ta_short"] == "சூ"
    assert by_name["Venus"]["ta_short"] == "சு"

    for g in grahas:
        first = unicodedata.category(g["ta_short"][0])
        assert not first.startswith("M"), f"{g['en']} starts with a combining mark"
        assert g["ta_short"] in g["ta"], f"{g['en']} abbreviation is not a prefix"


def test_meta_gives_a_client_everything_it_needs(client) -> None:
    body = client.get("/api/meta").json()
    assert len(body["rasis"]) == 12
    assert len(body["nakshatras"]) == 27
    assert len(body["grahas"]) == 9
    assert len(body["vargas"]) == 16
    assert body["rasis"][0]["ta"] == "மேஷம்"
    assert body["grahas"][0]["ta"] == "சூரியன்"
    assert set(body["ayanamsas"]) == {"lahiri", "true_chitrapaksha", "kp", "raman"}


def test_cors_allows_every_method_the_api_exposes(client) -> None:
    """A preflight must succeed for PUT and DELETE.

    TestClient is same-process and never sends a preflight, which is exactly
    why PUT and DELETE shipped blocked at the browser while this suite stayed
    green. Issuing the OPTIONS request explicitly closes that blind spot.
    """
    for method in ("GET", "POST", "PUT", "DELETE"):
        r = client.options("/api/records/1", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": method,
        })
        assert r.status_code == 200, f"{method} preflight rejected: {r.text}"
        allowed = r.headers.get("access-control-allow-methods", "")
        assert method in allowed, f"{method} missing from {allowed!r}"


def test_meta_reports_the_real_ephemeris_range(client) -> None:
    """Derived from the loaded kernel, not a hardcoded string.

    The kernel is configurable via ASTROAPP_EPHEMERIS, so a fixed range would
    misreport, and the date picker built from it would reject valid dates.
    """
    from jyotish.core.ephemeris import covered_years

    first, last = covered_years()
    body = client.get("/api/meta").json()
    assert body["first_year"] == first
    assert body["last_year"] == last
    assert str(first) in body["ephemeris_range"]


@pytest.mark.parametrize("offset", [-1, 1])
def test_out_of_range_date_is_422(client, offset: int) -> None:
    from jyotish.core.ephemeris import covered_years

    first, last = covered_years()
    year = first - 1 if offset < 0 else last + 1
    r = client.post("/api/chart", json={"date": f"{year}-06-01", "time": "06:30",
                                        **CHENNAI})
    assert r.status_code == 422
    assert "ephemeris" in r.text.lower() or str(first) in r.text


def test_health(client) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["engine_version"] == service.ENGINE_VERSION


def test_engine_version_travels_with_every_chart(client) -> None:
    """Part of the cache key, so a correctness fix cannot serve stale results."""
    assert chart(client)["engine_version"] == service.ENGINE_VERSION
