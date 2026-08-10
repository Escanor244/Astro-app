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
