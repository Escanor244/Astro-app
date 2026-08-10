# Phase 1c testing — chart library, A4 export, theme

What Phase 1c added:

- **A saved chart library** — save a birth, reopen it, rename it, delete it.
- **A4 export** — one sheet per chart, as SVG or via print.
- **Light / dark / system theme**, and larger type throughout.
- **[docs/ayanamsa.md](../ayanamsa.md)** and an ⓘ panel beside the selector.

Prerequisite: [phase-1b.md](phase-1b.md) setup, both processes running.

---

## 1. Automated tests

```bash
cd services\jyotish && python -m pytest tests\ -q     # 521 tests
cd apps\web && npm test && npm run build              # 54 tests + type-check
```

Two of these deserve naming, because they cover failures that shipped green in
the first cut of this phase:

- `test_an_older_record_stays_readable_after_rules_tighten` — validation gates
  what comes *in*; it must never lock stored data in. Adding an ephemeris range
  check made one older row fail on *read*, and since that read happens inside
  the list endpoint, a single record returned 500 and **hid every other saved
  chart**.
- `test_cors_allows_every_method_the_api_exposes` — issues a real preflight.
  `TestClient` is same-process and never sends one, which is exactly why PUT and
  DELETE shipped blocked in the browser with a fully green suite.

## 2. The library

| # | Action | Expect |
|---|---|---|
| 1 | Cast a chart, press **Save to library** | Appears in the list on the left |
| 2 | Click the saved row | Form repopulates and the chart re-casts |
| 3 | With a record open, press **Update saved chart** | Same row updates; no duplicate |
| 4 | Edit any form field after opening a record | Button reverts to **Save to library** |
| 5 | Save 4+ records | A search box appears; try a name and a place |
| 6 | Click **×** then **Delete** | Row disappears and stays gone after reload |
| 7 | Click **×** then **Keep** | Nothing is deleted |

Item 4 is deliberate: editing detaches the form from the record it came from,
so you never silently overwrite the original.

**Item 6 is the one to actually check**, because it was broken twice over —
CORS blocked the request, and the UI treated the failure as success, so the row
vanished from the screen while surviving on disk.

### What a record stores, and why

A record keeps the **resolved** latitude, longitude, timezone and place name —
not just the `geonameid`. The place index is a 100 MB build artifact regenerated
from a GeoNames download with no recorded vintage; if a record re-resolved the
id on read, rebuilding the index could silently move a saved chart with nothing
to diff against.

Computed charts are **not** stored. A chart is a pure function of its inputs and
the engine version, so caching one would only create a second thing that can go
stale. Opening a record re-casts it, which means a correctness fix reaches every
saved chart for free.

You can confirm both properties: `test_a_record_needs_no_place_index_at_all`
saves a record with a `geonameid` that exists nowhere and still round-trips.

## 3. A4 export

| # | Action | Expect |
|---|---|---|
| 8 | **↓ A4** on any chart | Downloads `<name>-<date>-<code>.svg` |
| 9 | Open the file in a browser | One A4 sheet: header, chart, placement table, footer |
| 10 | Print it (Ctrl+P) | Fits one page, nothing clipped |
| 11 | **↓ Download all as A4** | One file per selected chart |
| 12 | **Print / Save as PDF** | One A4 page per chart; no form or buttons on paper |
| 13 | Export in **தமிழ்** | Rasi names, graha labels and லக்னம் all in Tamil |
| 14 | Export a chart on a DST boundary | The warning wraps across lines; nothing cut off at the edge |
| 15 | Export a birth in a very long-named place | Place fits its own row, never overprints Ayanamsa |

Items 14 and 15 were real defects. SVG text does not wrap, so a 204-character
daylight-saving warning ran 270 mm wide on a 210 mm page and was **clipped at
the paper edge**, losing the sentence that told the reader what to do. A long
place name painted straight over the Ayanamsa value — which affects 11,604
places in the shipped index.

The one to check most carefully is **item 9 on a D1 sheet**. The table is always
exactly 9 graha rows plus a lagna row, and with a fixed row pitch the last two
rows printed *on top of the footer* and then ran off the bottom of the paper.
The pitch is now derived from the space that remains, and the tests measure
rendered extent rather than anchor positions — measuring anchors is why it
shipped green.

## 4. Theme and readability

| # | Action | Expect |
|---|---|---|
| 16 | Click ☀ / ☾ / ◐ | Light, dark, follow-the-OS |
| 17 | Reload | Your choice persists, with no flash of the wrong theme |
| 18 | On ◐, change the OS theme | Page follows without a reload |
| 19 | Read a chart | Degrees line up in a column (tabular numerals) |

Item 17 is why the theme script is inline and blocking in `layout.tsx`: anything
deferred runs *after* the browser has already painted.

## 5. Known limitations

- **Export embeds no fonts.** Tamil renders using a system font (Noto Sans
  Tamil, Nirmala UI or Latha). On a machine with none of them, Tamil in the
  exported file may not render — embedding one would add megabytes per sheet.
- **The library is local and unauthenticated**, like the rest of the app. The
  file is `data/library.sqlite`; back it up by copying it with the engine
  stopped.
- **No import/export of the library itself** yet, and no bulk operations.
- **Records are not versioned.** Updating one overwrites it.
