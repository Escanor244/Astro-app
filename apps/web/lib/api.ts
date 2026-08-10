/**
 * Typed client for the Jyotish API.
 *
 * The types here mirror `services/jyotish/jyotish/api/models.py`. They are
 * hand-written rather than generated so the file stays readable, but the API
 * tests pin the response shape, so a drift shows up on the Python side first.
 *
 * Note what this file does NOT contain: any Jyotish knowledge. No rasi names,
 * no nakshatra list, no varga rules. All of that arrives from `/api/meta` or
 * with the chart itself, so there is exactly one Tamil lexicon in the project
 * and it cannot drift from the one the engine computed against.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export type Term = {
  en: string;
  ta: string;
  ta_latin: string;
  /** Conventional abbreviations, authored in the engine lexicon. Never
   *  truncate a Tamil name yourself — cutting at a fixed length can drop a
   *  combining mark and turn one graha's name into another word. */
  en_short: string;
  ta_short: string;
};

export type Place = {
  geonameid: number;
  name: string;
  display_name: string;
  admin1: string;
  country_code: string;
  country_name: string;
  latitude: number;
  longitude: number;
  timezone: string;
  population: number;
};

export type ZodiacPosition = {
  longitude: number;
  formatted: string;
  rasi: number;
  rasi_name: Term;
  degrees_in_rasi: number;
  nakshatra: number;
  nakshatra_name: Term;
  pada: number;
  nakshatra_lord: number;
  nakshatra_lord_name: Term;
};

/** The dignity ladder. "undefined" for Rahu and Ketu, which the classical
 *  sources leave unassigned rather than us guessing. */
export type DignityState =
  | "exalted"
  | "moolatrikona"
  | "own"
  | "great_friend"
  | "friend"
  | "neutral"
  | "enemy"
  | "debilitated"
  | "undefined";

export type Graha = {
  graha: number;
  name: Term;
  sanskrit: string;
  position: ZodiacPosition;
  house: number;

  /** The three marked states. Independent — a graha can be all three at once. */
  retrograde: boolean;
  combust: boolean;
  speed_deg_per_day: number;

  dignity: DignityState;
  dignity_name: Term;
  /** Why, in plain words — shown as a tooltip. */
  dignity_reason: string;
  /** Degrees from deep exaltation, 0–180. Null for the nodes. */
  from_exaltation: number | null;
  dispositor: number;
  dispositor_name: Term;

  /** வர்க்கோத்தமம் — same rasi in the D1 and the D9. */
  vargottama: boolean;
  /** What this graha naturally signifies, whoever's chart it is. */
  karakas: Term[];
  aspects_rasis: number[];
  aspects_bhavas: number[];
};

/** One house, read from the lagna (லக்னப்படி) or from the Moon (ராசிப்படி).
 *  Note the Tamil: no source writes "சந்திர லக்னம்" — see docs/bhava-sources.md. */
export type Bhava = {
  number: number;
  name: Term;
  /** The numeric register, which Tamil keeps separate from the ஸ்தானம் one. */
  label: string;
  label_ta: string;
  rasi: number;
  rasi_name: Term;
  signification: string;
  lord: number;
  lord_name: Term;
  occupants: number[];
  /** kendra | trikona | upachaya | dusthana. A house can be in two. */
  groups: string[];
  group_names: Term[];
  aspected_by: number[];
};

export type VargaChart = {
  code: string;
  divisions: number;
  name: Term;
  significance: string;
  lagna_rasi: number;
  /** graha index (as a string key) -> rasi index */
  graha_rasis: Record<string, number>;
  retrogrades: number[];
};

export type Birth = {
  local_datetime: string;
  time_12h: string;
  utc: string;
  place_name: string | null;
  latitude: number;
  longitude: number;
  timezone: string;
  utc_offset: string;
  offset_note: string | null;
};

export type Chart = {
  birth: Birth;
  ayanamsa: string;
  ayanamsa_value: number;
  ayanamsa_formatted: string;
  lagna: ZodiacPosition;
  lagna_vargottama: boolean;
  grahas: Graha[];
  charts: VargaChart[];
  bhavas: Bhava[];
  bhavas_from_moon: Bhava[];
  badhaka_house: number;
  badhaka_lord: number;
  maraka_lords: number[];
  time_warning: string | null;
  /** Only an "ambiguous" time has a second reading to offer. */
  time_warning_kind: "ambiguous" | "nonexistent" | null;
  engine_version: string;
};

export type VargaMeta = {
  code: string;
  divisions: number;
  name: Term;
  significance: string;
};

export type Meta = {
  engine_version: string;
  ayanamsas: string[];
  default_ayanamsa: string;
  vargas: VargaMeta[];
  rasis: Term[];
  nakshatras: Term[];
  grahas: Term[];
  ephemeris_range: string;
};

export type ChartRequest = {
  date: string;
  time: string;
  geonameid?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  /** Keeps the place name on a chart cast from coordinates, e.g. a saved record. */
  place_name?: string | null;
  timezone?: string | null;
  fold?: number;
  ayanamsa?: string;
  vargas?: string[];
  name?: string | null;
};

/** An API error carrying the server's explanation, not a generic status code. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(
      `Cannot reach the Jyotish engine at ${API_BASE}. Is it running? ` +
        `Start it with:  uvicorn jyotish.api.app:app`,
      0,
    );
  }

  if (!response.ok) {
    // FastAPI puts the useful message in `detail`, which is either a string
    // (our own ValueError) or a list of field errors (Pydantic validation).
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        detail = body.detail
          .map((d: { loc?: string[]; msg?: string }) => {
            const field = d.loc?.filter((p) => p !== "body").join(".");
            return field ? `${field}: ${d.msg}` : d.msg;
          })
          .join("; ");
      }
    } catch {
      /* keep the status-code fallback */
    }
    throw new ApiError(detail, response.status);
  }

  // 204 has no body; calling .json() on it throws. DELETE returns 204.
  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function fetchMeta(): Promise<Meta> {
  return request<Meta>("/api/meta");
}

export function searchPlaces(
  query: string,
  signal?: AbortSignal,
): Promise<{ query: string; results: Place[] }> {
  return request(`/api/places?q=${encodeURIComponent(query)}&limit=10`, {
    signal,
  });
}

/** A saved birth in the library. */
export type SavedRecord = {
  id: number;
  name: string;
  notes: string;
  birth_date: string;
  birth_time: string;
  fold: number;
  ayanamsa: string;
  latitude: number;
  longitude: number;
  timezone_name: string;
  place_name: string;
  /** Provenance only — the coordinates above are the source of truth. */
  geonameid: number | null;
  vargas: string[];
  created_at: string;
  updated_at: string;
};

export type RecordInput = Omit<SavedRecord, "id" | "created_at" | "updated_at">;

export function listRecords(
  query = "",
): Promise<{ records: SavedRecord[]; total: number }> {
  return request(`/api/records?q=${encodeURIComponent(query)}`);
}

export function saveRecord(body: RecordInput): Promise<SavedRecord> {
  return request<SavedRecord>("/api/records", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateRecord(
  id: number,
  body: RecordInput,
): Promise<SavedRecord> {
  return request<SavedRecord>(`/api/records/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function deleteRecord(id: number): Promise<void> {
  // Routed through request() like everything else. A bare fetch here ignored
  // response.ok, so a 404 — or a CORS preflight rejection — was reported as
  // success and the row vanished from the list while surviving on disk.
  await request<void>(`/api/records/${id}`, { method: "DELETE" });
}

export function computeChart(body: ChartRequest): Promise<Chart> {
  return request<Chart>("/api/chart", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/* --- Vimshottari dasha ---------------------------------------------------- */

/** One dasha period at any of the five levels.
 *
 *  `start`/`end` are local wall-clock time at the *birth place*, which is the
 *  frame a printed dasha table uses. `start_utc`/`end_utc` are the same instants
 *  unambiguously, for arithmetic. */
export type DashaPeriod = {
  lords: number[];
  lord_names: Term[];
  level: number;
  level_name: Term;
  start: string;
  end: string;
  start_utc: string;
  end_utc: string;
  days: number;
  running: boolean;
  has_children: boolean;
};

export type DashaBalance = {
  lord: number;
  lord_name: Term;
  nakshatra: number;
  nakshatra_name: Term;
  remaining_fraction: number;
  years: number;
  months: number;
  days: number;
  formatted: string;
  formatted_ta: string;
};

export type Dasha = {
  balance: DashaBalance;
  year_length: string;
  year_days: number;
  path: number[];
  parent: DashaPeriod | null;
  periods: DashaPeriod[];
  running: DashaPeriod[];
  at: string;
  moon_longitude: number;
  timezone: string;
  engine_version: string;
};

export type DashaRequest = ChartRequest & {
  /** Lord chain to expand, outermost first. Empty gives the mahadashas. */
  path?: number[];
  /** Local date/datetime at the birth place to report as running. */
  at?: string | null;
  year_length?: string;
};

/** Fetches one level of the tree. The whole tree is never requested: five
 *  levels of nine lords is 59,049 periods, and the deepest are minutes long. */
export function computeDasha(body: DashaRequest): Promise<Dasha> {
  return request<Dasha>("/api/dasha", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/* --- panchangam ----------------------------------------------------------- */

/** One of the five limbs. `end` is the "until HH:MM" a Tamil almanac prints. */
export type Limb = {
  index: number;
  name: Term;
  start: string;
  end: string;
  start_utc: string;
  end_utc: string;
  elapsed: number;
};

/** A named span of the day: a kalam, or one gowri window. */
export type DayWindow = {
  name: Term;
  start: string;
  end: string;
  auspicious: boolean | null;
};

export type Panchangam = {
  moment: string;
  timezone: string;
  place_name: string | null;
  latitude: number;
  longitude: number;
  ayanamsa: string;

  sunrise: string | null;
  sunset: string | null;
  next_sunrise: string | null;
  moonrise: string | null;
  moonset: string | null;
  /** Anything but "normal" means no daylight interval, so the windows below
   *  that are fractions of one are absent rather than guessed. */
  daylight: "normal" | "always_up" | "always_down";

  vaara: number;
  vaara_name: Term;

  tithi: Limb;
  paksha: number;
  paksha_name: Term;
  nakshatra: Limb;
  yoga: Limb;
  karana: Limb;

  rahu_kalam: DayWindow | null;
  yamagandam: DayWindow | null;
  kuligai: DayWindow | null;
  gowri_day: DayWindow[];
  gowri_night: DayWindow[];
  nalla_neram: DayWindow[];

  tamil_month: number;
  tamil_month_name: Term;
  tamil_day: number;
  tamil_year: number;
  tamil_year_name: Term;
  ayana_name: Term;
  ritu_name: Term;

  engine_version: string;
};

export function computePanchangam(body: ChartRequest): Promise<Panchangam> {
  return request<Panchangam>("/api/panchangam", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
