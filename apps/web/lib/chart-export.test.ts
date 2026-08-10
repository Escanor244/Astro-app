import { describe, expect, it } from "vitest";
import { buildA4Svg } from "./chart-export";
import type { Chart, Term, VargaChart } from "./api";

/**
 * The exported sheet is what a user prints and hands to someone, or keeps in a
 * folder for years. It is also the one artefact that leaves the app entirely,
 * so nothing downstream can correct it.
 */

const term = (en: string, ta: string, enShort = en.slice(0, 2), taShort = ta.slice(0, 1)): Term => ({
  en,
  ta,
  ta_latin: en,
  en_short: enShort,
  ta_short: taShort,
});

const RASIS: Term[] = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
].map((en, i) => term(en, ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி",
  "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"][i]));

const GRAHAS: Term[] = [
  ["Sun", "சூரியன்", "Su", "சூ"], ["Moon", "சந்திரன்", "Mo", "சந்"],
  ["Mars", "செவ்வாய்", "Ma", "செ"], ["Mercury", "புதன்", "Me", "பு"],
  ["Jupiter", "குரு", "Ju", "கு"], ["Venus", "சுக்கிரன்", "Ve", "சு"],
  ["Saturn", "சனி", "Sa", "சனி"], ["Rahu", "ராகு", "Ra", "ரா"],
  ["Ketu", "கேது", "Ke", "கே"],
].map(([en, ta, es, ts]) => term(en, ta, es, ts));

function zodiac(rasi: number) {
  return {
    longitude: rasi * 30 + 11.15,
    formatted: "11°09'21.84\"",
    rasi,
    rasi_name: RASIS[rasi],
    degrees_in_rasi: 11.15,
    nakshatra: 3,
    nakshatra_name: term("Rohini", "ரோகிணி"),
    pada: 1,
    nakshatra_lord: 1,
    nakshatra_lord_name: GRAHAS[1],
  };
}

const VARGA: VargaChart = {
  code: "D9",
  divisions: 9,
  name: term("Navamsa", "நவாம்சம்"),
  significance: "marriage, dharma, and the true strength of every graha",
  lagna_rasi: 0,
  graha_rasis: Object.fromEntries(Array.from({ length: 9 }, (_, i) => [String(i), i % 12])),
  retrogrades: [3, 6, 7, 8],
};

const CHART: Chart = {
  birth: {
    local_datetime: "1990-05-15T06:30:00",
    time_12h: "6:30 AM",
    utc: "1990-05-15T01:00:00",
    place_name: "Chennai, Tamil Nadu, India",
    latitude: 13.0878,
    longitude: 80.2785,
    timezone: "Asia/Kolkata",
    utc_offset: "UTC+05:30",
    offset_note: null,
  },
  ayanamsa: "lahiri",
  ayanamsa_value: 23.72,
  ayanamsa_formatted: "23°43'21.12\"",
  lagna: zodiac(1),
  grahas: GRAHAS.map((name, i) => ({
    graha: i,
    name,
    sanskrit: name.en,
    position: zodiac(i % 12),
    house: (i % 12) + 1,
    retrograde: i === 3 || i === 6 || i >= 7,
    speed_deg_per_day: 1,
  })),
  charts: [VARGA],
  time_warning: null,
  time_warning_kind: null,
  engine_version: "1a.1",
};

const svg = () => buildA4Svg(CHART, VARGA, RASIS, GRAHAS, "en", "Test Person");

describe("A4 sheet", () => {
  it("is a well-formed standalone SVG", () => {
    const out = svg();
    expect(out.startsWith("<?xml")).toBe(true);
    expect(out).toContain('xmlns="http://www.w3.org/2000/svg"');
    expect(out.trimEnd().endsWith("</svg>")).toBe(true);
    // Balanced tags: a truncated file prints as a blank page.
    expect((out.match(/<text/g) ?? []).length).toBe((out.match(/<\/text>/g) ?? []).length);
  });

  it("is sized to real A4, not just a 210:297 box", () => {
    const out = svg();
    // Physical units matter: without them a browser prints it at whatever the
    // default raster size happens to be.
    expect(out).toContain('width="210mm"');
    expect(out).toContain('height="297mm"');
    expect(out).toContain('viewBox="0 0 210 297"');
  });

  it("carries every birth detail needed to reproduce the chart", () => {
    const out = svg();
    for (const needed of [
      "1990-05-15",           // date
      "06:30:00",             // time as entered
      "6:30 AM",              // and unambiguously
      "Chennai",              // place
      "13.0878",              // coordinates, so the sheet is self-sufficient
      "80.2785",
      "Asia/Kolkata",         // zone
      "UTC+05:30",            // and the offset actually applied
      "lahiri",               // without this the degrees cannot be checked
      // The double-quote of the arcsecond mark is escaped; the apostrophe of
      // the arcminute mark is left alone, which is valid in XML text content.
      "23°43'21.12&quot;",
    ]) {
      expect(out, `missing ${needed}`).toContain(needed);
    }
  });

  it("names the chart in both scripts", () => {
    const out = svg();
    expect(out).toContain("D9");
    expect(out).toContain("நவாம்சம்");
    expect(out).toContain("Navamsa");
  });

  it("draws twelve cells and marks the lagna", () => {
    const out = svg();
    // 12 rasi cells + the hollow centre + the page background.
    expect((out.match(/<rect /g) ?? []).length).toBe(14);
    expect(out).toContain("ASC");
  });

  it("includes every graha", () => {
    const out = svg();
    for (const g of GRAHAS) {
      expect(out, `missing ${g.en}`).toContain(g.en);
    }
  });

  it("marks retrograde grahas but never the nodes", () => {
    const out = svg();
    // Rahu and Ketu are always retrograde; marking them is noise.
    const rahuLine = out.split("\n").find((l) => l.includes(">Rahu"));
    expect(rahuLine).toBeDefined();
    expect(rahuLine).not.toContain("℞");
    expect(out).toContain("℞"); // but Mercury and Saturn are marked
  });

  it("escapes text rather than letting it break the document", () => {
    const nasty = buildA4Svg(CHART, VARGA, RASIS, GRAHAS, "en", 'A & B <script>"x"');
    expect(nasty).toContain("&amp;");
    expect(nasty).toContain("&lt;script&gt;");
    expect(nasty).not.toContain("<script>");
  });

  it("falls back to a sensible title when no name is given", () => {
    expect(buildA4Svg(CHART, VARGA, RASIS, GRAHAS, "en")).toContain("Jathagam");
  });

  it("switches every label to Tamil", () => {
    const ta = buildA4Svg(CHART, VARGA, RASIS, GRAHAS, "ta", "தமிழ்");
    expect(ta).toContain("மேஷம்");
    expect(ta).toContain("லக்னம்");
    expect(ta).toContain("சந்"); // Moon, mark intact
  });

  it("carries the warnings, which are the whole reason they exist", () => {
    const warned: Chart = {
      ...CHART,
      birth: { ...CHART.birth, offset_note: "wartime India, 1942-09-01 to 1945-10-15" },
      time_warning: "01:30 occurred twice; confirm which applies.",
      time_warning_kind: "ambiguous",
    };
    const out = buildA4Svg(warned, VARGA, RASIS, GRAHAS, "en", "X");
    expect(out).toContain("wartime India");
    expect(out).toContain("occurred twice");
  });

  /**
   * Every text element as {x, y, size, content}.
   *
   * The original version of these tests read only the x/y *attributes*, which
   * is why three separate overflow defects shipped green: an anchor inside the
   * page says nothing about where the glyphs actually end. Everything below
   * reasons about extent.
   */
  function elements(out: string) {
    return [
      ...out.matchAll(
        /<text x="([-\d.]+)" y="([-\d.]+)" font-size="([\d.]+)"[^>]*text-anchor="(\w+)"[^>]*>([^<]*)</g,
      ),
    ].map((m) => {
      const [x, y, size, anchor, content] = [
        Number(m[1]), Number(m[2]), Number(m[3]), m[4], m[5],
      ];
      // Same advance estimate the exporter uses to pick its own line breaks.
      const width = content.length * size * 0.52;
      // The anchor decides which side of x the glyphs fall on. Ignoring it
      // reports right-aligned text as overflowing when it is nowhere near the
      // edge — the title is anchored at x=196 and extends *left*.
      const left =
        anchor === "end" ? x - width : anchor === "middle" ? x - width / 2 : x;
      return { x, y, size, anchor, content, left, right: left + width };
    });
  }

  it("keeps every anchor inside the page", () => {
    for (const e of elements(svg())) {
      expect(e.x).toBeGreaterThanOrEqual(0);
      expect(e.x).toBeLessThanOrEqual(210);
      expect(e.y).toBeGreaterThanOrEqual(0);
      expect(e.y).toBeLessThanOrEqual(297);
    }
  });

  it("keeps every line of text inside the right margin", () => {
    // Middle-anchored text is centred, so its own x is not its left edge.
    for (const e of elements(svg())) {
      if (e.content.trim() === "") continue;
      expect(e.right, `"${e.content}" runs to ${e.right.toFixed(1)}mm`).toBeLessThanOrEqual(215);
      expect(e.left, `"${e.content}" starts at ${e.left.toFixed(1)}mm`).toBeGreaterThanOrEqual(-5);
    }
  });

  it("never lets the D1 table reach the footer", () => {
    // 9 grahas plus a lagna row is the invariant case, not an edge case. A
    // fixed row pitch put Rahu's row on top of the footer and Ketu's row
    // 1.4mm from the paper edge, inside every desktop printer's dead margin.
    const out = svg();
    const d1 = buildA4Svg(
      { ...CHART, charts: [{ ...VARGA, code: "D1" }] },
      { ...VARGA, code: "D1" },
      RASIS, GRAHAS, "en", "Test",
    );
    for (const sheet of [out, d1]) {
      const rows = elements(sheet);
      const footer = rows.find((e) => e.content.startsWith("Engine"));
      expect(footer).toBeDefined();
      const above = rows.filter((e) => e !== footer && !e.content.startsWith("Place data"));
      const lowest = Math.max(...above.map((e) => e.y));
      expect(lowest, "a row overlaps the footer").toBeLessThan(footer!.y - 3);
    }
  });

  it("wraps a long daylight-saving warning instead of clipping it", () => {
    // The real ambiguous-time warning is ~204 characters. On one line that is
    // 270mm wide on a 210mm page, so the sentence telling the reader what to
    // do was cut off at the paper edge.
    const long =
      "01:30 on 07 Nov 2010 occurred twice in America/New_York: the clocks went " +
      "back. This chart uses UTC-04:00; the other reading is UTC-05:00. They give " +
      "lagnas about 15 degrees apart, so confirm which applies.";
    const out = buildA4Svg(
      { ...CHART, time_warning: long, time_warning_kind: "ambiguous" },
      VARGA, RASIS, GRAHAS, "en", "X",
    );

    for (const e of elements(out)) {
      expect(e.right, `"${e.content}" overflows`).toBeLessThanOrEqual(215);
    }
    // And nothing is lost: the final clause must survive somewhere.
    expect(out).toContain("confirm which applies");
  });

  it("does not let a long place name overprint the ayanamsa", () => {
    // 11,604 places in the shipped index have display names over 44 chars.
    const longPlace =
      "Nani Daman, Daman, Daman And Diu, Dadra and Nagar Haveli and Daman and Diu, India";
    const out = buildA4Svg(
      { ...CHART, birth: { ...CHART.birth, place_name: longPlace } },
      VARGA, RASIS, GRAHAS, "en", "X",
    );

    const rows = elements(out);
    const place = rows.find((e) => e.content.startsWith("Nani Daman"));
    const ayanamsa = rows.find((e) => e.content === "Ayanamsa");
    expect(place && ayanamsa).toBeTruthy();
    // Either on different lines, or ellipsized clear of it.
    if (place!.y === ayanamsa!.y) {
      expect(place!.right).toBeLessThan(ayanamsa!.x);
    }
    for (const e of rows) {
      expect(e.right, `"${e.content}" overflows`).toBeLessThanOrEqual(215);
    }
  });

  it("survives a very long person name", () => {
    const out = buildA4Svg(CHART, VARGA, RASIS, GRAHAS, "en", "A".repeat(120));
    for (const e of elements(out)) {
      expect(e.right).toBeLessThanOrEqual(220);
    }
  });

  it("fits a full house of nine grahas in one cell", () => {
    const crowded: VargaChart = {
      ...VARGA,
      code: "D2",
      graha_rasis: Object.fromEntries(Array.from({ length: 9 }, (_, i) => [String(i), 3])),
    };
    const out = buildA4Svg(CHART, crowded, RASIS, GRAHAS, "en", "X");
    // Cancer is rasi 3 -> CELL [3,1] -> y 74+37.5 .. 74+75
    const cellTop = 74 + 150 / 4;
    const cellBottom = cellTop + 150 / 4;
    // The label may carry a trailing retrograde mark, so match the prefix.
    const inCell = [
      ...out.matchAll(/<text x="([\d.]+)" y="([\d.]+)"[^>]*>(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)℞?</g),
    ];
    expect(inCell.length).toBe(9);
    for (const m of inCell) {
      expect(Number(m[2]), `${m[3]} escaped its cell`).toBeGreaterThan(cellTop);
      expect(Number(m[2]), `${m[3]} escaped its cell`).toBeLessThan(cellBottom);
    }
  });
});
