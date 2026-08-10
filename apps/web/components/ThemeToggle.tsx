"use client";

import { useEffect, useState } from "react";

/**
 * Light / dark / system theme switch.
 *
 * Three states rather than two, because "follow the OS" is a real preference
 * and not the same as either fixed choice. The chosen mode is stored in
 * localStorage under `theme`, and a small script in `layout.tsx` applies it
 * before first paint so the page never flashes the wrong theme.
 */

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "theme";

/** Apply a theme to <html>. Shared with the pre-paint script in layout.tsx. */
export function applyTheme(theme: Theme) {
  const dark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
}

const OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: "light", label: "Light", icon: "☀" },
  { value: "dark", label: "Dark", icon: "☾" },
  { value: "system", label: "System", icon: "◐" },
];

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (stored) setTheme(stored);
  }, []);

  // Track the OS while on "system", so the page follows a change made outside
  // the app rather than going stale until the next reload.
  useEffect(() => {
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme]);

  function choose(next: Theme) {
    setTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  return (
    <div
      role="group"
      aria-label="Colour theme"
      className="flex overflow-hidden rounded-md border border-slate-300 dark:border-slate-600"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => choose(option.value)}
          aria-pressed={theme === option.value}
          title={`${option.label} theme`}
          className={`px-2.5 py-1 text-sm transition ${
            theme === option.value
              ? "bg-amber-600 text-white"
              : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          }`}
        >
          <span aria-hidden>{option.icon}</span>
          <span className="sr-only">{option.label}</span>
        </button>
      ))}
    </div>
  );
}
