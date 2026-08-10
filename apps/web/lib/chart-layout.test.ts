import { describe, expect, it } from "vitest";
import { BOARD, CELL, CELL_SIZE, cellOrigin, houseOf } from "./chart-layout";

/**
 * A South Indian chart with a rasi in the wrong cell still looks like a chart.
 * Nothing about it is visibly broken, and only someone who reads charts would
 * catch it — which is exactly the class of defect this project keeps finding.
 */

describe("cell layout", () => {
  it("places all twelve rasis, each in its own cell", () => {
    expect(CELL).toHaveLength(12);
    expect(new Set(CELL.map(([c, r]) => `${c},${r}`)).size).toBe(12);
  });

  it("leaves the centre 2x2 hollow", () => {
    const centre = new Set(["1,1", "2,1", "1,2", "2,2"]);
    for (const [col, row] of CELL) {
      expect(centre.has(`${col},${row}`)).toBe(false);
    }
  });

  it("keeps every cell inside the 4x4 board", () => {
    for (const [col, row] of CELL) {
      expect(col).toBeGreaterThanOrEqual(0);
      expect(col).toBeLessThan(4);
      expect(row).toBeGreaterThanOrEqual(0);
      expect(row).toBeLessThan(4);
    }
  });

  it("puts Mesham second in the top row, where it always is", () => {
    expect(CELL[0]).toEqual([1, 0]);
  });

  it("runs clockwise: consecutive rasis are always adjacent", () => {
    // The defining property of the layout. An off-by-one anywhere in the ring
    // breaks adjacency somewhere, so this catches a rotation or a swap that
    // the uniqueness check above would not.
    for (let rasi = 0; rasi < 12; rasi++) {
      const [c1, r1] = CELL[rasi];
      const [c2, r2] = CELL[(rasi + 1) % 12];
      const step = Math.abs(c1 - c2) + Math.abs(r1 - r2);
      expect(step, `rasi ${rasi} -> ${(rasi + 1) % 12}`).toBe(1);
    }
  });

  it("places the four corners on the sign each quadrant starts", () => {
    // Meenam, Mithunam, Kanni and Dhanusu are the dual signs, and they sit at
    // the corners of a South Indian chart.
    expect(cellOrigin(11)).toEqual({ x: 0, y: 0 }); // Meenam, top-left
    expect(cellOrigin(2)).toEqual({ x: 300, y: 0 }); // Mithunam, top-right
    expect(cellOrigin(5)).toEqual({ x: 300, y: 300 }); // Kanni, bottom-right
    expect(cellOrigin(8)).toEqual({ x: 0, y: 300 }); // Dhanusu, bottom-left
  });

  it("derives pixel origins from the grid", () => {
    expect(BOARD).toBe(CELL_SIZE * 4);
    expect(cellOrigin(0)).toEqual({ x: CELL_SIZE, y: 0 });
  });
});

describe("house numbering", () => {
  it("makes the lagna's own rasi house 1", () => {
    for (let lagna = 0; lagna < 12; lagna++) {
      expect(houseOf(lagna, lagna)).toBe(1);
    }
  });

  it("counts forward through the rasis", () => {
    // Taurus lagna: Taurus is 1, Gemini 2, ... Aries 12.
    expect(houseOf(1, 1)).toBe(1);
    expect(houseOf(2, 1)).toBe(2);
    expect(houseOf(0, 1)).toBe(12);
  });

  it("wraps rather than going negative", () => {
    // Aries rasi with a Pisces lagna is house 2, not house -10.
    expect(houseOf(0, 11)).toBe(2);
    expect(houseOf(11, 0)).toBe(12);
  });

  it("always yields 1..12, for every lagna and rasi", () => {
    for (let lagna = 0; lagna < 12; lagna++) {
      const seen = new Set<number>();
      for (let rasi = 0; rasi < 12; rasi++) {
        const house = houseOf(rasi, lagna);
        expect(house).toBeGreaterThanOrEqual(1);
        expect(house).toBeLessThanOrEqual(12);
        seen.add(house);
      }
      // All twelve houses appear exactly once per chart.
      expect(seen.size).toBe(12);
    }
  });

  it("matches the chart the user verified", () => {
    // Taurus lagna, 15 May 1990 Chennai: Sun in Taurus is house 1, Moon in
    // Sagittarius house 8, Saturn in Capricorn house 9, Ketu in Cancer house 3.
    const lagna = 1; // Taurus
    expect(houseOf(1, lagna)).toBe(1); // Sun, Taurus
    expect(houseOf(8, lagna)).toBe(8); // Moon, Sagittarius
    expect(houseOf(9, lagna)).toBe(9); // Saturn, Capricorn
    expect(houseOf(3, lagna)).toBe(3); // Ketu, Cancer
    expect(houseOf(0, lagna)).toBe(12); // Mercury, Aries
  });
});
