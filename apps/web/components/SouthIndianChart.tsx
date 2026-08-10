"use client";

import type { Term, VargaChart } from "@/lib/api";
import {
  BOARD,
  CELL,
  CELL_SIZE,
  ascLabelY,
  houseOf,
  occupantPositions,
} from "@/lib/chart-layout";

/**
 * The South Indian square chart (கட்டம்).
 *
 * The defining property, and the reason this is drawn rather than a generic
 * grid: **the rasis never move.** Mesham is always the second cell of the top
 * row, in every chart ever drawn. It is the *houses* that rotate — whichever
 * cell holds the lagna becomes house 1, counted clockwise from there.
 *
 * That is the opposite of the North Indian diamond, where the houses are fixed
 * and the signs move. Same information, opposite convention, and the source of
 * endless confusion when reading books written for the other tradition. This
 * app is Tamil-native, so the square chart is the primary view and not a
 * display toggle.
 *
 * Row-major cell positions for rasi 0..11, running clockwise from Mesham:
 *
 *     Meenam  | Mesham  | Rishabam | Mithunam
 *     Kumbam  |                    | Kadagam
 *     Magaram |                    | Simmam
 *     Dhanusu | Viruchigam | Thulam| Kanni
 */

export type Language = "en" | "ta";

type Props = {
  chart: VargaChart;
  rasis: Term[];
  grahas: Term[];
  lang: Language;
  /** Highlighted when the user hovers a graha in the table. */
  highlightGraha?: number | null;
};

/**
 * Short label for a graha.
 *
 * Taken from the engine lexicon, never truncated here. Tamil letters are a base
 * character plus combining marks, so slicing to a fixed length can drop the mark
 * and produce a different word: சந்திரன் (Moon) became சந and சனி (Saturn)
 * became சன — neither is a graha, and they differ only in ந vs ன.
 */
function grahaLabel(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta_short : term.en_short;
}

export function SouthIndianChart({
  chart,
  rasis,
  grahas,
  lang,
  highlightGraha = null,
}: Props) {
  // Group grahas by the rasi they occupy in *this* chart. A varga is the same
  // grid with different placements, which is why this component takes a
  // VargaChart rather than a birth chart.
  const occupants = new Map<number, number[]>();
  for (const [key, rasi] of Object.entries(chart.graha_rasis)) {
    const gi = Number(key);
    occupants.set(rasi, [...(occupants.get(rasi) ?? []), gi]);
  }

  return (
    <svg
      viewBox={`-1 -1 ${BOARD + 2} ${BOARD + 2}`}
      className="w-full max-w-xl select-none"
      role="img"
      aria-label={`${chart.name.en} chart`}
    >
      <title>{`${chart.code} ${chart.name.en} / ${chart.name.ta}`}</title>

      {/* The hollow centre. Purely conventional, and it carries the label. */}
      <rect
        x={CELL_SIZE}
        y={CELL_SIZE}
        width={CELL_SIZE * 2}
        height={CELL_SIZE * 2}
        className="fill-amber-50/60 dark:fill-slate-800/40"
      />
      <text
        x={BOARD / 2}
        y={BOARD / 2 - 8}
        textAnchor="middle"
        className="fill-slate-500 text-[15px] font-semibold dark:fill-slate-400"
      >
        {chart.code}
      </text>
      <text
        x={BOARD / 2}
        y={BOARD / 2 + 14}
        textAnchor="middle"
        className="fill-slate-400 text-[12px] dark:fill-slate-500"
      >
        {lang === "ta" ? chart.name.ta : chart.name.en}
      </text>

      {CELL.map(([col, row], rasi) => {
        const x = col * CELL_SIZE;
        const y = row * CELL_SIZE;
        const here = occupants.get(rasi) ?? [];
        const isLagna = rasi === chart.lagna_rasi;
        // Houses rotate with the lagna; the rasi cell itself never does.
        const house = houseOf(rasi, chart.lagna_rasi);

        return (
          <g key={rasi}>
            <rect
              x={x}
              y={y}
              width={CELL_SIZE}
              height={CELL_SIZE}
              className={
                isLagna
                  ? "fill-amber-100 stroke-slate-400 dark:fill-amber-950/40 dark:stroke-slate-600"
                  : "fill-white stroke-slate-300 dark:fill-slate-900 dark:stroke-slate-700"
              }
              strokeWidth={1}
            />

            {/* Rasi name — fixed to this cell forever. */}
            <text
              x={x + 5}
              y={y + 15}
              className="fill-slate-600 text-[11px] dark:fill-slate-300"
            >
              {lang === "ta" ? rasis[rasi]?.ta : rasis[rasi]?.en}
            </text>

            {/* House number — rotates with the lagna. */}
            <text
              x={x + CELL_SIZE - 5}
              y={y + 15}
              textAnchor="end"
              className="fill-slate-500 text-[11px] font-semibold dark:fill-slate-400"
            >
              {house}
            </text>

            {isLagna && (
              <text
                x={x + 5}
                y={y + ascLabelY()}
                className="fill-amber-700 text-[10px] font-bold tracking-wide dark:fill-amber-400"
              >
                {lang === "ta" ? "லக்னம்" : "ASC"}
              </text>
            )}

            {/* Grahas. The layout is count-aware so that a full house of nine
                — which D2 Hora produces regularly, since it maps the whole
                zodiac into two rasis — stays inside its own cell. */}
            {occupantPositions(here.length, isLagna).map((slot, i) => {
              const gi = here[i];
              const isRetro = chart.retrogrades.includes(gi) && gi !== 7 && gi !== 8;
              const isHot = highlightGraha === gi;
              return (
                <text
                  key={gi}
                  x={x + slot.x}
                  y={y + slot.y}
                  fontSize={slot.fontSize}
                  className={
                    isHot
                      ? "fill-amber-600 font-bold dark:fill-amber-400"
                      : "fill-slate-800 font-medium dark:fill-slate-100"
                  }
                >
                  {grahaLabel(grahas[gi], lang)}
                  {isRetro && (
                    <tspan fontSize={slot.fontSize * 0.7} dy={-4}>
                      ℞
                    </tspan>
                  )}
                </text>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}
