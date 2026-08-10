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

export type Term = { en: string; ta: string; ta_latin: string };

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

export type Graha = {
  graha: number;
  name: Term;
  sanskrit: string;
  position: ZodiacPosition;
  house: number;
  retrograde: boolean;
  speed_deg_per_day: number;
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
  grahas: Graha[];
  charts: VargaChart[];
  time_warning: string | null;
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

export function computeChart(body: ChartRequest): Promise<Chart> {
  return request<Chart>("/api/chart", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
