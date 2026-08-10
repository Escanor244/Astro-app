"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, type Place, searchPlaces } from "@/lib/api";

/**
 * Birth-place autocomplete.
 *
 * Nobody knows the latitude of the village they were born in, so this is the
 * primary way a birth is located. Tamil script works as input — typing மதுரை
 * finds Madurai — because the index folds diacritics on Latin only and leaves
 * Indic combining marks alone.
 *
 * Two details that matter for correctness rather than polish:
 *
 * - Requests are aborted when superseded. Without that, a slow response for
 *   "Mad" can land after a fast one for "Madurai" and silently replace the
 *   right list with a stale one.
 * - The selected place is cleared the moment the text changes, so a chart can
 *   never be cast against a place the user has since typed away from.
 */

const DEBOUNCE_MS = 180;

type Props = {
  value: Place | null;
  onChange: (place: Place | null) => void;
};

export function PlaceSearch({ value, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState(0);

  const boxRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!query.trim() || value?.display_name === query) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);
      try {
        const body = await searchPlaces(query.trim(), controller.signal);
        setResults(body.results);
        setActive(0);
        setOpen(true);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof ApiError ? err.message : "Search failed.");
        setResults([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [query, value]);

  // Close on an outside click, so the list does not hang over the form.
  useEffect(() => {
    function onDown(event: MouseEvent) {
      if (!boxRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  function select(place: Place) {
    onChange(place);
    setQuery(place.display_name);
    setOpen(false);
    setResults([]);
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (!open || results.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) => (i + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => (i - 1 + results.length) % results.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      select(results[active]);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div ref={boxRef} className="relative">
      <label
        htmlFor="place"
        className="block text-sm font-medium text-slate-700 dark:text-slate-300"
      >
        Birth place <span className="text-slate-400">/ பிறந்த ஊர்</span>
      </label>
      <input
        id="place"
        type="text"
        value={query}
        autoComplete="off"
        placeholder="Madurai, மதுரை, Singapore…"
        onChange={(e) => {
          setQuery(e.target.value);
          // A stale selection must never outlive the text it came from.
          if (value) onChange(null);
        }}
        onFocus={() => results.length > 0 && setOpen(true)}
        onKeyDown={onKeyDown}
        className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        aria-expanded={open}
        aria-autocomplete="list"
        role="combobox"
        aria-controls="place-results"
      />

      {loading && (
        <span className="absolute right-3 top-9 text-xs text-slate-400">…</span>
      )}

      {value && (
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {value.latitude.toFixed(4)}, {value.longitude.toFixed(4)} · {value.timezone}
        </p>
      )}

      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}

      {open && results.length > 0 && (
        <ul
          id="place-results"
          role="listbox"
          className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800"
        >
          {results.map((place, i) => (
            <li
              key={place.geonameid}
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                select(place);
              }}
              className={`cursor-pointer px-3 py-2 text-sm ${
                i === active
                  ? "bg-amber-50 dark:bg-slate-700"
                  : "hover:bg-slate-50 dark:hover:bg-slate-700/50"
              }`}
            >
              <div className="text-slate-900 dark:text-slate-100">
                {place.display_name}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {place.latitude.toFixed(3)}, {place.longitude.toFixed(3)} ·{" "}
                {place.timezone}
                {place.population > 0 &&
                  ` · ${place.population.toLocaleString()} people`}
              </div>
            </li>
          ))}
        </ul>
      )}

      {open && !loading && query.trim() && results.length === 0 && !error && (
        <div className="absolute z-20 mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 shadow-lg dark:border-slate-700 dark:bg-slate-800">
          No place matches “{query}”. Try fewer letters, or a nearby town.
        </div>
      )}
    </div>
  );
}
