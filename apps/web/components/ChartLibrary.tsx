"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  type SavedRecord,
  deleteRecord,
  listRecords,
} from "@/lib/api";

/**
 * The saved chart library.
 *
 * A record stores the birth *inputs* and the resolved place, never the computed
 * chart. Opening one re-casts it with the current engine, so a correctness fix
 * reaches every saved chart automatically instead of leaving a shelf of stale
 * results behind.
 */

type Props = {
  onOpen: (record: SavedRecord) => void;
  /** Bumped by the parent after a save, to refetch the list. */
  refreshKey: number;
  currentId: number | null;
};

export function ChartLibrary({ onOpen, refreshKey, currentId }: Props) {
  const [records, setRecords] = useState<SavedRecord[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const body = await listRecords(query);
        if (!cancelled) setRecords(body.records);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load saved charts.");
        }
      }
    }, query ? 180 : 0);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, refreshKey]);

  async function remove(id: number) {
    // The row is only dropped from the list once the server confirms. Without
    // the catch, a failed delete threw and left the user stuck in the confirm
    // state with no message and the record still on disk.
    try {
      setError(null);
      await deleteRecord(id);
      setRecords((rs) => rs.filter((r) => r.id !== id));
      setConfirming(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete that chart.");
      setConfirming(null);
    }
  }

  return (
    <section className="no-print rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="font-semibold text-slate-900 dark:text-slate-100">
        Saved charts <span className="font-normal text-slate-400">/ சேமித்தவை</span>
      </h2>

      {records.length > 3 && (
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search name or place…"
          className="mt-3 w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
      )}

      {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}

      {!error && records.length === 0 && (
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          {query
            ? `Nothing matches “${query}”.`
            : "Nothing saved yet. Cast a chart and press Save."}
        </p>
      )}

      <ul className="mt-3 space-y-1.5">
        {records.map((r) => (
          <li key={r.id}>
            <div
              className={`flex items-center gap-2 rounded-md border px-3 py-2 transition ${
                r.id === currentId
                  ? "border-amber-400 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/30"
                  : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:border-slate-600 dark:hover:bg-slate-800/60"
              }`}
            >
              <button
                type="button"
                onClick={() => onOpen(r)}
                className="min-w-0 flex-1 text-left"
              >
                <div className="truncate font-medium text-slate-900 dark:text-slate-100">
                  {r.name}
                </div>
                <div className="truncate text-xs text-slate-500 dark:text-slate-400">
                  {r.birth_date} · {r.birth_time.slice(0, 5)} ·{" "}
                  {r.place_name || `${r.latitude.toFixed(2)}, ${r.longitude.toFixed(2)}`}
                </div>
                {r.notes && (
                  <div className="truncate text-xs italic text-slate-400">
                    {r.notes}
                  </div>
                )}
              </button>

              {confirming === r.id ? (
                <span className="flex shrink-0 gap-1">
                  <button
                    type="button"
                    onClick={() => remove(r.id)}
                    className="rounded bg-rose-600 px-2 py-1 text-xs font-medium text-white"
                  >
                    Delete
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirming(null)}
                    className="rounded border border-slate-300 px-2 py-1 text-xs dark:border-slate-600"
                  >
                    Keep
                  </button>
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirming(r.id)}
                  aria-label={`Delete ${r.name}`}
                  title="Delete"
                  className="shrink-0 rounded px-2 py-1 text-sm text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                >
                  ×
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
