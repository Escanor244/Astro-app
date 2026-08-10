"use client";

import type { Chart, Term } from "@/lib/api";
import type { Language } from "./SouthIndianChart";

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
      <table className="w-full min-w-[34rem] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <th className="py-2 pr-3 font-medium">Graha</th>
            <th className="py-2 pr-3 font-medium">Rasi</th>
            <th className="py-2 pr-3 text-right font-medium">Degree</th>
            <th className="py-2 pr-3 font-medium">Nakshatra</th>
            <th className="py-2 pr-3 text-center font-medium">Pada</th>
            <th className="py-2 pr-3 text-center font-medium">Bhava</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20">
            <td className="py-2 pr-3 font-semibold text-amber-800 dark:text-amber-400">
              {lang === "ta" ? "லக்னம்" : "Lagna"}
            </td>
            <td className="py-2 pr-3">{label(chart.lagna.rasi_name, lang)}</td>
            <td className="py-2 pr-3 text-right font-mono text-xs">
              {chart.lagna.formatted}
            </td>
            <td className="py-2 pr-3">
              {label(chart.lagna.nakshatra_name, lang)}
            </td>
            <td className="py-2 pr-3 text-center">{chart.lagna.pada}</td>
            <td className="py-2 pr-3 text-center">1</td>
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
                      title="Retrograde"
                      className="ml-2 rounded bg-rose-100 px-1 text-xs font-semibold text-rose-700 dark:bg-rose-950 dark:text-rose-400"
                    >
                      ℞
                    </span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {label(g.position.rasi_name, lang)}
                </td>
                <td className="py-2 pr-3 text-right font-mono text-xs">
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
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
