"use client";

import { useEffect, useState } from "react";
import { ApiError, type Chart, type Meta, computeChart, fetchMeta } from "@/lib/api";
import { BirthForm, type FormState } from "@/components/BirthForm";
import { GrahaTable } from "@/components/GrahaTable";
import { type Language, SouthIndianChart } from "@/components/SouthIndianChart";
import { ThemeToggle } from "@/components/ThemeToggle";

const INITIAL: FormState = {
  name: "",
  date: "1990-05-15",
  time: "06:30",
  place: null,
  ayanamsa: "lahiri",
  vargas: ["D1", "D9"],
  fold: 0,
};

export default function Home() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(INITIAL);
  const [chart, setChart] = useState<Chart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lang, setLang] = useState<Language>("en");
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    fetchMeta()
      .then(setMeta)
      .catch((e) => setMetaError(e instanceof ApiError ? e.message : String(e)));
  }, []);

  async function cast(fold = form.fold) {
    if (!form.place) return;
    setBusy(true);
    setError(null);
    try {
      setChart(
        await computeChart({
          date: form.date,
          time: form.time,
          geonameid: form.place.geonameid,
          ayanamsa: form.ayanamsa,
          vargas: form.vargas,
          fold,
          name: form.name || null,
        }),
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
      setChart(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">
            ஜாதகம் <span className="text-slate-400">·</span> Jathagam
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Vedic chart calculation — sidereal, South Indian, Tamil-native.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500 dark:text-slate-400">Labels</span>
            <div
              role="group"
              aria-label="Label language"
              className="flex overflow-hidden rounded-md border border-slate-300 dark:border-slate-600"
            >
              {(["en", "ta"] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  aria-pressed={lang === l}
                  className={`px-3 py-1 text-sm transition ${
                    lang === l
                      ? "bg-amber-600 text-white"
                      : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`}
                >
                  {l === "en" ? "English" : "தமிழ்"}
                </button>
              ))}
            </div>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {metaError && (
        <div className="mb-6 rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Cannot reach the engine</p>
          <p className="mt-1 whitespace-pre-line">{metaError}</p>
        </div>
      )}

      {/* min-w-0 on both grid items is load-bearing, not cosmetic. A CSS grid
          item defaults to min-width:auto, so the track refuses to shrink below
          its content's min-content width — the graha table's six columns of
          unbreakable text forced a 580px track inside a 343px grid, and the
          overflow escaped the table's own overflow-x-auto to become
          document-level horizontal scroll. On a 375px phone the chart's entire
          right-hand column sat off-screen. */}
      <div className="grid gap-8 lg:grid-cols-[22rem_1fr]">
        <section className="min-w-0 rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <BirthForm
            meta={meta}
            value={form}
            onChange={setForm}
            onSubmit={() => cast()}
            busy={busy}
            lang={lang}
          />
        </section>

        <section className="min-w-0 space-y-6">
          {error && (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
              {error}
            </div>
          )}

          {!chart && !error && (
            <div className="rounded-lg border border-dashed border-slate-300 p-12 text-center text-slate-400 dark:border-slate-700">
              <p>Enter birth details to cast a chart.</p>
              <p className="mt-2 text-xs">
                Place search accepts Tamil — try மதுரை.
              </p>
            </div>
          )}

          {chart && (
            <>
              {/* The offset actually applied, and why. A historical offset
                  moves the lagna about a rasi, so it is shown, not buried. */}
              <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm shadow-sm dark:border-slate-700 dark:bg-slate-900">
                <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500 dark:text-slate-400">Birth</dt>
                    <dd className="text-right font-medium">
                      {chart.birth.local_datetime.replace("T", " ")}{" "}
                      <span className="text-slate-500">
                        ({chart.birth.time_12h})
                      </span>
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500 dark:text-slate-400">Place</dt>
                    <dd className="text-right font-medium">
                      {chart.birth.place_name ??
                        `${chart.birth.latitude.toFixed(4)}, ${chart.birth.longitude.toFixed(4)}`}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500 dark:text-slate-400">Zone</dt>
                    <dd className="text-right font-medium">
                      {chart.birth.timezone} · {chart.birth.utc_offset}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500 dark:text-slate-400">
                      Ayanamsa
                    </dt>
                    <dd className="text-right font-mono text-xs">
                      {chart.ayanamsa} {chart.ayanamsa_formatted}
                    </dd>
                  </div>
                </dl>
                {chart.birth.offset_note && (
                  <p className="mt-2 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                    {chart.birth.offset_note}
                  </p>
                )}
              </div>

              {/* An hour of doubt is ~15 degrees of lagna. Never silent.
                  The toggle appears only for an *ambiguous* time, which is the
                  only kind with a second reading. A time that never existed has
                  exactly one interpretation, and offering to switch it would
                  invite the user into a choice that is not real. */}
              {chart.time_warning && (
                <div className="rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
                  <p className="font-semibold">Check this birth time</p>
                  <p className="mt-1">{chart.time_warning}</p>
                  {chart.time_warning_kind === "ambiguous" && (
                    <button
                      onClick={() => {
                        const next = form.fold === 0 ? 1 : 0;
                        setForm({ ...form, fold: next });
                        cast(next);
                      }}
                      className="mt-2 rounded border border-amber-400 px-2 py-1 text-xs font-medium hover:bg-amber-100 dark:hover:bg-amber-900/40"
                    >
                      Use the other reading
                    </button>
                  )}
                </div>
              )}

              <div className="grid gap-6 xl:grid-cols-2">
                {chart.charts.map((v) => (
                  <div
                    key={v.code}
                    className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900"
                  >
                    <h2 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
                      {v.code} · {v.name.ta}{" "}
                      <span className="font-normal text-slate-500">
                        {v.name.en} kattam
                      </span>
                    </h2>
                    <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
                      {v.significance}
                    </p>
                    {meta && (
                      <SouthIndianChart
                        chart={v}
                        rasis={meta.rasis}
                        grahas={meta.grahas}
                        lang={lang}
                        highlightGraha={hover}
                      />
                    )}
                  </div>
                ))}
              </div>

              <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
                <GrahaTable chart={chart} lang={lang} onHover={setHover} />
              </div>

              <p className="text-center text-xs text-slate-400">
                engine {chart.engine_version} · place data ©{" "}
                <a
                  href="https://www.geonames.org/"
                  className="underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  GeoNames
                </a>{" "}
                CC BY 4.0
              </p>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
