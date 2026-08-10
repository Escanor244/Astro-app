/**
 * Geometry of the South Indian square chart.
 *
 * Extracted from the component so it can be tested without a DOM. This is the
 * one piece of the UI that can be wrong *silently*: a chart with a rasi in the
 * wrong cell still looks like a perfectly good chart, and only someone who
 * reads charts would notice.
 */

/** Grid position of each rasi index, as [column, row] in a 4x4 layout. */
export const CELL: readonly (readonly [number, number])[] = [
  [1, 0], // 0  Mesham / Aries
  [2, 0], // 1  Rishabam / Taurus
  [3, 0], // 2  Mithunam / Gemini
  [3, 1], // 3  Kadagam / Cancer
  [3, 2], // 4  Simmam / Leo
  [3, 3], // 5  Kanni / Virgo
  [2, 3], // 6  Thulam / Libra
  [1, 3], // 7  Viruchigam / Scorpio
  [0, 3], // 8  Dhanusu / Sagittarius
  [0, 2], // 9  Magaram / Capricorn
  [0, 1], // 10 Kumbam / Aquarius
  [0, 0], // 11 Meenam / Pisces
];

export const GRID_SIZE = 4;
export const CELL_SIZE = 100;
export const BOARD = GRID_SIZE * CELL_SIZE;

/**
 * Whole-sign bhava (1-12) for a rasi, counted from the lagna's rasi.
 *
 * The South Indian chart *is* the whole-sign house system drawn directly: the
 * cell holding the lagna is house 1, and the count runs clockwise from there.
 * The rasi cell itself never moves.
 */
export function houseOf(rasi: number, lagnaRasi: number): number {
  return (((rasi - lagnaRasi) % 12) + 12) % 12 + 1;
}

/** Pixel origin of a rasi's cell. */
export function cellOrigin(rasi: number): { x: number; y: number } {
  const [col, row] = CELL[rasi];
  return { x: col * CELL_SIZE, y: row * CELL_SIZE };
}

/** Top of the occupant band: below the rasi name and house number. */
const BAND_TOP = 28;
/** Bottom margin, and the extra room the lagna cell needs for its ASC label. */
const BAND_BOTTOM = 6;
const ASC_LABEL_HEIGHT = 13;

/** Graha type size: comfortable by default, smaller only when a cell fills up. */
export const GRAHA_FONT = 15;
export const GRAHA_FONT_CROWDED = 11;

export type Occupant = { x: number; y: number; fontSize: number };

/**
 * Where to draw each graha inside a cell, given how many share it.
 *
 * This is count-aware for a reason. A fixed two-per-row layout at a fixed pitch
 * fits exactly eight grahas in a 100-unit cell; the ninth landed 14 units past
 * the cell's own bottom edge, inside the neighbouring rasi. Usually the next
 * cell's opaque fill painted over it and the graha simply vanished from the
 * chart — a South Indian chart silently missing Ketu, with nothing on screen to
 * contradict it. Occasionally it showed through in the wrong sign instead.
 *
 * All nine in one cell is not exotic: D2 Hora maps the entire zodiac into just
 * Cancer and Leo, and Rahu and Ketu always share a hora, so roughly one D2 chart
 * in two hundred is a full house.
 *
 * Everything returned is guaranteed to sit inside the cell, which
 * `chart-layout.test.ts` asserts for every count from 1 to 9.
 */
export function occupantPositions(count: number, isLagna = false): Occupant[] {
  if (count <= 0) return [];

  const perRow = count <= 4 ? 2 : 3;
  const rows = Math.ceil(count / perRow);
  const fontSize = count > 6 ? GRAHA_FONT_CROWDED : GRAHA_FONT;

  const bottom = CELL_SIZE - BAND_BOTTOM - (isLagna ? ASC_LABEL_HEIGHT : 0);
  const band = bottom - BAND_TOP;
  // Never exceed the natural pitch; shrink it only when the rows demand it.
  const pitch = Math.min(fontSize + 4, band / rows);
  const colWidth = (CELL_SIZE - 12) / perRow;

  return Array.from({ length: count }, (_, i) => ({
    x: 6 + (i % perRow) * colWidth,
    // Baselines start one pitch below the band top so ascenders stay clear.
    y: BAND_TOP + pitch * (Math.floor(i / perRow) + 1),
    fontSize,
  }));
}

/** Baseline for the lagna cell's ASC label, below the occupant band. */
export function ascLabelY(): number {
  return CELL_SIZE - BAND_BOTTOM + 2;
}
