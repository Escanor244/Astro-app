"""Place search, timezone resolution, and DST edge cases.

The place index is a build artifact (gitignored, ~98 MB), so these tests skip
cleanly when it has not been built. Run ``python scripts/build_places_db.py``
to enable them.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core import places
from jyotish.core import positions as pos
from jyotish.core.birthdata import BirthData, resolve_timezone

pytestmark = pytest.mark.skipif(
    not places.DB_PATH.exists(),
    reason="place index not built; run scripts/build_places_db.py",
)


# --- coverage ---------------------------------------------------------------

def test_index_has_village_level_coverage() -> None:
    """The whole point of ingesting all of India rather than cities500 alone."""
    assert places.count() > 500_000


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Chennai", "Chennai"),
        ("Madurai", "Madurai"),
        ("Thanjavur", "Thanjavur"),
        ("Kumbakonam", "Kumbakonam"),
        ("Tiruchirappalli", "Tiruchirappalli"),
        ("Singapore", "Singapore"),
    ],
)
def test_finds_expected_place(query: str, expected: str) -> None:
    results = places.search(query, limit=5)
    assert results, f"no match for {query!r}"
    assert results[0].name == expected


# --- Tamil script -----------------------------------------------------------

@pytest.mark.parametrize(
    "tamil,expected",
    [
        ("மதுரை", "Madurai"),
        ("சென்னை", "Chennai"),
        ("கோயம்புத்தூர்", "Coimbatore"),
    ],
)
def test_tamil_script_search(tamil: str, expected: str) -> None:
    """A Tamil-native app must accept Tamil input, not just romanisation."""
    results = places.search(tamil, limit=5)
    assert results, f"no match for {tamil}"
    assert results[0].name == expected


# --- ranking ----------------------------------------------------------------

def test_major_city_outranks_namesakes() -> None:
    """'Chennai' must return the city of four million, not a hamlet."""
    assert places.search("Chennai", limit=5)[0].population > 1_000_000


def test_exactness_outranks_column_matched() -> None:
    """'Trichy' is an alternate name for Tiruchirappalli.

    There is also a population-zero place named literally 'Trichy'. An exact hit
    on the primary name must not beat an exact hit on an alternate name purely
    because of which column matched -- population breaks the tie instead.
    """
    top = places.search("Trichy", limit=5)[0]
    assert top.population > 100_000


def test_populated_city_outranks_unpopulated_exact_match() -> None:
    """'Madu' exactly matches a population-zero hamlet, and prefix-matches
    Madurai. The city of 1.4 million is what the user meant."""
    assert places.search("Madu", limit=5)[0].name == "Madurai"


def test_unpopulated_village_still_findable() -> None:
    """Demoting population-zero places must not bury them.

    Village coverage is the reason the full India dataset is ingested at all, so
    a village with a distinctive name has to come back first.
    """
    results = places.search("Maduravoyal", limit=5)
    assert results and results[0].name == "Maduravoyal"


# --- diacritics -------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,folded",
    [
        ("Hosūr", "hosur"),
        ("Zürich", "zurich"),
        ("São Paulo", "sao paulo"),
        ("Kāraikudi", "karaikudi"),
        ("Bogotá", "bogota"),
        ("MADURAI", "madurai"),
    ],
)
def test_fold_name_strips_latin_diacritics(raw: str, folded: str) -> None:
    assert places.fold_name(raw) == folded


@pytest.mark.parametrize("tamil", ["மதுரை", "சென்னை", "கோயம்புத்தூர்", "திருச்சிராப்பள்ளி"])
def test_fold_name_leaves_tamil_untouched(tamil: str) -> None:
    """Tamil vowel signs are Unicode combining marks too.

    மதுரை is ம + த + vowel-sign-U + ர + vowel-sign-AI. Stripping combining
    characters after NFD -- the obvious way to remove accents -- would turn it
    into மதரை, a different word. Only marks over ASCII letters may be dropped.
    """
    assert places.fold_name(tamil) == tamil


@pytest.mark.parametrize(
    "query", ["Hosur", "Madurai", "Karaikudi", "Thanjavur", "Kumbakonam", "Salem"]
)
def test_displayed_name_can_be_searched_back(query: str) -> None:
    """search(search(q)[0].name) must find the same place.

    It did not: search_key came from GeoNames' ascii_name ("Hosur") while
    display_name renders the name column ("Hosūr"), so pasting back what the app
    had just printed returned nothing for most of Tamil Nadu.
    """
    first = places.search(query, limit=1)
    assert first, f"no result for {query!r}"
    again = places.search(first[0].name, limit=1)
    assert again, f"{first[0].name!r} (as displayed) is not findable"
    assert again[0].geonameid == first[0].geonameid


@pytest.mark.parametrize(
    "accented,plain",
    [("Zürich", "Zurich"), ("São Paulo", "Sao Paulo"), ("Málaga", "Malaga"),
     ("Bogotá", "Bogota")],
)
def test_both_spellings_find_the_same_city(accented: str, plain: str) -> None:
    """GeoNames romanises rather than transliterating in places -- Zürich's
    ascii_name is "Zuerich" -- so it previously matched *neither* spelling."""
    a = places.search(accented, limit=1)
    b = places.search(plain, limit=1)
    assert a and b, f"{accented!r} -> {len(a)}, {plain!r} -> {len(b)}"
    assert a[0].geonameid == b[0].geonameid


def test_schema_version_is_enforced() -> None:
    """A stale index must fail loudly rather than quietly stop matching names."""
    row = places._connect().execute(
        "SELECT value FROM meta WHERE key = 'schema_version'"
    ).fetchone()
    assert row is not None, "index has no schema_version; rebuild it"
    assert int(row[0]) == places.SCHEMA_VERSION


def test_london_uk_before_london_ontario() -> None:
    assert places.search("London", limit=5)[0].country_code == "GB"


def test_country_filter() -> None:
    for place in places.search("London", limit=5, country="CA"):
        assert place.country_code == "CA"


# --- robustness -------------------------------------------------------------

def test_empty_query_returns_nothing() -> None:
    assert places.search("") == []
    assert places.search("   ") == []


def test_like_wildcards_are_escaped() -> None:
    """A '%' must be a literal, not 'match everything'."""
    assert places.search("%") == []


def test_unknown_place_returns_nothing() -> None:
    assert places.search("Zzzzqqqq Nowhere") == []


# --- timezone ---------------------------------------------------------------

@pytest.mark.parametrize(
    "query", ["Chennai", "Madurai", "Singapore", "London", "Sydney", "Colombo"]
)
def test_geonames_timezone_agrees_with_coordinate_lookup(query: str) -> None:
    """Two independent sources for the same fact must agree.

    GeoNames ships a timezone per place; timezonefinder derives one from
    coordinates. Place-based entry uses the former and manual coordinate entry
    the latter, so a disagreement would mean the same birth produced different
    charts depending on how it was entered.
    """
    place = places.search(query, limit=1)[0]
    assert place.timezone == resolve_timezone(place.latitude, place.longitude)


# --- integration with BirthData --------------------------------------------

def test_place_and_coordinates_give_identical_charts() -> None:
    """Place search is input convenience and must not perturb the astronomy."""
    when = datetime(1990, 5, 15, 6, 30)
    place = places.search("Chennai", limit=1)[0]

    by_place = pos.compute(BirthData.from_place(place, when), ay.Ayanamsa.LAHIRI)
    by_coords = pos.compute(
        BirthData(
            when=when,
            latitude=place.latitude,
            longitude=place.longitude,
            timezone_name=place.timezone,
        ),
        ay.Ayanamsa.LAHIRI,
    )

    assert by_place.lagna.longitude == by_coords.lagna.longitude
    for gi in range(9):
        assert by_place.grahas[gi].longitude == by_coords.grahas[gi].longitude


def test_from_place_carries_timezone_and_display_name() -> None:
    place = places.search("Madurai", limit=1)[0]
    birth = BirthData.from_place(place, datetime(1975, 11, 3, 22, 15))
    assert birth.timezone_name == "Asia/Kolkata"
    assert birth.utc_offset == timedelta(hours=5, minutes=30)
    assert "Tamil Nadu" in birth.place_name


def test_timezone_override_beats_place_timezone() -> None:
    """A birth certificate naming a zone must win over the geographic default."""
    place = places.search("Chennai", limit=1)[0]
    birth = BirthData.from_place(
        place, datetime(1990, 5, 15, 6, 30), timezone_name="Asia/Singapore"
    )
    assert birth.utc_offset == timedelta(hours=8)
