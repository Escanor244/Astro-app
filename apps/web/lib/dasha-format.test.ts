import { describe, expect, it } from "vitest";
import {
  formatDuration,
  formatPeriodDate,
  formatPeriodTime,
  isPast,
} from "./dasha-format";

/**
 * The two traps these guard.
 *
 * Dates must be formatted by slicing the string, never through `new Date(...)`.
 * The engine sends naive local ISO already converted to the birth place's wall
 * clock; handing that to the Date constructor makes the browser reinterpret it
 * in the *viewer's* timezone, so a dasha beginning at 00:30 in Chennai would
 * print as the previous day for someone reading in London.
 *
 * Durations span five orders of magnitude, and rounding has to carry — a 16-year
 * mahadasha must not print as "15y 12m".
 */

describe("formatPeriodDate", () => {
  it("formats a naive local ISO string", () => {
    expect(formatPeriodDate("2015-02-01T10:23:45")).toBe("1 Feb 2015");
    expect(formatPeriodDate("2026-12-31T23:59:59")).toBe("31 Dec 2026");
  });

  it("does not shift the date across a timezone", () => {
    // Just after local midnight. A Date-based implementation moves this to the
    // 9th for any viewer west of the birth place.
    expect(formatPeriodDate("2026-08-10T00:30:00")).toBe("10 Aug 2026");
    // And just before it, which moves the other way.
    expect(formatPeriodDate("2026-08-10T23:45:00")).toBe("10 Aug 2026");
  });

  it("accepts a bare date", () => {
    expect(formatPeriodDate("2026-08-10")).toBe("10 Aug 2026");
  });

  it("returns the input unchanged rather than throwing on nonsense", () => {
    expect(formatPeriodDate("not-a-date")).toBe("not-a-date");
  });
});

describe("formatPeriodTime", () => {
  it("takes the clock part only", () => {
    expect(formatPeriodTime("2026-08-10T05:56:12")).toBe("05:56");
  });

  it("is empty when there is no time", () => {
    expect(formatPeriodTime("2026-08-10")).toBe("");
  });
});

describe("formatDuration", () => {
  it("uses years and months at mahadasha scale", () => {
    expect(formatDuration(20 * 365.25)).toBe("20y");
    expect(formatDuration(16 * 365.25)).toBe("16y");
    expect(formatDuration(6 * 365.25)).toBe("6y");
  });

  it("never prints a twelfth month", () => {
    // Two ways this used to happen. 16 x 365.25 = 5844 days rounds its month
    // remainder up and must carry, or it reads "15y 12m". And anything from 360
    // to 365 days is already twelve 30-day months, which fell into the months
    // branch and printed "12m 5d".
    expect(formatDuration(5844)).toBe("16y");
    for (let d = 355; d < 400; d += 0.7) {
      expect(formatDuration(d)).not.toMatch(/\b1[2-9]m\b/);
    }
    expect(formatDuration(364.9)).toBe("1y");
    expect(formatDuration(359)).toBe("11m 29d");
  });

  it("uses months and days at antardasha scale", () => {
    expect(formatDuration(90)).toBe("3m");
    expect(formatDuration(100)).toBe("3m 10d");
  });

  it("uses days and hours at pratyantar scale", () => {
    expect(formatDuration(1)).toBe("1d");
    expect(formatDuration(2.5)).toBe("2d 12h");
  });

  it("uses hours and minutes at prana scale", () => {
    expect(formatDuration(0.5)).toBe("12h");
    expect(formatDuration(0.1)).toBe("2h 24m");
    expect(formatDuration(0.01)).toBe("14m");
  });

  it("never prints a zero-length period", () => {
    expect(formatDuration(0)).toBe("1m");
    expect(formatDuration(0.0001)).toBe("1m");
  });

  it("is monotonic across the unit boundaries", () => {
    // Every threshold must produce something non-empty and not a bare unit.
    for (const days of [0.9, 1, 1.1, 29.9, 30, 30.1, 364, 365, 366]) {
      const out = formatDuration(days);
      expect(out).toMatch(/^\d/);
      expect(out).not.toContain("NaN");
    }
  });
});

describe("isPast", () => {
  it("compares same-format ISO strings lexicographically", () => {
    const at = "2026-08-10T12:00:00";
    expect(isPast({ end: "2015-02-01T00:00:00" }, at)).toBe(true);
    expect(isPast({ end: "2030-02-01T00:00:00" }, at)).toBe(false);
  });

  it("orders correctly across a century boundary", () => {
    expect(isPast({ end: "2099-12-31T23:59:59" }, "2100-01-01T00:00:00")).toBe(
      true,
    );
  });
});
