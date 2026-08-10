"""The saved chart library.

The central property under test is the one the pre-UI audit warned about: a
saved record must be **immutable against a rebuilt place index**. The place
database is a 100 MB build artifact regenerated from a GeoNames download with no
recorded vintage; if a record stored only a `geonameid` and re-resolved it on
read, rebuilding from a newer dump could silently move a saved chart.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jyotish.api.app import app
from jyotish.store import records as store


@pytest.fixture(autouse=True)
def isolated_library(tmp_path, monkeypatch):
    """Give every test its own library file."""
    store.close()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "library.sqlite")
    yield
    store.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


RECORD = {
    "name": "Test Person",
    "birth_date": "1990-05-15",
    "birth_time": "06:30:00",
    "latitude": 13.0878,
    "longitude": 80.2785,
    "timezone_name": "Asia/Kolkata",
    "place_name": "Chennai, Tamil Nadu, India",
    "geonameid": 1264527,
    "vargas": ["D1", "D9"],
}


# --- the reason this design exists ------------------------------------------

def test_resolved_place_is_stored_not_re_resolved(client) -> None:
    """A record keeps the coordinates it was saved with, not the id's current ones.

    This is the whole point. `geonameid` is provenance; the coordinates,
    timezone and place name are the source of truth, so a rebuilt place index
    cannot move a saved chart.
    """
    created = client.post("/api/records", json=RECORD).json()
    fetched = client.get(f"/api/records/{created['id']}").json()

    assert fetched["latitude"] == RECORD["latitude"]
    assert fetched["longitude"] == RECORD["longitude"]
    assert fetched["timezone_name"] == "Asia/Kolkata"
    assert fetched["place_name"] == RECORD["place_name"]
    assert fetched["geonameid"] == RECORD["geonameid"]


def test_a_record_needs_no_place_index_at_all(client) -> None:
    """Saving and reading must not touch the place database.

    A record whose geonameid does not exist anywhere still round-trips, which
    proves nothing re-resolves it.
    """
    body = {**RECORD, "geonameid": 999_999_999}
    created = client.post("/api/records", json=body).json()
    assert created["latitude"] == RECORD["latitude"]
    assert client.get(f"/api/records/{created['id']}").json()["latitude"] == RECORD["latitude"]


def test_opening_a_record_keeps_its_place_name(client) -> None:
    """A saved chart must still name its birth place.

    Records are re-cast from coordinates, not from the geonameid, so without
    carrying place_name the chart -- and the A4 sheet exported from it -- would
    fall back to bare numbers for every saved birth.
    """
    created = client.post("/api/records", json=RECORD).json()
    chart = client.post("/api/chart", json={
        "date": created["birth_date"], "time": created["birth_time"],
        "latitude": created["latitude"], "longitude": created["longitude"],
        "place_name": created["place_name"], "timezone": created["timezone_name"],
    }).json()
    assert chart["birth"]["place_name"] == "Chennai, Tamil Nadu, India"


def test_record_without_a_geonameid_is_fine(client) -> None:
    """Coordinates typed by hand are a first-class way to save a birth."""
    body = {**RECORD}
    body.pop("geonameid")
    assert client.post("/api/records", json=body).status_code == 201


def test_saved_record_casts_the_same_chart(client) -> None:
    """Opening a record must reproduce the chart it was saved from."""
    created = client.post("/api/records", json=RECORD).json()

    direct = client.post("/api/chart", json={
        "date": RECORD["birth_date"], "time": RECORD["birth_time"],
        "latitude": RECORD["latitude"], "longitude": RECORD["longitude"],
        "timezone": RECORD["timezone_name"], "vargas": RECORD["vargas"],
    }).json()

    from_record = client.post("/api/chart", json={
        "date": created["birth_date"], "time": created["birth_time"],
        "latitude": created["latitude"], "longitude": created["longitude"],
        "timezone": created["timezone_name"], "fold": created["fold"],
        "ayanamsa": created["ayanamsa"], "vargas": created["vargas"],
    }).json()

    assert from_record["lagna"]["longitude"] == direct["lagna"]["longitude"]
    assert from_record["charts"] == direct["charts"]


# --- CRUD -------------------------------------------------------------------

def test_create_and_read(client) -> None:
    r = client.post("/api/records", json=RECORD)
    assert r.status_code == 201
    created = r.json()
    assert created["id"] > 0
    assert created["created_at"] and created["updated_at"]

    fetched = client.get(f"/api/records/{created['id']}").json()
    assert fetched == created


def test_list_is_newest_first(client) -> None:
    for name in ["First", "Second", "Third"]:
        client.post("/api/records", json={**RECORD, "name": name})
    body = client.get("/api/records").json()
    assert body["total"] == 3
    assert [r["name"] for r in body["records"]] == ["Third", "Second", "First"]


def test_search_by_name_and_place(client) -> None:
    client.post("/api/records", json={**RECORD, "name": "Anbu"})
    client.post("/api/records", json={
        **RECORD, "name": "Kavya", "place_name": "Madurai, Tamil Nadu, India"})

    assert len(client.get("/api/records", params={"q": "anbu"}).json()["records"]) == 1
    assert len(client.get("/api/records", params={"q": "madurai"}).json()["records"]) == 1
    assert len(client.get("/api/records", params={"q": "tamil nadu"}).json()["records"]) == 2
    assert len(client.get("/api/records", params={"q": "zzz"}).json()["records"]) == 0


def test_update_in_place(client) -> None:
    created = client.post("/api/records", json=RECORD).json()
    r = client.put(f"/api/records/{created['id']}",
                   json={**RECORD, "name": "Renamed", "notes": "checked vs JHora"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"
    assert r.json()["id"] == created["id"]
    assert client.get("/api/records").json()["total"] == 1


def test_delete(client) -> None:
    created = client.post("/api/records", json=RECORD).json()
    assert client.delete(f"/api/records/{created['id']}").status_code == 204
    assert client.get(f"/api/records/{created['id']}").status_code == 404
    assert client.get("/api/records").json()["total"] == 0


def test_crud_targets_the_right_record_among_several(client) -> None:
    """Every CRUD operation must act on the id it was given, and only that one.

    Every other test here works on a library holding exactly one record, which
    means get/update/delete could ignore the id entirely and still pass.
    Mutation-testing confirmed it: dropping the WHERE clause from DELETE --
    which wipes the user's whole library on every delete -- left the suite
    green. This is the test that kills that mutant.
    """
    ids = {
        name: client.post("/api/records", json={**RECORD, "name": name}).json()["id"]
        for name in ("Alpha", "Beta", "Gamma")
    }

    # GET returns the one asked for.
    assert client.get(f"/api/records/{ids['Beta']}").json()["name"] == "Beta"
    assert client.get("/api/records").json()["total"] == 3

    # PUT edits only that one.
    client.put(f"/api/records/{ids['Beta']}", json={**RECORD, "name": "Beta edited"})
    names = {r["id"]: r["name"] for r in client.get("/api/records").json()["records"]}
    assert names == {ids["Alpha"]: "Alpha", ids["Beta"]: "Beta edited", ids["Gamma"]: "Gamma"}

    # DELETE removes only that one.
    assert client.delete(f"/api/records/{ids['Beta']}").status_code == 204
    remaining = client.get("/api/records").json()
    assert remaining["total"] == 2
    assert {r["name"] for r in remaining["records"]} == {"Alpha", "Gamma"}
    assert client.get(f"/api/records/{ids['Alpha']}").json()["name"] == "Alpha"


def test_a_failed_update_leaves_the_library_writable(client) -> None:
    """A rejected update must not strand an open write transaction.

    The 'no such record' raise happens after the UPDATE has opened one, and
    without a rollback the shared connection held SQLite's write lock forever,
    blocking every other writer.
    """
    with pytest.raises(store.LibraryError):
        store.save(store.BirthRecord(
            id=9999, name="Ghost", birth_date="1990-05-15", birth_time="06:30",
            latitude=13.0, longitude=80.0, timezone_name="Asia/Kolkata"))

    assert not store.connect().in_transaction, "write transaction left open"
    assert client.post("/api/records", json=RECORD).status_code == 201


def test_missing_record_is_404(client) -> None:
    assert client.get("/api/records/999").status_code == 404
    assert client.delete("/api/records/999").status_code == 404
    assert client.put("/api/records/999", json=RECORD).status_code == 404


# --- validation -------------------------------------------------------------

@pytest.mark.parametrize(
    "patch",
    [
        {"name": ""},
        {"latitude": 95.0},
        {"longitude": 200.0},
        {"timezone_name": "Not/AZone"},
        {"fold": 2},
        {"ayanamsa": "placidus"},
        {"birth_time": "13:30 PM"},
        {"birth_time": "not a time"},
        {"birth_date": "not a date"},
    ],
)
def test_invalid_records_are_rejected(client, patch: dict) -> None:
    r = client.post("/api/records", json={**RECORD, **patch})
    assert r.status_code == 422, f"{patch} was accepted"


def test_a_date_outside_the_ephemeris_cannot_be_saved(client) -> None:
    """Never accept a record that cannot subsequently be opened.

    An out-of-range date used to save with 201 and then fail with 422 on every
    attempt to open it — a permanent entry in the library that could not be
    read, and no indication of which field was at fault.
    """
    from jyotish.core.ephemeris import covered_years

    first, last = covered_years()
    for bad in (f"{first - 1}-06-01", f"{last + 1}-06-01"):
        r = client.post("/api/records", json={**RECORD, "birth_date": bad})
        assert r.status_code == 422, f"{bad} was accepted"
        assert str(first) in r.text and str(last) in r.text

    assert client.get("/api/records").json()["total"] == 0


def test_an_older_record_stays_readable_after_rules_tighten(client) -> None:
    """Validation gates what comes in; it must never lock stored data in.

    Adding the ephemeris range check made a row saved before it existed fail on
    *read*, and because that read happens inside the list endpoint, one old
    record returned 500 and hid every other saved chart. Output models must not
    re-apply input rules.
    """
    # Write straight to the store, bypassing the API's input validation, which
    # is exactly the situation a record saved under older rules is in.
    store.save(store.BirthRecord(
        name="Saved under older rules", birth_date="1800-01-01",
        birth_time="06:30:00", latitude=13.0878, longitude=80.2785,
        timezone_name="Asia/Kolkata"))
    client.post("/api/records", json={**RECORD, "name": "Current"})

    listing = client.get("/api/records")
    assert listing.status_code == 200, listing.text
    names = {r["name"] for r in listing.json()["records"]}
    assert names == {"Saved under older rules", "Current"}

    # And it can still be fetched and deleted individually.
    old = next(r for r in listing.json()["records"] if r["birth_date"] == "1800-01-01")
    assert client.get(f"/api/records/{old['id']}").status_code == 200
    assert client.delete(f"/api/records/{old['id']}").status_code == 204


def test_every_saved_record_can_be_opened(client) -> None:
    """The invariant, stated directly: save then cast must always succeed."""
    from jyotish.core.ephemeris import covered_years

    first, last = covered_years()
    for date in (f"{first}-01-02", "1990-05-15", f"{last}-12-30"):
        created = client.post("/api/records",
                              json={**RECORD, "birth_date": date}).json()
        chart = client.post("/api/chart", json={
            "date": created["birth_date"], "time": created["birth_time"],
            "latitude": created["latitude"], "longitude": created["longitude"],
            "timezone": created["timezone_name"], "vargas": created["vargas"],
        })
        assert chart.status_code == 200, f"saved {date} but could not open it"


def test_a_bad_time_cannot_be_saved(client) -> None:
    """Rejected on save, not on open.

    A record that cannot be cast is worse than a rejected save: the user finds
    out later, with no idea which field is wrong.
    """
    assert client.post("/api/records",
                       json={**RECORD, "birth_time": "25:00"}).status_code == 422
    assert client.get("/api/records").json()["total"] == 0


def test_notes_are_kept(client) -> None:
    created = client.post("/api/records",
                          json={**RECORD, "notes": "Verified against JHora"}).json()
    assert client.get(f"/api/records/{created['id']}").json()["notes"] == "Verified against JHora"


def test_list_limit_is_bounded(client) -> None:
    assert client.get("/api/records", params={"limit": 0}).status_code == 422
    assert client.get("/api/records", params={"limit": 10_000}).status_code == 422


# --- the store, directly ----------------------------------------------------

def test_store_rejects_invalid_records() -> None:
    with pytest.raises(store.LibraryError, match="needs a name"):
        store.BirthRecord(name="  ", birth_date="1990-05-15", birth_time="06:30",
                          latitude=13.0, longitude=80.0, timezone_name="Asia/Kolkata")


def test_store_survives_reopening(tmp_path, monkeypatch) -> None:
    """The library is a file; closing and reopening must not lose anything."""
    store.close()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "reopen.sqlite")

    saved = store.save(store.BirthRecord(
        name="Persisted", birth_date="1990-05-15", birth_time="06:30:00",
        latitude=13.0878, longitude=80.2785, timezone_name="Asia/Kolkata"))
    store.close()

    reopened = store.get(saved.id)
    assert reopened is not None
    assert reopened.name == "Persisted"
    assert reopened.latitude == 13.0878
    store.close()


def test_updating_an_unknown_id_raises() -> None:
    with pytest.raises(store.LibraryError, match="No saved record"):
        store.save(store.BirthRecord(
            id=4242, name="Ghost", birth_date="1990-05-15", birth_time="06:30",
            latitude=13.0, longitude=80.0, timezone_name="Asia/Kolkata"))
