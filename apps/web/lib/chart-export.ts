/**
 * A4 chart export.
 *
 * Produces a self-contained SVG sized to a real A4 sheet, so the file both
 * prints correctly and opens in any browser at the right proportions. SVG
 * rather than PNG because a chart is line work and text: it stays sharp at any
 * zoom, prints crisply, and the file is a few kilobytes.
 *
 * Everything is laid out in **millimetres**. The viewBox is 210x297, the actual
 * dimensions of A4, so 1 user unit = 1mm and every size below can be reasoned
 * about physically — a 4mm capital height is about 11pt, comfortably readable
 * on paper. That is the whole reason for the unit choice: "clear wordings" is a
 * measurable property once the units are real.
 *
 * The export is deliberately standalone. Fonts are named rather than embedded
 * (a Tamil font would add megabytes), styles are inline rather than in classes,
 * and nothing references the page it came from.
 */

import type { Chart, Term, VargaChart } from "./api";
import { CELL } from "./chart-layout";

const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN = 14;

/** Chart block: a square, centred, leaving room for header and table. */
const GRID = 138;
const GRID_X = (PAGE_W - GRID) / 2;
const GRID_Y = 68;
const CELL_MM = GRID / 4;

/** Baseline of the footer. Everything above must clear it. */
const FOOTER_Y = PAGE_H - 8;
/** Ink allowance between the last table row and the footer's own ascenders. */
const FOOTER_GAP = 5;

const FONT = "'Noto Sans Tamil', 'Nirmala UI', 'Latha', sans-serif";

export type Language = "en" | "ta";

function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function text(
  x: number,
  y: number,
  content: string,
  opts: {
    size?: number;
    weight?: number;
    anchor?: "start" | "middle" | "end";
    fill?: string;
  } = {},
): string {
  const { size = 3.4, weight = 400, anchor = "start", fill = "#1e293b" } = opts;
  return (
    `<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" ` +
    `text-anchor="${anchor}" fill="${fill}">${esc(content)}</text>`
  );
}

/**
 * Approximate rendered width in millimetres.
 *
 * SVG text does not wrap and does not report its own width without a DOM, so
 * anything that could be long has to be measured here before it is drawn. The
 * 0.52 factor is the average advance of this font stack relative to its size,
 * calibrated against measured glyph boxes; it is an estimate, but it only needs
 * to be good enough to decide where to break a line.
 */
function widthOf(content: string, size: number): number {
  return content.length * size * 0.52;
}

/**
 * Greedy word wrap to a millimetre budget.
 *
 * Exists because a long string was silently *clipped at the page edge*, not
 * merely ugly: the daylight-saving warning lost the sentence containing its
 * call to action, on a sheet whose whole purpose is to be read away from the
 * app. A very long single word is left over-long rather than broken mid-word.
 */
function wrap(content: string, size: number, maxWidth: number): string[] {
  const lines: string[] = [];
  let current = "";
  for (const word of content.split(/\s+/)) {
    const candidate = current ? `${current} ${word}` : word;
    if (current && widthOf(candidate, size) > maxWidth) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

/** Shorten to a width budget, keeping the start, which is the specific part. */
function ellipsize(content: string, size: number, maxWidth: number): string {
  if (widthOf(content, size) <= maxWidth) return content;
  const room = Math.max(4, Math.floor(maxWidth / (size * 0.52)) - 1);
  return `${content.slice(0, room).trimEnd()}…`;
}

function label(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta : term.en;
}

function shortLabel(term: Term, lang: Language): string {
  return lang === "ta" ? term.ta_short : term.en_short;
}

/** The square chart, in millimetres, ready to drop into the page. */
function grid(
  varga: VargaChart,
  rasis: Term[],
  grahas: Term[],
  lang: Language,
): string {
  const occupants = new Map<number, number[]>();
  for (const [key, rasi] of Object.entries(varga.graha_rasis)) {
    const gi = Number(key);
    occupants.set(rasi, [...(occupants.get(rasi) ?? []), gi]);
  }

  const parts: string[] = [];

  // Hollow centre, carrying the chart's own name.
  parts.push(
    `<rect x="${GRID_X + CELL_MM}" y="${GRID_Y + CELL_MM}" ` +
      `width="${CELL_MM * 2}" height="${CELL_MM * 2}" fill="#fffbeb"/>`,
  );
  parts.push(
    text(PAGE_W / 2, GRID_Y + CELL_MM * 2 - 2, varga.code, {
      size: 7,
      weight: 700,
      anchor: "middle",
      fill: "#92400e",
    }),
  );
  parts.push(
    text(PAGE_W / 2, GRID_Y + CELL_MM * 2 + 5, label(varga.name, lang), {
      size: 4.6,
      anchor: "middle",
      fill: "#78716c",
    }),
  );
  parts.push(
    text(PAGE_W / 2, GRID_Y + CELL_MM * 2 + 11, "கட்டம்", {
      size: 3.6,
      anchor: "middle",
      fill: "#a8a29e",
    }),
  );

  for (let rasi = 0; rasi < 12; rasi++) {
    const [col, row] = CELL[rasi];
    const x = GRID_X + col * CELL_MM;
    const y = GRID_Y + row * CELL_MM;
    const isLagna = rasi === varga.lagna_rasi;
    const house = (((rasi - varga.lagna_rasi) % 12) + 12) % 12 + 1;
    const here = occupants.get(rasi) ?? [];

    parts.push(
      `<rect x="${x}" y="${y}" width="${CELL_MM}" height="${CELL_MM}" ` +
        `fill="${isLagna ? "#fef3c7" : "#ffffff"}" stroke="#334155" stroke-width="0.4"/>`,
    );
    parts.push(
      text(x + 2, y + 5, label(rasis[rasi], lang), { size: 3.2, fill: "#475569" }),
    );
    parts.push(
      text(x + CELL_MM - 2, y + 5, String(house), {
        size: 3.2,
        weight: 600,
        anchor: "end",
        fill: "#64748b",
      }),
    );
    if (isLagna) {
      parts.push(
        text(x + 2, y + CELL_MM - 2.5, lang === "ta" ? "லக்னம்" : "ASC", {
          size: 3,
          weight: 700,
          fill: "#b45309",
        }),
      );
    }

    // Same count-aware packing as the screen chart: three per row once a cell
    // holds more than four, so a full house of nine still fits.
    const perRow = here.length <= 4 ? 2 : 3;
    const size = here.length > 6 ? 3.6 : 5;
    const pitch = Math.min(size + 1.6, (CELL_MM - 16) / Math.ceil(here.length / perRow));
    here.forEach((gi, i) => {
      const retro = varga.retrogrades.includes(gi) && gi !== 7 && gi !== 8;
      parts.push(
        text(
          x + 2.5 + (i % perRow) * ((CELL_MM - 4) / perRow),
          y + 9 + pitch * (Math.floor(i / perRow) + 1),
          shortLabel(grahas[gi], lang) + (retro ? "℞" : ""),
          { size, weight: 500, fill: "#0f172a" },
        ),
      );
    });
  }

  return parts.join("\n  ");
}

/** Placement table beneath the chart. */
function table(
  chart: Chart,
  varga: VargaChart,
  rasis: Term[],
  lang: Language,
): string {
  const top = GRID_Y + GRID + 10;
  const isRasiChart = varga.code === "D1";
  const parts: string[] = [];

  // Self-fitting row pitch. The D1 table is always exactly 9 graha rows plus a
  // lagna row, and a fixed pitch put the last two rows *on top of the footer*
  // and then off the bottom of the sheet. Deriving the pitch from the space
  // that actually remains makes that unrepresentable rather than merely fixed.
  const firstRow = top + 12;
  const pitch = Math.min(5.6, (FOOTER_Y - FOOTER_GAP - firstRow) / 8);

  const cols = isRasiChart
    ? [MARGIN, 48, 88, 120, 158, 176]
    : [MARGIN, 60, 110, 160];
  const heads = isRasiChart
    ? ["Graha", "Rasi", "Degree", "Nakshatra", "Pada", "Bhava"]
    : ["Graha", "Rasi", "Graha", "Rasi"];

  heads.forEach((h, i) =>
    parts.push(text(cols[i], top, h, { size: 3, weight: 700, fill: "#64748b" })),
  );
  parts.push(
    `<line x1="${MARGIN}" y1="${top + 1.6}" x2="${PAGE_W - MARGIN}" y2="${top + 1.6}" stroke="#cbd5e1" stroke-width="0.3"/>`,
  );

  if (isRasiChart) {
    const lagna = chart.lagna;
    const lagnaY = top + 6;
    parts.push(text(cols[0], lagnaY, lang === "ta" ? "லக்னம்" : "Lagna", { size: 3.4, weight: 700, fill: "#b45309" }));
    parts.push(text(cols[1], lagnaY, label(lagna.rasi_name, lang), { size: 3.4, fill: "#b45309" }));
    parts.push(text(cols[2], lagnaY, lagna.formatted, { size: 3.2, fill: "#b45309" }));
    parts.push(text(cols[3], lagnaY, label(lagna.nakshatra_name, lang), { size: 3.4, fill: "#b45309" }));
    parts.push(text(cols[4], lagnaY, String(lagna.pada), { size: 3.4, fill: "#b45309" }));
    parts.push(text(cols[5], lagnaY, "1", { size: 3.4, fill: "#b45309" }));

    chart.grahas.forEach((g, i) => {
      const y = firstRow + i * pitch;
      const retro = g.retrograde && g.graha !== 7 && g.graha !== 8;
      parts.push(text(cols[0], y, label(g.name, lang) + (retro ? " ℞" : ""), { size: 3.4 }));
      parts.push(text(cols[1], y, label(g.position.rasi_name, lang), { size: 3.4 }));
      parts.push(text(cols[2], y, g.position.formatted, { size: 3.2 }));
      parts.push(text(cols[3], y, label(g.position.nakshatra_name, lang), { size: 3.4 }));
      parts.push(text(cols[4], y, String(g.position.pada), { size: 3.4 }));
      parts.push(text(cols[5], y, String(g.house), { size: 3.4 }));
    });
  } else {
    // Two columns of graha -> rasi for the divisional charts.
    chart.grahas.forEach((g, i) => {
      const col = i < 5 ? 0 : 2;
      const y = top + 6 + (i % 5) * pitch;
      const rasi = varga.graha_rasis[String(g.graha)];
      const retro = varga.retrogrades.includes(g.graha) && g.graha !== 7 && g.graha !== 8;
      parts.push(text(cols[col], y, label(g.name, lang) + (retro ? " ℞" : ""), { size: 3.4 }));
      parts.push(text(cols[col + 1], y, label(rasis[rasi], lang), { size: 3.4 }));
    });
  }

  return parts.join("\n  ");
}

/** A complete A4 sheet for one divisional chart. */
export function buildA4Svg(
  chart: Chart,
  varga: VargaChart,
  rasis: Term[],
  grahas: Term[],
  lang: Language,
  personName?: string,
): string {
  const b = chart.birth;
  const [date, time] = b.local_datetime.split("T");

  const header: string[] = [];
  // Budgeted, not free-running: the title shares its line with the right-aligned
  // chart name, and an unbounded name ran hundreds of millimetres off the sheet.
  header.push(
    text(MARGIN, 16, ellipsize(personName?.trim() || "ஜாதகம் · Jathagam", 7, 110), {
      size: 7,
      weight: 700,
    }),
  );
  header.push(
    text(
      PAGE_W - MARGIN,
      16,
      `${varga.code} · ${varga.name.ta} / ${varga.name.en}`,
      { size: 5, weight: 600, anchor: "end", fill: "#92400e" },
    ),
  );
  header.push(
    `<line x1="${MARGIN}" y1="20" x2="${PAGE_W - MARGIN}" y2="20" stroke="#94a3b8" stroke-width="0.5"/>`,
  );

  // Two short columns, then Place on its own full-width row. Place used to
  // share a column with a 72mm budget, and a name longer than about 44
  // characters simply painted over the Ayanamsa label and value beside it --
  // which happens for 11,604 places in the shipped index, Ho Chi Minh City
  // among them. Truncating is honest; overprinting is not.
  const pairs: [string, string][] = [
    ["Birth date", date],
    ["Coordinates", `${b.latitude.toFixed(4)}, ${b.longitude.toFixed(4)}`],
    ["Birth time", `${time}  (${b.time_12h})`],
    ["Time zone", `${b.timezone}  ${b.utc_offset}`],
    ["Ayanamsa", `${chart.ayanamsa}  ${chart.ayanamsa_formatted}`],
  ];
  pairs.forEach(([k, v], i) => {
    const x = MARGIN + (i % 2) * 98;
    const y = 27 + Math.floor(i / 2) * 5.4;
    header.push(text(x, y, k, { size: 3, fill: "#64748b" }));
    header.push(text(x + 26, y, v, { size: 3.4, weight: 500 }));
  });

  const fullWidth = PAGE_W - MARGIN * 2;
  const place = b.place_name ?? `${b.latitude.toFixed(4)}, ${b.longitude.toFixed(4)}`;
  header.push(text(MARGIN, 43.2, "Place", { size: 3, fill: "#64748b" }));
  header.push(
    text(MARGIN + 26, 43.2, ellipsize(place, 3.4, fullWidth - 26), {
      size: 3.4,
      weight: 500,
    }),
  );

  // Notes and warnings wrap. The daylight-saving warning runs to ~204
  // characters, which on one line is 270mm wide on a 210mm page -- it was
  // clipped at the paper edge, losing the sentence that tells the reader what
  // to do about it.
  let noteY = 49;
  for (const [prefix, body] of [
    ["Note", b.offset_note],
    ["Check", chart.time_warning],
  ] as const) {
    if (!body) continue;
    for (const line of wrap(`${prefix}: ${body}`, 2.9, fullWidth)) {
      header.push(text(MARGIN, noteY, line, { size: 2.9, fill: "#b45309" }));
      noteY += 3.8;
    }
  }

  header.push(
    text(PAGE_W / 2, Math.max(noteY + 2, 62), ellipsize(varga.significance, 3.2, fullWidth), {
      size: 3.2,
      anchor: "middle",
      fill: "#78716c",
    }),
  );

  const footer =
    text(MARGIN, PAGE_H - 8, `Engine ${chart.engine_version} · sidereal, South Indian`, {
      size: 2.6,
      fill: "#94a3b8",
    }) +
    text(PAGE_W - MARGIN, PAGE_H - 8, "Place data © GeoNames CC BY 4.0", {
      size: 2.6,
      anchor: "end",
      fill: "#94a3b8",
    });

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm"
     viewBox="0 0 ${PAGE_W} ${PAGE_H}" font-family="${FONT}">
  <title>${esc(varga.code)} ${esc(varga.name.en)} — ${esc(personName?.trim() || "Jathagam")}</title>
  <rect width="${PAGE_W}" height="${PAGE_H}" fill="#ffffff"/>
  ${header.join("\n  ")}
  ${grid(varga, rasis, grahas, lang)}
  ${table(chart, varga, rasis, lang)}
  ${footer}
</svg>
`;
}

/** Trigger a browser download of one chart as an A4 SVG. */
export function downloadChart(
  chart: Chart,
  varga: VargaChart,
  rasis: Term[],
  grahas: Term[],
  lang: Language,
  personName?: string,
): void {
  const svg = buildA4Svg(chart, varga, rasis, grahas, lang, personName);
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const who = (personName?.trim() || "jathagam").replace(/[^\w஀-௿-]+/g, "-");
  const link = document.createElement("a");
  link.href = url;
  link.download = `${who}-${chart.birth.local_datetime.slice(0, 10)}-${varga.code}.svg`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Revoke on the next tick; revoking immediately can cancel the download in
  // some browsers before it has read the blob.
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
