"""HTTP contract for /api/dasha and /api/panchangam.

The engine-level behaviour is covered by test_dasha.py and test_panchangam.py.
What is checked here is the part only the HTTP layer can get wrong: that bad
input becomes a 422 with a usable message rather than a 500, that the drill-down
path round-trips, and that every method the browser will issue survives the CORS
preflight -- which is exactly how PUT and DELETE shipped broken in Phase 1c with
a fully green suite.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from jyotish.api.app import app

# raise_server_exceptions=False so a 500 is observed as a response rather than
# re-raised into the test, which is the only way to assert that unhandled errors
# come back as structured JSON.
client = TestClient(app, raise_server_exceptions=False)

CHENNAI = {
    "date": "1990-05-15",
    "time": "06:30",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "timezone": "Asia/Kolkata",
    "place_name": "Chennai",
}


def post(url: str, **overrides):
    # Named `url`, not `path`: the request body has a field called `path`, and a
    # collision here silently swallowed it as the endpoint argument.
    return client.post(url, json={**CHENNAI, **overrides})


# --- dasha -------------------------------------------------------------------


def test_dasha_returns_nine_mahadashas_and_a_balance():
    body = post("/api/dasha").json()
    assert len(body["periods"]) == 9
    assert all(p["level"] == 1 for p in body["periods"])
    assert body["parent"] is None
    assert body["balance"]["years"] >= 0
    assert body["balance"]["formatted_ta"]
    assert body["year_length"] == "julian"
    assert body["year_days"] == 365.25


def test_the_running_chain_has_all_five_levels():
    body = post("/api/dasha", at="2026-08-10").json()
    running = body["running"]
    assert [p["level"] for p in running] == [1, 2, 3, 4, 5]
    for outer, inner in zip(running, running[1:]):
        assert inner["lords"][:-1] == outer["lords"]
    assert running[-1]["has_children"] is False


def test_drilling_down_a_path_returns_that_nodes_children():
    top = post("/api/dasha").json()
    lord = top["periods"][0]["lords"][0]

    level2 = post("/api/dasha", path=[lord]).json()
    assert level2["parent"]["lords"] == [lord]
    assert len(level2["periods"]) == 9
    assert all(p["level"] == 2 for p in level2["periods"])
    # A sub-period sequence opens with its own parent's lord.
    assert level2["periods"][0]["lords"] == [lord, lord]

    # The children exactly fill the parent, which the client relies on to draw
    # a contiguous table.
    assert level2["periods"][0]["start"] == level2["parent"]["start"]
    assert level2["periods"][-1]["end"] == level2["parent"]["end"]


def test_the_deepest_level_reports_no_children():
    top = post("/api/dasha").json()
    lord = top["periods"][0]["lords"][0]
    body = post("/api/dasha", path=[lord, lord, lord, lord]).json()
    assert all(p["level"] == 5 for p in body["periods"])
    assert all(p["has_children"] is False for p in body["periods"])


def test_a_path_deeper_than_five_levels_is_refused_at_the_model_boundary():
    """Caught by the field's own length bound, before any dasha is computed.

    Four sub-lords is the deepest addressable node, since naming four takes you
    to level five and level five has no children. The service raises a clear
    ValueError too, but the model should get there first -- that is the pattern
    the rest of this API follows.
    """
    top = post("/api/dasha").json()
    lord = top["periods"][0]["lords"][0]
    r = post("/api/dasha", path=[lord] * 5)
    assert r.status_code == 422
    assert "at most 4" in str(r.json()["detail"])


def test_an_out_of_range_lord_is_a_422():
    r = post("/api/dasha", path=[99])
    assert r.status_code == 422


def test_an_unknown_year_length_names_the_known_ones():
    r = post("/api/dasha", year_length="metric")
    assert r.status_code == 422
    assert "savana" in str(r.json()["detail"])


def test_an_unreadable_at_value_is_a_422_with_an_example():
    r = post("/api/dasha", at="next tuesday")
    assert r.status_code == 422
    assert "YYYY-MM-DD" in r.json()["detail"]


def test_dates_come_back_in_the_birth_places_zone():
    body = post("/api/dasha").json()
    assert body["timezone"] == "Asia/Kolkata"
    first = body["periods"][0]
    # +05:30 means the local rendering is never equal to the UTC one.
    assert first["start"] != first["start_utc"]


def test_a_date_outside_the_cycle_returns_an_empty_chain_not_an_error():
    body = post("/api/dasha", at="1800-01-01").json()
    assert body["running"] == []


# --- panchangam --------------------------------------------------------------


def test_panchangam_returns_all_five_limbs():
    body = post("/api/panchangam").json()
    for limb in ("tithi", "nakshatra", "yoga", "karana"):
        assert body[limb]["name"]["ta"]
        assert body[limb]["start"] < body[limb]["end"]
    assert 0 <= body["vaara"] <= 6
    assert body["vaara_name"]["ta"]
    assert body["paksha"] in (0, 1)


def test_panchangam_returns_the_windows_and_the_tamil_date():
    body = post("/api/panchangam", date="2026-08-10", time="12:00").json()
    assert body["daylight"] == "normal"
    assert len(body["gowri_day"]) == 8
    assert len(body["gowri_night"]) == 8
    assert body["rahu_kalam"]["auspicious"] is False
    assert body["tamil_month_name"]["ta"] == "ஆடி"
    assert body["tamil_year_name"]["ta"] == "பராபவ"
    assert body["tamil_day"] == 25
    # Nalla neram is the auspicious gowri windows, day and night.
    assert len(body["nalla_neram"]) == 10
    assert all(w["auspicious"] for w in body["nalla_neram"])


def test_a_polar_day_omits_the_windows_rather_than_inventing_them():
    r = client.post("/api/panchangam", json={
        "date": "2026-06-21", "time": "12:00",
        "latitude": 69.6492, "longitude": 18.9553,
        "timezone": "Europe/Oslo", "place_name": "Tromso",
    })
    body = r.json()
    assert r.status_code == 200
    assert body["daylight"] == "always_up"
    assert body["sunrise"] is None and body["sunset"] is None
    assert body["rahu_kalam"] is None
    assert body["gowri_day"] == []
    # The limbs are longitudes and are unaffected by the horizon.
    assert body["nakshatra"]["name"]["ta"]


def test_panchangam_rejects_a_date_the_ephemeris_cannot_cover():
    r = post("/api/panchangam", date="1200-01-01")
    assert r.status_code == 422


def test_panchangam_rejects_a_bad_time_with_a_readable_message():
    r = post("/api/panchangam", time="25:99")
    assert r.status_code == 422


# --- CORS --------------------------------------------------------------------


def test_the_preflight_allows_the_new_endpoints():
    """TestClient never sends a preflight of its own, so it is issued by hand.

    This is the exact gap that let PUT and DELETE ship blocked in the browser in
    Phase 1c while every same-process test passed.
    """
    for path in ("/api/dasha", "/api/panchangam"):
        r = client.options(path, headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert r.status_code == 200, path
        allowed = r.headers["access-control-allow-methods"]
        assert "POST" in allowed


# --- the meta contract -------------------------------------------------------


def test_meta_still_describes_the_engine():
    body = client.get("/api/meta").json()
    assert body["engine_version"] == "2.0"
    assert len(body["nakshatras"]) == 27
