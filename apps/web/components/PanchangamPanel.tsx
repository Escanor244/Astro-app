"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  type ChartRequest,
  type DayWindow,
  type Limb,
  type Panchangam,
  type Term,
  computePanchangam,
} from "@/lib/api";
import { formatPeriodDate, formatPeriodTime } from "@/lib/dasha-format";
import type { Language } from "./SouthIndianChart";

/**
 * பஞ்சாங்கம் — the five limbs and the day's windows, for the birth moment.
 *
 * Two things here are easy to misread and are therefore labelled rather than
 * left implicit.
 *
 * The **vaara is the sunrise-to-sunrise weekday**, not the calendar one. For a
 * birth between midnight and sunrise these differ, and every window on this
 * panel is keyed to the Jyotish one.
 *
 * **நல்ல நேரம் here is the auspicious gowri windows.** A printed Tamil tear-off
 * calendar prints fixed one-hour bands under the same heading, and they are
 * demonstrably not the same windows — two weekdays in seven land their printed
 * band on Soram or Rogam. Saying which definition is on screen is more useful
 * than silently picking one.
 */

type Props = {
  request: ChartRequest | null;
  lang: Language;
};

function label(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta : term.en;
}

function both(term: Term): string {
  return `${term.ta} · ${term.en}`;
}

/** "05:56" from a naive local ISO string, without letting Date reinterpret it. */
function clock(iso: string | null): string {
  return iso ? formatPeriodTime(iso) : "—";
}

/** Adds the date when a window ends on the following day, as night ones do. */
function span(w: DayWindow, dayStart: string | null): string {
  const crossesMidnight =
    dayStart !== null && w.end.slice(0, 10) !== dayStart.slice(0, 10);
  return `${clock(w.start)}–${clock(w.end)}${crossesMidnight ? "⁺" : ""}`;
}

function LimbRow({
  heading,
  limb,
  lang,
  moment,
}: {
  heading: string;
  limb: Limb;
  lang: Language;
  moment: string;
}) {
  const endsToday = limb.end.slice(0, 10) === moment.slice(0, 10);
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-3 border-b border-slate-100 py-2 dark:border-slate-800">
      <dt className="text-sm text-slate-500 dark:text-slate-400">{heading}</dt>
      <dd className="text-right">
        <span className="font-medium text-slate-900 dark:text-slate-100">
          {label(limb.name, lang)}
        </span>
        <span className="tabular ml-2 font-mono text-xs text-slate-500 dark:text-slate-400">
          {lang === "ta" ? "வரை" : "until"} {clock(limb.end)}
          {!endsToday && ` ${formatPeriodDate(limb.end)}`}
        </span>
      </dd>
    </div>
  );
}

function WindowRow({ w, lang, dayStart }: { w: DayWindow; lang: Language; dayStart: string | null }) {
  return (
    <li
      className={`flex items-baseline justify-between gap-3 rounded px-2 py-1 text-sm ${
        w.auspicious
          ? "bg-emerald-50 dark:bg-emerald-950/30"
          : w.auspicious === false
            ? "bg-rose-50 dark:bg-rose-950/30"
            : ""
      }`}
    >
      <span className="text-slate-700 dark:text-slate-200">
        {label(w.name, lang)}
      </span>
      <span className="tabular font-mono text-xs text-slate-600 dark:text-slate-400">
        {span(w, dayStart)}
      </span>
    </li>
  );
}

export function PanchangamPanel({ request, lang }: Props) {
  const [data, setData] = useState<Panchangam | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setError(null);
    if (!request) return;
    let cancelled = false;
    computePanchangam(request)
      .then((p) => !cancelled && setData(p))
      .catch(
        (e) =>
          !cancelled &&
          setError(
            e instanceof ApiError ? e.message : "Could not compute the panchangam.",
          ),
      );
    return () => {
      cancelled = true;
    };
  }, [request]);

  if (!request) return null;
  if (error) {
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
        {error}
      </div>
    );
  }
  if (!data) return <p className="text-sm text-slate-400">Computing panchangam…</p>;

  const kalams = [data.rahu_kalam, data.yamagandam, data.kuligai].filter(
    (w): w is DayWindow => w !== null,
  );

  return (
    <div className="space-y-5">
      {/* The Tamil date line an almanac opens with. */}
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-700 dark:bg-slate-800/50">
        <p className="font-medium text-slate-900 dark:text-slate-100">
          {data.tamil_year_name.ta} வருடம் · {data.tamil_month_name.ta}{" "}
          {data.tamil_day} · {data.vaara_name.ta}
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {data.tamil_year_name.en} year · {data.tamil_month_name.en}{" "}
          {data.tamil_day} · {data.vaara_name.en} · {both(data.ayana_name)} ·{" "}
          {both(data.ritu_name)}
        </p>
      </div>

      {data.daylight !== "normal" && (
        <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          The Sun neither rises nor sets here on this date (
          {data.daylight === "always_up" ? "midnight sun" : "polar night"}). Rahu
          kalam and the gowri windows are fractions of the interval between
          sunrise and sunset, so on this day they have no definition and are not
          shown. The five limbs are unaffected — they are longitudes.
        </p>
      )}

      <div className="grid gap-6 sm:grid-cols-2">
        {/* The five limbs. */}
        <div>
          <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
            பஞ்சாங்கம்{" "}
            <span className="font-normal text-slate-500">the five limbs</span>
          </h3>
          <dl>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 border-b border-slate-100 py-2 dark:border-slate-800">
              <dt className="text-sm text-slate-500 dark:text-slate-400">
                {lang === "ta" ? "கிழமை" : "Vaara"}
              </dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {label(data.vaara_name, lang)}
              </dd>
            </div>
            <LimbRow
              heading={
                (lang === "ta" ? "திதி" : "Tithi") +
                ` (${data.paksha_name.ta})`
              }
              limb={data.tithi}
              lang={lang}
              moment={data.moment}
            />
            <LimbRow
              heading={lang === "ta" ? "நட்சத்திரம்" : "Nakshatra"}
              limb={data.nakshatra}
              lang={lang}
              moment={data.moment}
            />
            <LimbRow
              heading={lang === "ta" ? "யோகம்" : "Yoga"}
              limb={data.yoga}
              lang={lang}
              moment={data.moment}
            />
            <LimbRow
              heading={lang === "ta" ? "கரணம்" : "Karana"}
              limb={data.karana}
              lang={lang}
              moment={data.moment}
            />
          </dl>

          <h3 className="mb-1 mt-5 font-semibold text-slate-900 dark:text-slate-100">
            {lang === "ta" ? "உதயம் / அஸ்தமனம்" : "Rise and set"}
          </h3>
          <dl className="text-sm">
            {[
              ["சூரிய உதயம் · Sunrise", data.sunrise],
              ["சூரிய அஸ்தமனம் · Sunset", data.sunset],
              ["சந்திர உதயம் · Moonrise", data.moonrise],
              ["சந்திர அஸ்தமனம் · Moonset", data.moonset],
            ].map(([heading, value]) => (
              <div
                key={heading as string}
                className="flex justify-between gap-3 border-b border-slate-100 py-1.5 dark:border-slate-800"
              >
                <dt className="text-slate-500 dark:text-slate-400">{heading}</dt>
                <dd className="tabular font-mono">{clock(value as string | null)}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* The windows. */}
        <div>
          {kalams.length > 0 && (
            <>
              <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
                {lang === "ta" ? "தீய நேரம்" : "Periods to avoid"}
              </h3>
              <ul className="mb-5 space-y-1">
                {kalams.map((w) => (
                  <WindowRow
                    key={w.name.en}
                    w={w}
                    lang={lang}
                    dayStart={data.sunrise}
                  />
                ))}
              </ul>
            </>
          )}

          {data.gowri_day.length > 0 && (
            <>
              <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
                கௌரி பஞ்சாங்கம்{" "}
                <span className="font-normal text-slate-500">— பகல் (day)</span>
              </h3>
              <ul className="space-y-0.5">
                {data.gowri_day.map((w, i) => (
                  <WindowRow
                    key={`d${i}`}
                    w={w}
                    lang={lang}
                    dayStart={data.sunrise}
                  />
                ))}
              </ul>
            </>
          )}

          {data.gowri_night.length > 0 && (
            <>
              <h3 className="mb-1 mt-4 font-semibold text-slate-900 dark:text-slate-100">
                கௌரி பஞ்சாங்கம்{" "}
                <span className="font-normal text-slate-500">— இரவு (night)</span>
              </h3>
              <ul className="space-y-0.5">
                {data.gowri_night.map((w, i) => (
                  <WindowRow
                    key={`n${i}`}
                    w={w}
                    lang={lang}
                    dayStart={data.sunset}
                  />
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      {data.nalla_neram.length > 0 && (
        <p className="text-xs text-slate-500 dark:text-slate-400">
          <strong className="text-slate-700 dark:text-slate-300">
            நல்ல நேரம்
          </strong>{" "}
          on this page means the auspicious gowri windows above — அமிர்தம்,
          லாபம், தனம், சுகம் and உத்தியோகம். A printed tear-off Tamil calendar
          prints fixed one-hour bands under the same heading, and those are not
          the same windows.
        </p>
      )}
    </div>
  );
}
