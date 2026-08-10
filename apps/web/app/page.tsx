"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  type Chart,
  type ChartRequest,
  type Meta,
  type RecordInput,
  type SavedRecord,
  computeChart,
  fetchMeta,
  saveRecord,
  updateRecord,
} from "@/lib/api";
import { downloadChart } from "@/lib/chart-export";
import { ChartLibrary } from "@/components/ChartLibrary";
import { BirthForm, type FormState } from "@/components/BirthForm";
import { DashaTree } from "@/components/DashaTree";
import { BhavaPanel } from "@/components/BhavaPanel";
import { GrahaTable } from "@/components/GrahaTable";
import { PanchangamPanel } from "@/components/PanchangamPanel";
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

  // The request that produced the chart on screen. The dasha and panchangam
  // panels re-issue it against their own endpoints, so they always describe the
  // chart being displayed rather than whatever the form has since been edited to.
  const [lastRequest, setLastRequest] = useState<ChartRequest | null>(null);

  // Library state. `savedId` tracks which record the form currently represents,
  // so Save updates that record rather than silently creating duplicates every
  // time the user tweaks and re-saves.
  const [savedId, setSavedId] = useState<number | null>(null);
  const [libraryKey, setLibraryKey] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchMeta()
      .then(setMeta)
      .catch((e) => setMetaError(e instanceof ApiError ? e.message : String(e)));
  }, []);

  async function cast(fold = form.fold) {
    if (!form.place) return;
    setBusy(true);
    setError(null);
    const body: ChartRequest = {
      date: form.date,
      time: form.time,
      geonameid: form.place.geonameid,
      ayanamsa: form.ayanamsa,
      vargas: form.vargas,
      fold,
      name: form.name || null,
    };
    try {
      setChart(await computeChart(body));
      setLastRequest(body);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
      setChart(null);
      setLastRequest(null);
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (!form.place || !chart) return;
    setSaving(true);
    setError(null);
    try {
      // The *resolved* place travels with the record, not just the geonameid.
      // The place index is a regenerable build artifact, so re-resolving an id
      // later could silently move a saved chart.
      const body: RecordInput = {
        name: form.name.trim() || form.place.name,
        notes: "",
        birth_date: form.date,
        birth_time: form.time.length === 5 ? `${form.time}:00` : form.time,
        fold: form.fold,
        ayanamsa: form.ayanamsa,
        latitude: form.place.latitude,
        longitude: form.place.longitude,
        timezone_name: form.place.timezone,
        place_name: form.place.display_name,
        geonameid: form.place.geonameid,
        vargas: form.vargas,
      };
      const record = savedId
        ? await updateRecord(savedId, body)
        : await saveRecord(body);
      setSavedId(record.id);
      setLibraryKey((k) => k + 1);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  async function openRecord(record: SavedRecord) {
    // Reconstruct the form from the record, then re-cast. The saved
    // coordinates are used directly rather than the geonameid, which is what
    // makes a saved chart reproducible.
    const place = {
      geonameid: record.geonameid ?? -1,
      name: record.place_name.split(",")[0] ?? record.place_name,
      display_name: record.place_name,
      admin1: "",
      country_code: "",
      country_name: "",
      latitude: record.latitude,
      longitude: record.longitude,
      timezone: record.timezone_name,
      population: 0,
    };
    setForm({
      name: record.name,
      date: record.birth_date,
      time: record.birth_time,
      place,
      ayanamsa: record.ayanamsa,
      vargas: record.vargas,
      fold: record.fold,
    });
    setSavedId(record.id);

    setBusy(true);
    setError(null);
    const body: ChartRequest = {
      date: record.birth_date,
      time: record.birth_time,
      latitude: record.latitude,
      longitude: record.longitude,
      place_name: record.place_name,
      timezone: record.timezone_name,
      fold: record.fold,
      ayanamsa: record.ayanamsa,
      vargas: record.vargas,
      name: record.name,
    };
    try {
      setChart(await computeChart(body));
      setLastRequest(body);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not open that chart.");
      setChart(null);
      setLastRequest(null);
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
        <div className="no-print flex flex-wrap items-center gap-4">
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
        <div className="min-w-0 space-y-6">
          <section className="no-print rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <BirthForm
              meta={meta}
              value={form}
              onChange={(next) => {
                // Editing the form detaches it from the record it came from,
                // so Save creates a new entry rather than overwriting the one
                // the user opened.
                if (savedId !== null) setSavedId(null);
                setForm(next);
              }}
              onSubmit={() => cast()}
              busy={busy}
              lang={lang}
            />
          </section>

          <ChartLibrary
            onOpen={openRecord}
            refreshKey={libraryKey}
            currentId={savedId}
          />
        </div>

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
              <div className="no-print flex flex-wrap justify-end gap-2">
                <button
                  type="button"
                  onClick={save}
                  disabled={saving || !form.place}
                  className="mr-auto rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-white"
                >
                  {saved
                    ? "Saved ✓"
                    : saving
                      ? "Saving…"
                      : savedId
                        ? "Update saved chart"
                        : "Save to library"}
                </button>
                <button
                  type="button"
                  onClick={() => window.print()}
                  title="One A4 page per chart"
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-amber-600 hover:text-amber-700 dark:border-slate-600 dark:text-slate-200 dark:hover:border-amber-500 dark:hover:text-amber-400"
                >
                  Print / Save as PDF
                </button>
                {meta && (
                  <button
                    type="button"
                    onClick={() =>
                      chart.charts.forEach((v, i) =>
                        // Stagger slightly: browsers drop rapid successive
                        // downloads triggered from one click.
                        setTimeout(
                          () =>
                            downloadChart(chart, v, meta.rasis, meta.grahas, lang, form.name),
                          i * 350,
                        ),
                      )
                    }
                    className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-amber-600 hover:text-amber-700 dark:border-slate-600 dark:text-slate-200 dark:hover:border-amber-500 dark:hover:text-amber-400"
                  >
                    ↓ Download all as A4
                  </button>
                )}
              </div>

              {/* The offset actually applied, and why. A historical offset
                  moves the lagna about a rasi, so it is shown, not buried. */}
              <div className="print-chart rounded-lg border border-slate-200 bg-white p-4 text-sm shadow-sm dark:border-slate-700 dark:bg-slate-900">
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
                    className="print-chart rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900"
                  >
                    <div className="mb-1 flex items-start justify-between gap-3">
                      <h2 className="font-semibold text-slate-900 dark:text-slate-100">
                        {v.code} · {v.name.ta}{" "}
                        <span className="font-normal text-slate-500">
                          {v.name.en} kattam
                        </span>
                      </h2>
                      {meta && (
                        <button
                          type="button"
                          onClick={() =>
                            downloadChart(
                              chart,
                              v,
                              meta.rasis,
                              meta.grahas,
                              lang,
                              form.name,
                            )
                          }
                          title={`Download ${v.code} as an A4 sheet`}
                          className="no-print shrink-0 rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 transition hover:border-amber-600 hover:text-amber-700 dark:border-slate-600 dark:text-slate-300 dark:hover:border-amber-500 dark:hover:text-amber-400"
                        >
                          ↓ A4
                        </button>
                      )}
                    </div>
                    <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
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

              {/* Houses, and செவ்வாய் தோஷம் as inputs rather than a verdict. */}
              <div className="print-chart rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
                <BhavaPanel chart={chart} lang={lang} />
              </div>

              {/* Panchangam for the birth moment. The vaara here is the
                  sunrise-to-sunrise weekday, which differs from the calendar
                  one for any birth between midnight and sunrise. */}
              <div className="print-chart rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
                <h2 className="mb-3 font-semibold text-slate-900 dark:text-slate-100">
                  பஞ்சாங்கம்{" "}
                  <span className="font-normal text-slate-500">
                    Panchangam at birth
                  </span>
                </h2>
                <PanchangamPanel request={lastRequest} lang={lang} />
              </div>

              {/* Dasha. A chart says what is possible; the dasha says when, so
                  this is where a consultation actually spends its time. */}
              <div className="print-chart rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
                <h2 className="mb-3 font-semibold text-slate-900 dark:text-slate-100">
                  விம்சோத்தரி தசை{" "}
                  <span className="font-normal text-slate-500">
                    Vimshottari dasha
                  </span>
                </h2>
                <DashaTree request={lastRequest} lang={lang} />
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
