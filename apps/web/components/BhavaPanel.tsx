"use client";

import { useState } from "react";
import type { Chart, Sevvai, Term } from "@/lib/api";
import type { Language } from "./SouthIndianChart";

/**
 * பாவகங்கள் and செவ்வாய் தோஷம்.
 *
 * Two panels that share a concern: showing the *inputs* an astrologer reads,
 * rather than a conclusion drawn for them.
 *
 * The bhava table can be read from the lagna (லக்னப்படி) or from the Moon
 * (ராசிப்படி), which Tamil practice does as a matter of course. Note the
 * wording — no Tamil source writes "சந்திர லக்னம்"; see docs/bhava-sources.md.
 *
 * The sevvai panel deliberately renders **no verdict**. Three incompatible Tamil
 * house sets are in mainstream use, and one practitioner's exception list takes
 * a hundred flagged charts down to three — so a yes/no would be reporting our
 * choice of exception list, with this app's name on it, to someone asking about
 * their marriage. It shows where Mars is, which conventions flag it, and which
 * exemptions apply. Do not add a summary line.
 */

type Props = {
  chart: Chart;
  lang: Language;
};

function label(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta : term.en;
}

const GROUP_STYLE: Record<string, string> = {
  kendra: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  trikona:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  upachaya:
    "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  dusthana: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
};

const CONVENTION_LABEL: Record<string, string> = {
  tamil_common: "Tamil (common)",
  tamil_traditional: "Tamil (பாரம்பரிய)",
  classical: "Classical",
};

function SevvaiPanel({ sevvai, lang }: { sevvai: Sevvai; lang: Language }) {
  const active = sevvai.exemptions.filter((e) => e.applies);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-semibold text-slate-900 dark:text-slate-100">
          {sevvai.name.ta}{" "}
          <span className="font-normal text-slate-500">{sevvai.name.en}</span>
        </h3>
        <span className="text-sm text-slate-500 dark:text-slate-400">
          செவ்வாய் in {label(sevvai.mars_rasi_name, lang)}
        </span>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <th className="py-1.5 pr-3 font-medium">Counted from</th>
            <th className="py-1.5 pr-3 text-center font-medium">House</th>
            <th className="py-1.5 pr-3 font-medium">Flagged by</th>
          </tr>
        </thead>
        <tbody>
          {sevvai.readings.map((r) => (
            <tr
              key={r.reference}
              className="border-b border-slate-100 dark:border-slate-800"
            >
              <td className="py-1.5 pr-3">
                {label(r.reference_name, lang)}
                {r.reference === "lagna" && (
                  <span className="ml-1 text-xs text-slate-400">(primary)</span>
                )}
              </td>
              <td
                className={`tabular py-1.5 pr-3 text-center font-mono ${
                  r.severe ? "font-semibold text-rose-700 dark:text-rose-400" : ""
                }`}
              >
                {r.house}
              </td>
              <td className="py-1.5 pr-3">
                {r.flagged_by.length === 0 ? (
                  <span className="text-slate-400">—</span>
                ) : (
                  <span className="flex flex-wrap gap-1">
                    {r.flagged_by.map((c) => (
                      <span
                        key={c}
                        title={`houses ${sevvai.house_sets[c]?.join(", ")}`}
                        className="cursor-help rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-300"
                      >
                        {CONVENTION_LABEL[c] ?? c}
                      </span>
                    ))}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div>
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          விதிவிலக்குகள்{" "}
          <span className="font-normal text-slate-500">
            exemptions — {active.length} of {sevvai.exemptions.length} apply
          </span>
        </h4>
        <ul className="mt-1 space-y-1">
          {sevvai.exemptions.map((e) => (
            <li
              key={e.key}
              className={`rounded px-2 py-1 text-sm ${
                e.applies
                  ? "bg-emerald-50 dark:bg-emerald-950/30"
                  : "text-slate-400 dark:text-slate-500"
              }`}
            >
              <span className="font-medium">{e.applies ? "✓" : "—"}</span>{" "}
              {label(e.name, lang)}
              <span
                title={e.provenance}
                className="ml-1 cursor-help text-xs text-slate-400"
              >
                ⓘ
              </span>
              {e.applies && (
                <p className="ml-4 text-xs text-slate-600 dark:text-slate-400">
                  {e.detail}
                </p>
              )}
            </li>
          ))}
        </ul>
      </div>

      <p className="rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400">
        <strong className="text-slate-700 dark:text-slate-300">
          No verdict is shown, and that is deliberate.
        </strong>{" "}
        Three incompatible Tamil house sets are in mainstream use, and one
        practitioner&rsquo;s exception list reduces a hundred flagged charts to
        three. A yes or no here would report a choice of exception list rather
        than the chart. See <code>docs/dosham-sources.md</code>.
      </p>
    </div>
  );
}

export function BhavaPanel({ chart, lang }: Props) {
  const [fromMoon, setFromMoon] = useState(false);
  const houses = fromMoon ? chart.bhavas_from_moon : chart.bhavas;
  const grahaName = (i: number) =>
    lang === "ta" ? chart.grahas[i]?.name.ta_short : chart.grahas[i]?.name.en_short;

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
            பாவகங்கள்{" "}
            <span className="font-normal text-slate-500">the twelve houses</span>
          </h3>
          {/* லக்னப்படி / ராசிப்படி — the two reading passes, in the words Tamil
              uses. Not "Chandra lagna", which no Tamil source writes. */}
          <div
            role="group"
            aria-label="Count houses from"
            className="no-print flex overflow-hidden rounded-md border border-slate-300 text-sm dark:border-slate-600"
          >
            {[
              { on: false, ta: "லக்னப்படி", en: "from lagna" },
              { on: true, ta: "ராசிப்படி", en: "from the Moon" },
            ].map((opt) => (
              <button
                key={String(opt.on)}
                onClick={() => setFromMoon(opt.on)}
                aria-pressed={fromMoon === opt.on}
                className={`px-3 py-1 transition ${
                  fromMoon === opt.on
                    ? "bg-amber-600 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                }`}
              >
                {lang === "ta" ? opt.ta : opt.en}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-400">
                <th className="py-2 pr-3 font-medium">#</th>
                <th className="py-2 pr-3 font-medium">House</th>
                <th className="py-2 pr-3 font-medium">Rasi</th>
                <th className="py-2 pr-3 font-medium">Lord</th>
                <th className="py-2 pr-3 font-medium">In it</th>
                <th className="py-2 pr-3 font-medium">Aspected by</th>
              </tr>
            </thead>
            <tbody>
              {houses.map((h) => (
                <tr
                  key={h.number}
                  className="border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="tabular py-2 pr-3 font-mono">{h.number}</td>
                  <td className="py-2 pr-3">
                    <span title={h.signification} className="cursor-help">
                      {label(h.name, lang)}
                    </span>
                    {h.groups.map((g, i) => (
                      <span
                        key={g}
                        className={`ml-1 rounded px-1 text-xs ${GROUP_STYLE[g] ?? ""}`}
                      >
                        {label(h.group_names[i], lang)}
                      </span>
                    ))}
                  </td>
                  <td className="py-2 pr-3">{label(h.rasi_name, lang)}</td>
                  <td className="py-2 pr-3">{label(h.lord_name, lang)}</td>
                  <td className="py-2 pr-3">
                    {h.occupants.map(grahaName).join(" ") || (
                      <span className="text-slate-300 dark:text-slate-600">—</span>
                    )}
                  </td>
                  <td className="py-2 pr-3 text-slate-500 dark:text-slate-400">
                    {h.aspected_by.map(grahaName).join(" ") || (
                      <span className="text-slate-300 dark:text-slate-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-2 text-xs text-slate-400">
          {lang === "ta" ? "பாதகாதிபதி" : "Badhaka lord"}:{" "}
          {grahaName(chart.badhaka_lord)} ({chart.badhaka_house}
          {lang === "ta" ? "ஆம் பாவகம்" : "th house"}) ·{" "}
          {lang === "ta" ? "மாரகாதிபதி" : "Maraka lords"}:{" "}
          {chart.maraka_lords.map(grahaName).join(", ")}
          {chart.lagna_vargottama && " · லக்னம் வர்க்கோத்தமம்"}
        </p>
      </div>

      <div className="border-t border-slate-200 pt-5 dark:border-slate-700">
        <SevvaiPanel sevvai={chart.sevvai} lang={lang} />
      </div>
    </div>
  );
}
