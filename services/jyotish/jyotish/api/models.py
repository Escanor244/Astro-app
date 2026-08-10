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

from pydantic import BaseModel, Field

from ..charts import vargas
from ..core import ayanamsa as ay

AyanamsaName = Literal["lahiri", "true_chitrapaksha", "kp", "raman"]


class TermOut(BaseModel):
    """A Jyotish term in each script the UI may want to show."""

    en: str
    ta: str
    ta_latin: str


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
    time: str = Field(
        description='Local birth time. 24-hour "18:30", or "6:30 PM". '
                    "A bare time is 24-hour.",
        examples=["06:30", "18:30", "6:30 PM"],
    )

    # Either a place id, or explicit coordinates.
    geonameid: int | None = Field(
        default=None, description="Place from /api/places. Preferred."
    )
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)

    timezone: str | None = Field(
        default=None,
        description="IANA zone override. Derived from the place when omitted.",
    )
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
    retrograde: bool
    speed_deg_per_day: float


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
    engine_version: str


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


def all_ayanamsas() -> list[str]:
    return [a.value for a in ay.Ayanamsa]


def all_vargas() -> list[str]:
    return list(vargas.VARGA_ORDER)
