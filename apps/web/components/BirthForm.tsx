"use client";

import { useState } from "react";
import type { Meta, Place } from "@/lib/api";
import { AyanamsaInfo } from "./AyanamsaInfo";
import { PlaceSearch } from "./PlaceSearch";
import type { Language } from "./SouthIndianChart";

export type FormState = {
  name: string;
  date: string;
  time: string;
  place: Place | null;
  ayanamsa: string;
  vargas: string[];
  fold: number;
};

/** The vargas offered up front. The rest are behind "show all sixteen". */
const COMMON = ["D1", "D9", "D10", "D2", "D3", "D7", "D12", "D30"];

type Props = {
  meta: Meta | null;
  value: FormState;
  onChange: (next: FormState) => void;
  onSubmit: () => void;
  busy: boolean;
  lang: Language;
};

export function BirthForm({ meta, value, onChange, onSubmit, busy, lang }: Props) {
  const [showAllVargas, setShowAllVargas] = useState(false);

  const set = <K extends keyof FormState>(key: K, v: FormState[K]) =>
    onChange({ ...value, [key]: v });

  function toggleVarga(code: string) {
    const has = value.vargas.includes(code);
    // Always leave at least one chart selected; an empty grid is not a state
    // the user can do anything useful with.
    if (has && value.vargas.length === 1) return;
    const next = has
      ? value.vargas.filter((c) => c !== code)
      : [...value.vargas, code];
    // Keep the canonical order rather than click order, so D1 stays first.
    const order = meta?.vargas.map((v) => v.code) ?? next;
    set("vargas", [...next].sort((a, b) => order.indexOf(a) - order.indexOf(b)));
  }

  const offered = showAllVargas
    ? (meta?.vargas.map((v) => v.code) ?? COMMON)
    : COMMON;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="space-y-4"
    >
      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          Name <span className="text-slate-400">(optional)</span>
        </label>
        <input
          id="name"
          type="text"
          value={value.name}
          onChange={(e) => set("name", e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 shadow-sm outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label
            htmlFor="date"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Birth date
          </label>
          <input
            id="date"
            type="date"
            required
            value={value.date}
            onChange={(e) => set("date", e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 shadow-sm outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
        </div>
        <div>
          <label
            htmlFor="time"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Birth time
          </label>
          <input
            id="time"
            type="time"
            step={1}
            required
            value={value.time}
            onChange={(e) => set("time", e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 shadow-sm outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
          {/* A 24-hour picker removes the AM/PM trap at the source: there is no
              ambiguous reading to mis-enter. The result header still echoes the
              12-hour form so the user can confirm it. */}
          <p className="mt-1 text-xs text-slate-400">24-hour · 18:30 = 6:30 PM</p>
        </div>
      </div>

      <PlaceSearch value={value.place} onChange={(p) => set("place", p)} />

      <div>
        <label
          htmlFor="ayanamsa"
          className="flex items-center text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          Ayanamsa <span className="ml-1 text-slate-400">/ அயனாம்சம்</span>
          <AyanamsaInfo />
        </label>
        <select
          id="ayanamsa"
          value={value.ayanamsa}
          onChange={(e) => set("ayanamsa", e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 shadow-sm outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          {(meta?.ayanamsas ?? ["lahiri"]).map((a) => (
            <option key={a} value={a}>
              {a === "lahiri"
                ? "Lahiri (Chitrapaksha) — India's standard"
                : a === "kp"
                  ? "KP (Krishnamurti) — required for KP work"
                  : a === "true_chitrapaksha"
                    ? "True Chitrapaksha (Spica-based)"
                    : "Raman"}
            </option>
          ))}
        </select>
      </div>

      <fieldset>
        <legend className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Charts
        </legend>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {offered.map((code) => {
            const info = meta?.vargas.find((v) => v.code === code);
            const on = value.vargas.includes(code);
            return (
              <button
                key={code}
                type="button"
                onClick={() => toggleVarga(code)}
                aria-pressed={on}
                title={info ? `${info.name.en} — ${info.significance}` : code}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
                  on
                    ? "bg-amber-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                }`}
              >
                {code}
                {info && (
                  <span className="ml-1 opacity-70">
                    {lang === "ta" ? info.name.ta : info.name.en}
                  </span>
                )}
              </button>
            );
          })}
        </div>
        {meta && meta.vargas.length > COMMON.length && (
          <button
            type="button"
            onClick={() => setShowAllVargas((v) => !v)}
            className="mt-2 text-xs text-amber-700 underline dark:text-amber-500"
          >
            {showAllVargas
              ? "Show fewer"
              : `Show all ${meta.vargas.length} (Shodashavarga)`}
          </button>
        )}
      </fieldset>

      <button
        type="submit"
        disabled={busy || !value.place}
        className="w-full rounded-md bg-amber-600 px-4 py-2.5 font-semibold text-white shadow-sm transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
      >
        {busy ? "Calculating…" : value.place ? "Cast chart" : "Choose a birth place"}
      </button>
    </form>
  );
}
