"use client";

import type { Chart, DignityState, Term } from "@/lib/api";
import type { Language } from "./SouthIndianChart";

/** Colour by how well the graha is placed, so the two extremes read at a
 *  glance — which is how they read on a printed jathagam. */
const DIGNITY_STYLE: Record<DignityState, string> = {
  exalted:
    "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-300",
  moolatrikona:
    "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-400",
  own: "bg-sky-50 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300",
  great_friend: "bg-sky-50 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300",
  friend: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  neutral: "text-slate-500 dark:text-slate-400",
  enemy: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
  debilitated: "bg-rose-100 text-rose-900 dark:bg-rose-950 dark:text-rose-300",
  undefined: "text-slate-400 dark:text-slate-500",
};

/**
 * The planetary positions table.
 *
 * Shows degree-within-rasi, nakshatra and pada for every graha, because those
 * are what a practising astrologer checks first and what they will diff against
 * Jagannatha Hora. Retrogradation is marked, but not for Rahu and Ketu: the
 * mean nodes are always retrograde, so flagging them is noise rather than
 * information.
 */

type Props = {
  chart: Chart;
  lang: Language;
  onHover?: (graha: number | null) => void;
};

function label(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta : term.en;
}

export function GrahaTable({ chart, lang, onHover }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[34rem] text-base">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <th className="py-2 pr-3 font-medium">Graha</th>
            <th className="py-2 pr-3 font-medium">Rasi</th>
            <th className="py-2 pr-3 text-right font-medium">Degree</th>
            <th className="py-2 pr-3 font-medium">Nakshatra</th>
            <th className="py-2 pr-3 text-center font-medium">Pada</th>
            <th className="py-2 pr-3 text-center font-medium">Bhava</th>
            <th className="py-2 pr-3 font-medium">
              {lang === "ta" ? "நிலை" : "Dignity"}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20">
            <td className="py-2 pr-3 font-semibold text-amber-800 dark:text-amber-400">
              {lang === "ta" ? "லக்னம்" : "Lagna"}
            </td>
            <td className="py-2 pr-3">{label(chart.lagna.rasi_name, lang)}</td>
            <td className="tabular py-2.5 pr-3 text-right font-mono text-sm">
              {chart.lagna.formatted}
            </td>
            <td className="py-2 pr-3">
              {label(chart.lagna.nakshatra_name, lang)}
            </td>
            <td className="py-2 pr-3 text-center">{chart.lagna.pada}</td>
            <td className="py-2 pr-3 text-center">1</td>
            {/* The lagna is a point, not a graha, so it has no dignity. */}
            <td className="py-2 pr-3 text-slate-300 dark:text-slate-600">—</td>
          </tr>

          {chart.grahas.map((g) => {
            // Rahu and Ketu are always retrograde; marking them says nothing.
            const showRetro = g.retrograde && g.graha !== 7 && g.graha !== 8;
            return (
              <tr
                key={g.graha}
                onMouseEnter={() => onHover?.(g.graha)}
                onMouseLeave={() => onHover?.(null)}
                className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <td className="py-2 pr-3">
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    {g.name.en}
                  </span>
                  <span className="ml-2 text-slate-500 dark:text-slate-400">
                    {g.name.ta}
                  </span>
                  {showRetro && (
                    <span
                      title="Retrograde · வக்ரம்"
                      className="ml-2 rounded bg-rose-100 px-1 text-xs font-semibold text-rose-700 dark:bg-rose-950 dark:text-rose-400"
                    >
                      ℞
                    </span>
                  )}
                  {g.combust && (
                    <span
                      title={`Combust · அஸ்தங்கதம் — within ${Math.abs(
                        g.position.longitude - chart.grahas[0].position.longitude,
                      ).toFixed(0)}° of the Sun`}
                      className="ml-1 rounded bg-orange-100 px-1 text-xs font-semibold text-orange-800 dark:bg-orange-950 dark:text-orange-400"
                    >
                      ☌
                    </span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {label(g.position.rasi_name, lang)}
                </td>
                <td className="tabular py-2.5 pr-3 text-right font-mono text-sm">
                  {g.position.formatted}
                </td>
                <td className="py-2 pr-3">
                  {label(g.position.nakshatra_name, lang)}
                  <span className="ml-1 text-xs text-slate-400">
                    ({g.position.nakshatra_lord_name.en})
                  </span>
                </td>
                <td className="py-2 pr-3 text-center">{g.position.pada}</td>
                <td className="py-2 pr-3 text-center">{g.house}</td>
                <td className="py-2 pr-3">
                  {g.dignity === "undefined" ? (
                    <span
                      className="text-slate-300 dark:text-slate-600"
                      title={g.dignity_reason}
                    >
                      —
                    </span>
                  ) : (
                    <span
                      title={g.dignity_reason}
                      className={`inline-block cursor-help rounded px-1.5 py-0.5 text-sm ${DIGNITY_STYLE[g.dignity]}`}
                    >
                      {label(g.dignity_name, lang)}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
