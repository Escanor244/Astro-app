"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  type ChartRequest,
  type Dasha,
  type DashaPeriod,
  type Term,
  computeDasha,
} from "@/lib/api";
import {
  formatDuration,
  formatPeriodDate,
  formatPeriodTime,
  isPast,
} from "@/lib/dasha-format";
import type { Language } from "./SouthIndianChart";

/**
 * The Vimshottari dasha table, drilled one level at a time.
 *
 * The tree is never fetched whole. Five levels of nine lords is 59,049 periods
 * and the deepest are minutes long, so each click asks the engine for one node's
 * children by sending the chain of lords above it. That also keeps the levels
 * consistent: the client never does dasha arithmetic of its own, so it cannot
 * drift from the engine.
 *
 * Two things sit above the table because they are what a consultation opens
 * with: the **balance at birth** (திசை இருப்பு), which is printed on every
 * Tamil horoscope and never changes, and the **chain running right now**, which
 * is the actual question being asked.
 */

type Props = {
  request: ChartRequest | null;
  lang: Language;
};

function label(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta : term.en;
}

function pathLabel(period: DashaPeriod, lang: Language): string {
  return period.lord_names.map((t) => label(t, lang)).join(" / ");
}

export function DashaTree({ request, lang }: Props) {
  const [data, setData] = useState<Dasha | null>(null);
  const [path, setPath] = useState<number[]>([]);
  const [at, setAt] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Every request carries a sequence number and only the newest may write.
  // Without this a slow reply can land after a newer one and paint a different
  // chart's dasha under the chart on screen — the two requests differ only in
  // the birth in the body, so nothing about the result looks wrong. Opening two
  // library records in quick succession is enough to trigger it.
  const latest = useRef(0);

  const load = useCallback(
    async (nextPath: number[], nextAt: string) => {
      if (!request) return;
      const ticket = ++latest.current;
      setBusy(true);
      setError(null);
      try {
        const next = await computeDasha({
          ...request,
          path: nextPath,
          at: nextAt || null,
        });
        if (ticket !== latest.current) return;
        setData(next);
        setPath(nextPath);
      } catch (e) {
        if (ticket !== latest.current) return;
        setError(
          e instanceof ApiError ? e.message : "Could not compute the dasha.",
        );
      } finally {
        if (ticket === latest.current) setBusy(false);
      }
    },
    [request],
  );

  // A new birth invalidates the whole tree, so drop back to the mahadashas
  // rather than trying to keep a path that belonged to a different chart.
  useEffect(() => {
    setPath([]);
    setData(null);
    if (request) void load([], at);
    // `at` is deliberately excluded: changing the date should not reset the
    // level the user has drilled to.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [request, load]);

  if (!request) return null;

  if (error) {
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <p className="text-sm text-slate-400">Computing dasha periods…</p>
    );
  }

  const { balance } = data;

  return (
    <div className="space-y-5">
      {/* Balance at birth — printed on every Tamil horoscope, fixed for life. */}
      <div className="rounded-md border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/60 dark:bg-amber-950/30">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h3 className="font-semibold text-amber-900 dark:text-amber-300">
            {lang === "ta" ? "திசை இருப்பு" : "Dasha balance at birth"}
          </h3>
          <p className="text-lg font-semibold text-amber-900 dark:text-amber-200">
            {label(balance.lord_name, lang)}{" "}
            <span className="tabular font-mono text-base">
              {balance.years}y {balance.months}m {balance.days}d
            </span>
          </p>
        </div>
        <p className="mt-1 text-sm text-amber-800 dark:text-amber-400/90">
          Born in {label(balance.nakshatra_name, lang)}, with{" "}
          {(balance.remaining_fraction * 100).toFixed(1)}% of the star still to
          cross. That fraction <em>is</em> the balance.
        </p>
      </div>

      {/* What is running. The question a consultation actually asks. */}
      <div className="rounded-md border border-slate-200 p-4 dark:border-slate-700">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
            {lang === "ta" ? "நடப்பு திசை" : "Running"}
          </h3>
          <label className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            on
            <input
              type="date"
              value={at || data.at.slice(0, 10)}
              onChange={(e) => {
                setAt(e.target.value);
                void load(path, e.target.value);
              }}
              className="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
            />
          </label>
        </div>

        {data.running.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            That date falls outside the 120-year cycle from this birth.
          </p>
        ) : (
          <ol className="space-y-1">
            {data.running.map((p) => (
              <li
                key={p.lords.join("-")}
                className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 text-sm"
              >
                <span className="w-32 shrink-0 text-xs uppercase tracking-wide text-slate-400">
                  {label(p.level_name, lang)}
                </span>
                <span className="min-w-24 font-medium text-slate-900 dark:text-slate-100">
                  {label(p.lord_names[p.lords.length - 1], lang)}
                </span>
                <span className="tabular font-mono text-xs text-slate-500 dark:text-slate-400">
                  {formatPeriodDate(p.start)} → {formatPeriodDate(p.end)}
                  {p.level >= 4 && (
                    <span className="ml-1">
                      ({formatPeriodTime(p.start)}–{formatPeriodTime(p.end)})
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>

      {/* The drill-down table. */}
      <div>
        <nav className="mb-2 flex flex-wrap items-center gap-1 text-sm">
          <button
            type="button"
            onClick={() => void load([], at)}
            className={`rounded px-2 py-0.5 ${
              path.length === 0
                ? "font-semibold text-slate-900 dark:text-slate-100"
                : "text-amber-700 hover:underline dark:text-amber-400"
            }`}
          >
            {lang === "ta" ? "மகா தசை" : "Mahadasha"}
          </button>
          {path.map((lord, i) => (
            <span key={`${lord}-${i}`} className="flex items-center gap-1">
              <span className="text-slate-400">›</span>
              <button
                type="button"
                onClick={() => void load(path.slice(0, i + 1), at)}
                className={`rounded px-2 py-0.5 ${
                  i === path.length - 1
                    ? "font-semibold text-slate-900 dark:text-slate-100"
                    : "text-amber-700 hover:underline dark:text-amber-400"
                }`}
              >
                {data.parent
                  ? label(data.parent.lord_names[i], lang)
                  : `#${lord}`}
              </button>
            </span>
          ))}
          {busy && <span className="ml-2 text-xs text-slate-400">…</span>}
        </nav>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[30rem] text-base">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-400">
                <th className="py-2 pr-3 font-medium">
                  {data.periods[0]
                    ? label(data.periods[0].level_name, lang)
                    : "Period"}
                </th>
                <th className="py-2 pr-3 font-medium">From</th>
                <th className="py-2 pr-3 font-medium">To</th>
                <th className="py-2 pr-3 text-right font-medium">Length</th>
                <th className="py-2 w-6" />
              </tr>
            </thead>
            <tbody>
              {data.periods.map((p) => {
                const lord = p.lords[p.lords.length - 1];
                const past = isPast(p, data.at);
                return (
                  <tr
                    key={p.lords.join("-")}
                    onClick={() =>
                      p.has_children && void load([...path, lord], at)
                    }
                    className={[
                      "border-b border-slate-100 dark:border-slate-800",
                      p.has_children ? "cursor-pointer" : "",
                      p.running
                        ? "bg-amber-50 font-medium dark:bg-amber-950/30"
                        : "hover:bg-slate-50 dark:hover:bg-slate-800/50",
                      past && !p.running
                        ? "text-slate-400 dark:text-slate-500"
                        : "",
                    ].join(" ")}
                  >
                    <td className="py-2 pr-3">
                      {label(p.lord_names[p.lords.length - 1], lang)}
                      {p.running && (
                        <span className="ml-2 rounded bg-amber-600 px-1.5 py-0.5 text-xs font-semibold text-white">
                          {lang === "ta" ? "நடப்பு" : "now"}
                        </span>
                      )}
                    </td>
                    {/* Sookshma runs for hours and prana for minutes, so at
                        those levels a date alone renders every row as
                        "10 Nov 1989 → 10 Nov 1989" — the same day twice, with
                        the actual period invisible. */}
                    <td className="tabular py-2 pr-3 font-mono text-sm">
                      {formatPeriodDate(p.start)}
                      {p.level >= 4 && (
                        <span className="ml-1 text-slate-500">
                          {formatPeriodTime(p.start)}
                        </span>
                      )}
                    </td>
                    <td className="tabular py-2 pr-3 font-mono text-sm">
                      {formatPeriodDate(p.end)}
                      {p.level >= 4 && (
                        <span className="ml-1 text-slate-500">
                          {formatPeriodTime(p.end)}
                        </span>
                      )}
                    </td>
                    <td className="tabular py-2 pr-3 text-right font-mono text-sm">
                      {formatDuration(p.days)}
                    </td>
                    <td className="py-2 text-slate-300 dark:text-slate-600">
                      {p.has_children ? "›" : ""}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="mt-2 text-xs text-slate-400">
          {path.length < 4
            ? "Click any row to open its sub-periods."
            : "Prana is the fifth and last level."}{" "}
          Dates are local time at the birth place ({data.timezone}), on a{" "}
          {data.year_length} dasha year of {data.year_days} days.
        </p>
      </div>
    </div>
  );
}
