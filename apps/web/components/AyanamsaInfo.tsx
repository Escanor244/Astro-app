"use client";

import { useEffect, useRef, useState } from "react";

/**
 * The ⓘ beside the ayanamsa selector.
 *
 * Short enough to read while choosing, and it links to the full guide rather
 * than trying to teach the whole topic in a popover. Ayanamsa is the one
 * setting in this form where picking the wrong value produces a chart that
 * looks entirely normal and is wrong throughout, so it earns an explanation
 * at the point of choosing.
 */

const NOTES: { id: string; title: string; body: string; when: string }[] = [
  {
    id: "lahiri",
    title: "Lahiri (Chitrapaksha)",
    body: "India's official standard since 1955. Anchors the zodiac so the star Chitra (Spica) sits at 180°.",
    when: "Use this unless you have a specific reason not to. Every Indian panchangam and almost every Tamil astrology site uses it.",
  },
  {
    id: "true_chitrapaksha",
    title: "True Chitrapaksha",
    body: "The same idea, but it recomputes Spica's real position each time instead of carrying a fixed value forward. About 1′ from Lahiri.",
    when: "For the star-tracking definition, or to reproduce someone else's work that used it.",
  },
  {
    id: "kp",
    title: "KP (Krishnamurti)",
    body: "K. S. Krishnamurti's own value, about 5′49″ below Lahiri. KP splits the zodiac into 249 subs, the smallest under 15′ wide.",
    when: "Required for any KP work. That 5′49″ is more than a third of the smallest sub, so KP on Lahiri gives wrong sub-lords while the chart still looks normal.",
  },
  {
    id: "raman",
    title: "Raman",
    body: "B. V. Raman's value, about 1°26′ below Lahiri — a large difference that visibly changes charts.",
    when: "To match the worked examples in Raman's books, or a lineage that teaches his value.",
  },
];

export function AyanamsaInfo() {
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDown(event: MouseEvent) {
      if (!boxRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onEsc(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  return (
    <span ref={boxRef} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label="What is ayanamsa, and which should I choose?"
        className="ml-1.5 inline-flex h-5 w-5 items-center justify-center rounded-full border border-slate-400 text-xs font-semibold text-slate-500 transition hover:border-amber-600 hover:text-amber-700 dark:border-slate-500 dark:text-slate-400 dark:hover:border-amber-500 dark:hover:text-amber-400"
      >
        i
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="About ayanamsa"
          className="absolute left-0 top-7 z-30 w-[22rem] max-w-[calc(100vw-3rem)] rounded-lg border border-slate-200 bg-white p-4 text-sm shadow-xl dark:border-slate-700 dark:bg-slate-800"
        >
          <p className="text-slate-700 dark:text-slate-200">
            Vedic astrology measures from the <strong>stars</strong>; Western
            measures from the <strong>March equinox</strong>. Those drifted apart
            over the centuries, and <strong>ayanamsa</strong> is the gap —
            currently about <strong>24°13′</strong>.
          </p>
          <p className="mt-2 text-slate-600 dark:text-slate-300">
            It shifts every graha by the same amount, so aspects and yogas never
            change. What can change is the <strong>rasi, nakshatra or pada</strong>{" "}
            a graha falls in, when it already sits near a boundary.
          </p>

          <dl className="mt-3 space-y-2.5 border-t border-slate-200 pt-3 dark:border-slate-700">
            {NOTES.map((n) => (
              <div key={n.id}>
                <dt className="font-semibold text-slate-800 dark:text-slate-100">
                  {n.title}
                </dt>
                <dd className="text-slate-600 dark:text-slate-300">
                  {n.body}{" "}
                  <span className="text-slate-500 dark:text-slate-400">
                    {n.when}
                  </span>
                </dd>
              </div>
            ))}
          </dl>

          <p className="mt-3 rounded bg-amber-50 px-2 py-1.5 text-xs text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
            Whichever you pick, <strong>be consistent</strong>. Never compare two
            charts computed with different ayanamsas — and if a chart disagrees
            with another program, check this setting before suspecting a bug.
          </p>

          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Full guide: <code>docs/ayanamsa.md</code>
          </p>
        </div>
      )}
    </span>
  );
}
