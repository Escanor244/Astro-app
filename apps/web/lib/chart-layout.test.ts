import { describe, expect, it } from "vitest";
import {
  BOARD,
  CELL,
  CELL_SIZE,
  GRAHA_FONT,
  GRAHA_FONT_CROWDED,
  ascLabelY,
  cellOrigin,
  houseOf,
  occupantPositions,
} from "./chart-layout";

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

describe("occupant placement", () => {
  // The defect this guards: a fixed two-per-row layout fitted exactly eight
  // grahas, and the ninth was drawn 14 units below the cell — usually painted
  // over by the neighbouring cell's opaque fill, so the chart silently lost a
  // graha. D2 Hora squeezes the whole zodiac into two rasis, so a full house of
  // nine happens in roughly one D2 chart in two hundred.
  //
  // Nothing asserted containment before, which is exactly why it shipped.

  const APPROX_DESCENDER = 0.3; // of font size, below the baseline
  const APPROX_ASCENDER = 0.75; // of font size, above the baseline

  for (const count of [1, 2, 3, 4, 5, 6, 7, 8, 9]) {
    for (const isLagna of [false, true]) {
      it(`keeps ${count} grahas inside the cell${isLagna ? " (lagna)" : ""}`, () => {
        const placed = occupantPositions(count, isLagna);
        expect(placed).toHaveLength(count);

        for (const [i, p] of placed.entries()) {
          const top = p.y - p.fontSize * APPROX_ASCENDER;
          const bottom = p.y + p.fontSize * APPROX_DESCENDER;

          expect(top, `graha ${i} top`).toBeGreaterThan(0);
          expect(bottom, `graha ${i} bottom`).toBeLessThan(CELL_SIZE);
          expect(p.x, `graha ${i} left`).toBeGreaterThanOrEqual(0);
          // Two characters wide, generously estimated.
          expect(p.x + p.fontSize * 1.6, `graha ${i} right`).toBeLessThan(CELL_SIZE);
        }
      });
    }
  }

  it("never overlaps the ASC label in the lagna's own cell", () => {
    // Seven or more grahas in the rising sign used to overprint the ASC label.
    for (let count = 1; count <= 9; count++) {
      const placed = occupantPositions(count, true);
      const lowest = Math.max(...placed.map((p) => p.y + p.fontSize * 0.3));
      expect(lowest, `${count} grahas`).toBeLessThan(
        ascLabelY() - 12 * 0.75,
      );
    }
  });

  it("does not overlap rows with each other", () => {
    for (let count = 1; count <= 9; count++) {
      const rows = [...new Set(occupantPositions(count).map((p) => p.y))].sort(
        (a, b) => a - b,
      );
      for (let i = 1; i < rows.length; i++) {
        // Consecutive baselines must clear a full glyph height.
        expect(rows[i] - rows[i - 1], `${count} grahas`).toBeGreaterThanOrEqual(10);
      }
    }
  });

  it("gives every graha a distinct position", () => {
    for (let count = 1; count <= 9; count++) {
      const seen = new Set(occupantPositions(count).map((p) => `${p.x},${p.y}`));
      expect(seen.size, `${count} grahas`).toBe(count);
    }
  });

  it("shrinks the type only when a cell is crowded", () => {
    // Referenced from the constants, not hardcoded: type size is a readability
    // choice that should be tunable without a test edit. What must hold is that
    // the *default* is used until a cell genuinely fills up — and the
    // containment tests above already prove the crowded size still fits.
    expect(occupantPositions(4)[0].fontSize).toBe(GRAHA_FONT);
    expect(occupantPositions(6)[0].fontSize).toBe(GRAHA_FONT);
    expect(occupantPositions(9)[0].fontSize).toBe(GRAHA_FONT_CROWDED);
    expect(GRAHA_FONT_CROWDED).toBeLessThan(GRAHA_FONT);
  });

  it("returns nothing for an empty cell", () => {
    expect(occupantPositions(0)).toEqual([]);
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

  it("stays consistent with the CLI's grid", () => {
    // scripts/chart.py draws the same chart in text with SOUTH_INDIAN_GRID,
    // laid out row-major. If the two ever disagree, one of them is drawing a
    // wrong chart, and the CLI is the one the user validated against an online
    // source — so this pins the UI to it.
    const cliGrid = [
      [11, 0, 1, 2],
      [10, null, null, 3],
      [9, null, null, 4],
      [8, 7, 6, 5],
    ];
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 4; col++) {
        const rasi = cliGrid[row][col];
        if (rasi === null) continue;
        expect(CELL[rasi], `rasi ${rasi}`).toEqual([col, row]);
      }
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
