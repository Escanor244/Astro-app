"""Request and response shapes for the JSON API.

This is the contract the web UI builds against, and any mobile client later.
Two principles shaped it:

* **Everything the CLI shows, the API returns.** The timezone actually applied,
  its annotation, and the daylight-saving warnings are not decoration -- they
  are how a user catches a mis-entered birth before reading a wrong chart. An
  API that returned only longitudes would push the UI into re-deriving them.
* **Names travel with indices.** A graha is an index internally, but a client
  should never need its own copy of the Tamil lexicon to render a chart. Every
  index is accompanied by its English and Tamil names.
"""

from __future__ import annotations

# Aliased because ChartRequest has a field called `date`, which would otherwise
# shadow the type in its own annotation namespace and break Pydantic.
from datetime import date as DateType
from typing import Literal
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, field_validator

from ..charts import vargas
from ..core import ayanamsa as ay

AyanamsaName = Literal["lahiri", "true_chitrapaksha", "kp", "raman"]


def _check_year(value: DateType) -> DateType:
    """Reject a date the loaded ephemeris cannot compute.

    Shared by charts and saved records. Without it on records, an out-of-range
    date saved happily and then failed with 422 on every attempt to open it --
    a record in the library that could never be read, which is worse than a
    refused save because the user finds out later and cannot tell which field
    is wrong.

    The bound comes from the kernel actually loaded, not a constant: DE440s
    covers 1849-2150, and ``ASTROAPP_EPHEMERIS=de440.bsp`` extends that to
    1550-2650.
    """
    from ..core.ephemeris import covered_years

    first, last = covered_years()
    if not first <= value.year <= last:
        raise ValueError(
            f"{value.isoformat()} is outside the range this ephemeris covers "
            f"({first}-{last}). Set ASTROAPP_EPHEMERIS=de440.bsp for a wider "
            "span, then restart the engine."
        )
    return value


class TermOut(BaseModel):
    """A Jyotish term in each script the UI may want to show.

    The ``_short`` forms are always populated. They exist so a client never has
    to truncate a name itself: Tamil letters are a base character plus combining
    marks, and cutting at a fixed length turns சந்திரன் (Moon) into சந and சனி
    (Saturn) into சன -- two plausible-looking words that are neither graha, and
    that differ from each other only in ந vs ன.
    """

    en: str
    ta: str
    ta_latin: str
    en_short: str
    ta_short: str


class PlaceOut(BaseModel):
    geonameid: int
    name: str
    display_name: str
    admin1: str
    country_code: str
    country_name: str
    latitude: float
    longitude: float
    timezone: str
    population: int


class PlacesResponse(BaseModel):
    query: str
    results: list[PlaceOut]


class ChartRequest(BaseModel):
    """A birth record, as a user would enter it."""

    date: DateType = Field(description="Local birth date at the birth place")

    _check_date = field_validator("date")(_check_year)
    time: str = Field(
        description='Local birth time. 24-hour "18:30", or "6:30 PM". '
                    "A bare time is 24-hour.",
        examples=["06:30", "18:30", "6:30 PM"],
    )

    # Either a place id, or explicit coordinates.
    geonameid: int | None = Field(
        default=None, ge=1, le=2**63 - 1,
        description="Place from /api/places. Preferred.",
    )
    # Bounded because it reaches SQLite, which rejects an integer outside the
    # signed 64-bit range with an OverflowError rather than simply not matching
    # -- a 500 for what is plainly bad input.
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    place_name: str | None = Field(
        default=None, max_length=200,
        description="Display name for a chart cast from coordinates. A saved "
                    "record supplies this so its place survives without being "
                    "re-resolved from a geonameid.",
    )

    timezone: str | None = Field(
        default=None,
        description="IANA zone override, e.g. Asia/Kolkata. Derived from the "
                    "place when omitted.",
        examples=["Asia/Kolkata"],
    )

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str | None) -> str | None:
        """Reject an unknown zone here, where it becomes a clean 422.

        Left to itself, ``ZoneInfo`` raises ``ZoneInfoNotFoundError``, which
        subclasses *KeyError* rather than ValueError -- so the route's
        ``except ValueError`` missed it and a typo like "asia/kolkata" or "IST"
        produced a bare 500 with no usable body.
        """
        if value is None or not value.strip():
            return None
        if value not in available_timezones():
            raise ValueError(
                f"Unknown timezone {value!r}. Use an IANA name such as "
                "'Asia/Kolkata'; names are case-sensitive."
            )
        return value
    fold: int = Field(
        default=0, ge=0, le=1,
        description="Which occurrence of a repeated hour to use at the end of "
                    "summer time. See `time_warning` in the response.",
    )
    ayanamsa: AyanamsaName = "lahiri"
    vargas: list[str] = Field(
        default_factory=lambda: ["D1"],
        description='Divisional charts to return, e.g. ["D1", "D9"].',
    )
    name: str | None = Field(default=None, max_length=120)


class ZodiacOut(BaseModel):
    """Where a longitude falls in the sidereal zodiac."""

    longitude: float
    formatted: str = Field(description='Degrees within the rasi, e.g. 11°09\'21.84"')
    rasi: int = Field(ge=0, le=11)
    rasi_name: TermOut
    degrees_in_rasi: float
    nakshatra: int = Field(ge=0, le=26)
    nakshatra_name: TermOut
    pada: int = Field(ge=1, le=4)
    nakshatra_lord: int = Field(ge=0, le=8)
    nakshatra_lord_name: TermOut


class GrahaOut(BaseModel):
    graha: int = Field(ge=0, le=8)
    name: TermOut
    sanskrit: str
    position: ZodiacOut
    house: int = Field(ge=1, le=12, description="Whole-sign bhava from the lagna")

    #: The three states a printed jathagam marks, and they are independent --
    #: a graha can be all three at once and each says something different.
    retrograde: bool
    combust: bool = Field(description="அஸ்தங்கதம், burnt by nearness to the Sun")
    speed_deg_per_day: float

    #: exalted | moolatrikona | own | friend | neutral | enemy | debilitated,
    #: or "undefined" for Rahu and Ketu, which the classical sources leave
    #: unassigned. See jyotish/core/dignity.py.
    dignity: str
    dignity_name: TermOut
    #: Why, in plain words. A dignity is the first place a user asks "why?".
    dignity_reason: str
    #: Degrees from the deep exaltation point, 0-180. Null for the nodes.
    #: 0 is peak exaltation; 180 is the depth of debilitation.
    from_exaltation: float | None
    #: Lord of the rasi the graha occupies.
    dispositor: int = Field(ge=0, le=8)
    dispositor_name: TermOut


class VargaOut(BaseModel):
    """One divisional chart, ready to draw."""

    code: str
    divisions: int
    name: TermOut
    significance: str
    lagna_rasi: int = Field(ge=0, le=11)
    #: graha index -> rasi index. Keys are strings because JSON object keys are.
    graha_rasis: dict[str, int]
    retrogrades: list[int]


class BirthOut(BaseModel):
    """The birth record as the engine actually interpreted it.

    Echoed back in full so a user can see what was assumed. The 12-hour reading
    and the offset annotation exist because an AM/PM slip moves the lagna about
    180 degrees and a historical offset moves it about one rasi -- both silent
    otherwise.
    """

    local_datetime: str
    time_12h: str
    utc: str
    place_name: str | None
    latitude: float
    longitude: float
    timezone: str
    utc_offset: str
    offset_note: str | None


class ChartResponse(BaseModel):
    birth: BirthOut
    ayanamsa: AyanamsaName
    ayanamsa_value: float
    ayanamsa_formatted: str
    lagna: ZodiacOut
    grahas: list[GrahaOut]
    charts: list[VargaOut]
    #: Set when the local time is ambiguous or never happened. The UI must show
    #: this prominently: an hour of doubt is about 15 degrees of lagna.
    time_warning: str | None = None
    #: Which kind of warning, so a client knows whether a second reading exists.
    #: Only an "ambiguous" time has one; a "nonexistent" time has exactly one
    #: interpretation, and offering to switch it would invite the user into a
    #: choice that is not real.
    time_warning_kind: Literal["ambiguous", "nonexistent"] | None = None
    engine_version: str


class DashaRequest(ChartRequest):
    """A birth, plus which slice of its dasha tree to return.

    The tree is not returned whole, and cannot be: five levels of nine lords is
    59,049 periods, and the deepest are minutes long. The client asks for one
    node's children at a time by naming the chain of lords above it, which is
    how the UI drills down a level per click.
    """

    path: list[int] = Field(
        default_factory=list,
        max_length=4,
        description="Lord chain to expand, outermost first. Empty returns the "
                    "mahadashas; [5] returns the antardashas inside Venus.",
        examples=[[], [5], [5, 6]],
    )
    at: str | None = Field(
        default=None,
        description="Which moment to report as running, as a local date or "
                    "datetime **at the birth place**. Defaults to now.",
        examples=["2026-08-10", "2026-08-10T14:30:00"],
    )
    year_length: str = Field(
        default="julian",
        description="Days in a dasha year. A convention, not an astronomical "
                    "fact. The four solar variants differ by under two days "
                    "across a whole cycle; 'savana' (360) is a different "
                    "tradition and lands ten months away. See docs/02-dasha.md.",
        examples=["julian", "sidereal", "savana"],
    )

    @field_validator("path")
    @classmethod
    def _known_lords(cls, value: list[int]) -> list[int]:
        if any(not 0 <= lord <= 8 for lord in value):
            raise ValueError("Every entry in path must be a graha index 0-8.")
        return value

    @field_validator("year_length")
    @classmethod
    def _known_year_length(cls, value: str) -> str:
        from ..dasha.vimshottari import YEAR_DAYS

        if value not in YEAR_DAYS:
            raise ValueError(
                f"Unknown dasha year length {value!r}. "
                f"Known: {', '.join(sorted(YEAR_DAYS))}."
            )
        return value


class PeriodOut(BaseModel):
    """One dasha period, at whichever of the five levels it sits.

    Dates come back twice. ``start``/``end`` are local time at the **birth
    place**, which is the frame a printed dasha table uses and the one an
    astrologer reads; ``start_utc``/``end_utc`` are the unambiguous instants, for
    a client doing its own arithmetic.
    """

    lords: list[int]
    lord_names: list[TermOut]
    level: int = Field(ge=1, le=5)
    level_name: TermOut
    start: str
    end: str
    start_utc: str
    end_utc: str
    days: float
    #: True when this period contains the requested `at` moment.
    running: bool
    has_children: bool


class DashaBalanceOut(BaseModel):
    """The unexpired first mahadasha -- திசை இருப்பு, as almanacs print it.

    ``years``/``months``/``days`` are dasha units: a month is a twelfth of a
    dasha year and a day a thirtieth of that, not calendar units.
    """

    lord: int = Field(ge=0, le=8)
    lord_name: TermOut
    nakshatra: int = Field(ge=0, le=26)
    nakshatra_name: TermOut
    remaining_fraction: float
    years: int
    months: int
    days: int
    formatted: str
    formatted_ta: str


class DashaResponse(BaseModel):
    balance: DashaBalanceOut
    #: Echoed back because it changes every date below and is a convention.
    year_length: str
    year_days: float
    path: list[int]
    #: The node whose children `periods` are, or null at the top level.
    parent: PeriodOut | None
    periods: list[PeriodOut]
    #: The nested chain running at `at`, outermost first. Empty when `at` falls
    #: outside the 240 years the sequence covers.
    running: list[PeriodOut]
    at: str
    moon_longitude: float
    timezone: str
    engine_version: str


class PanchangamRequest(ChartRequest):
    """A moment and a place. Same shape as a chart request, deliberately.

    The panchangam of a birth and the panchangam of a day are the same
    computation asked at different instants, so there is one endpoint and the
    client simply sends the date and time it cares about. `vargas` is ignored.
    """


class LimbOut(BaseModel):
    """One of the five limbs, with the window it occupies.

    ``end`` is the value a Tamil almanac actually prints -- "நட்சத்திரம் ரோகிணி
    வரை 14:23" -- and it is why the engine root-finds rather than looking up a
    duration. Local times are wall-clock at the place asked about.
    """

    index: int
    name: TermOut
    start: str
    end: str
    start_utc: str
    end_utc: str
    #: How far through the limb the moment sits, in [0, 1).
    elapsed: float


class WindowOut(BaseModel):
    """A named span of the day: a kalam, or one gowri period."""

    name: TermOut
    start: str
    end: str
    #: None where the tradition does not classify the window either way.
    auspicious: bool | None = None


class PanchangamResponse(BaseModel):
    moment: str
    timezone: str
    place_name: str | None
    latitude: float
    longitude: float
    ayanamsa: AyanamsaName

    sunrise: str | None
    sunset: str | None
    next_sunrise: str | None
    moonrise: str | None
    moonset: str | None
    #: "normal", "always_up" (midnight sun) or "always_down" (polar night).
    #: Anything but "normal" means there is no daylight interval, so every
    #: window below that is a fraction of one is absent rather than guessed.
    daylight: str

    vaara: int = Field(ge=0, le=6, description="0 = Sunday, on the sunrise day")
    vaara_name: TermOut

    tithi: LimbOut
    paksha: int = Field(ge=0, le=1, description="0 = waxing, 1 = waning")
    paksha_name: TermOut
    nakshatra: LimbOut
    yoga: LimbOut
    karana: LimbOut

    rahu_kalam: WindowOut | None
    yamagandam: WindowOut | None
    kuligai: WindowOut | None
    gowri_day: list[WindowOut]
    gowri_night: list[WindowOut]
    #: The auspicious gowri windows. See docs/03-panchangam.md: a printed Tamil
    #: tear-off calendar prints something different under the same heading.
    nalla_neram: list[WindowOut]

    tamil_month: int
    tamil_month_name: TermOut
    tamil_day: int
    tamil_year: int
    tamil_year_name: TermOut
    ayana_name: TermOut
    ritu_name: TermOut

    engine_version: str


class RecordFields(BaseModel):
    """The shape of a saved birth, with no validation attached.

    Input rules live on :class:`RecordIn` and are deliberately *not* inherited
    by :class:`RecordOut`. An output model describes what is already stored;
    applying input rules to it means that tightening a rule retroactively makes
    existing records unreadable. That is not hypothetical -- adding an ephemeris
    range check turned one pre-existing row into a 500 on the whole list
    endpoint, hiding every other saved chart behind it.

    Rules gate what comes in. Once something is stored, it must always come back
    out.
    """

    name: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=2000)

    birth_date: DateType
    birth_time: str
    fold: int = Field(default=0, ge=0, le=1)
    ayanamsa: AyanamsaName = "lahiri"

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    timezone_name: str
    place_name: str = Field(default="", max_length=200)
    geonameid: int | None = Field(
        default=None, ge=1, le=2**63 - 1,
        description="Provenance only. The coordinates above are the source of "
                    "truth and are never re-resolved from this.",
    )

    vargas: list[str] = Field(default_factory=lambda: ["D1", "D9"])


class RecordIn(RecordFields):
    """A birth being saved. Everything here gates what may enter the library.

    The resolved place fields are required, not optional, and are never
    re-derived from ``geonameid`` on read: the place index is a regenerable
    build artifact with no recorded vintage, so rebuilding it from a newer
    GeoNames dump could otherwise move a saved chart with no user action and
    nothing to diff against.
    """

    # Same bound as ChartRequest, so a record can never be saved that then
    # fails to open. Applied on the way in only -- see RecordFields.
    _check_birth_date = field_validator("birth_date")(_check_year)

    @field_validator("timezone_name")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        if value not in available_timezones():
            raise ValueError(f"Unknown timezone {value!r}.")
        return value


class RecordOut(RecordFields):
    """A birth being read back. No input rules -- see RecordFields."""

    id: int
    created_at: str
    updated_at: str


class RecordsResponse(BaseModel):
    records: list[RecordOut]
    total: int


class VargaMeta(BaseModel):
    code: str
    divisions: int
    name: TermOut
    significance: str


class MetaResponse(BaseModel):
    """Everything a client needs to build its own selectors."""

    engine_version: str
    ayanamsas: list[str]
    default_ayanamsa: AyanamsaName
    vargas: list[VargaMeta]
    rasis: list[TermOut]
    nakshatras: list[TermOut]
    grahas: list[TermOut]
    ephemeris_range: str
    #: Inclusive year bounds a client should use for its date picker. Derived
    #: from the loaded kernel, so it follows an ASTROAPP_EPHEMERIS override.
    first_year: int
    last_year: int


def all_ayanamsas() -> list[str]:
    return [a.value for a in ay.Ayanamsa]


def all_vargas() -> list[str]:
    return list(vargas.VARGA_ORDER)
