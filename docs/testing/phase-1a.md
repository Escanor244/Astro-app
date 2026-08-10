# Phase 1a testing — Navamsam, divisional charts, and birth-time entry

What Phase 1a added:

- **D9 Navamsam (நவாம்சம்)** and the full Shodashavarga — sixteen divisional
  charts.
- **AM/PM birth-time entry**, closing a silent-wrong-answer bug.

Prerequisite: [phase-0.md](phase-0.md) setup, with the virtualenv activated.

---

## 1. See the Navamsam

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1 --varga d1,d9
```

You get two square charts: the ராசி கட்டம் you already validated, then the
நவாம்சம் கட்டம் below it.

Other useful forms:

```bash
--varga d9              # Navamsam alone
--varga d1,d9,d10       # Rasi, Navamsam, Dasamsam (career)
--varga all             # the complete Shodashavarga, all sixteen
```

### Why Navamsam matters

It is the second chart every Tamil astrologer reads, and it is why a Rasi chart
shown on its own looks incomplete to anyone who practises. It is used for
marriage, dharma, and for judging the real strength of each graha: a graha that
looks strong in the Rasi chart but falls badly in D9 is treated as weaker than
it appears.

Each rasi is divided into nine parts of 3°20′. Which rasi each part maps to
depends on whether the sign is movable, fixed or dual.

---

## 2. Verify it against your online source

This is the check that matters, and it is the same method that validated the
Rasi chart.

1. Generate the chart with `--varga d1,d9`.
2. Open the same birth details on the site you used before.
3. Compare **graha by graha**: which rasi each graha sits in, in the நவாம்சம்
   கட்டம். Compare the Navamsa lagna too.

**Before concluding anything is wrong,** confirm both sides use **Lahiri**
ayanamsa and the **South Indian** chart style. Those two settings cause more
false mismatches than genuine bugs. See
[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

---

## 3. Birth-time entry

`--time` now takes either notation. A bare time is still 24-hour.

| Command | Means | Expect |
|---|---|---|
| `--time 06:30` | 6:30 in the morning | header shows `(6:30 AM)` |
| `--time 18:30` | 6:30 in the evening | header shows `(6:30 PM)` |
| `--time "6:30 PM"` | same as `18:30` | identical chart to `18:30` |
| `--time "6:30 AM"` | same as `06:30` | identical chart to `06:30` |
| `--time "13:30 PM"` | contradictory | **rejected** with an explanation |

The output always echoes the 12-hour reading:

```
Birth   : 1990-05-15  06:30:00  (6:30 AM)
```

**Try this, it is the whole point.** Run the same birth as morning and evening:

```bash
python scripts\chart.py --date 1990-05-15 --time "6:30 AM" --place "Chennai" --pick 1
python scripts\chart.py --date 1990-05-15 --time "6:30 PM" --place "Chennai" --pick 1
```

The lagna moves from **Taurus** to **Scorpio** — exact opposites, six rasis
apart. Twelve hours of error is about 180° of ascendant, so an AM/PM slip
produces a chart that is wrong in every particular while looking completely
plausible. That is why the app echoes the time back and refuses to guess.

---

## 4. Automated tests

```bash
python -m pytest tests\test_vargas.py -q          # divisional charts
python -m pytest tests\test_timezones.py -q       # includes time entry
```

### How the vargas are verified

Divisional charts are pure arithmetic on longitudes — no new astronomy — so they
inherit Phase 0's accuracy exactly. The risk is not precision but **getting a
rule wrong**, and a wrong Navamsam is immediately obvious to anyone who
practises.

So the rules are cross-validated. Ours are derived from the classical texts;
`jyotishganit` is an independent implementation. The suite compares the two at
25 points in every sign, including exact division boundaries. Two implementations
agreeing from different derivations is evidence; one implementation alone is an
assumption.

**Fifteen of the sixteen divisions agree exactly.** The exception is documented
below.

### The one deliberate disagreement: D30 Trimsamsa

D30 is the only division with *unequal* parts, and implementations differ.

Brihat Parashara Hora Shastra gives odd signs as Mars 0–5°, Saturn 5–10°,
Jupiter 10–18°, Mercury 18–25°, Venus 25–30°, and even signs as **the exact
reverse**: Venus 0–5°, Mercury 5–12°, Jupiter 12–20°, Saturn 20–25°, Mars
25–30°.

`jyotishganit` instead puts Saturn at 12–19° and Jupiter at 19–24° in even
signs, which swaps the pair and does not mirror its own odd-sign sequence. We
follow the text.

The test suite **asserts this disagreement** rather than skipping D30, so that
if the reference implementation is ever corrected upstream we find out instead
of silently drifting.

### Two bugs the cross-check caught

Both were ours, and neither was visible without a second implementation to
compare against:

1. **A floating-point boundary error.** 30/9 is not representable in binary, so
   20° — precisely the start of the 7th navamsa of Aries — divided to
   5.999999… and floored into the *previous* navamsa. Every exact boundary in
   D9 and D27 was off by one part.
2. **Two code paths disagreeing.** The rasi and the part-within-rasi were being
   derived by different arithmetic, so at exact boundaries they could land one
   part apart. They now come from a single calculation and cannot disagree.

Neither moved a graha by a meaningful distance — the errors were about 1e-14
degrees — but both would have put a graha in the wrong *navamsa* at exact
boundaries, which is a visible, wrong answer.

---

## 5. What to check by hand

| # | Command | Expect |
|---|---|---|
| 1 | `--varga d1,d9` on your own birth details | two charts; D1 identical to what you already validated |
| 2 | `--varga all` | sixteen charts, each labelled with its Tamil name and meaning |
| 3 | `--varga d5` | rejected — there is no D5 in the Shodashavarga |
| 4 | `--time "6:30 AM"` vs `--time 06:30` | identical charts |
| 5 | `--time "6:30 PM"` vs `--time 18:30` | identical charts |
| 6 | `--time "13:30 PM"` | rejected, with a suggestion |
| 7 | D9 for a graha at 0° of a movable sign | lands in the same sign (Aries 0° → Aries) |

Item 7 is a quick way to sanity-check the rule by hand: movable signs start
their navamsa count from themselves, fixed signs from the 9th sign, dual signs
from the 5th.

---

## Known limitations

- **Vargas beyond D9 are cross-validated but not yet checked against Jagannatha
  Hora.** D9 is the one that matters in practice and gets the most attention;
  the rarer divisions rely on the cross-implementation agreement above.
- **Varga degrees are not shown**, only the rasi each graha falls in. That is
  what the square chart displays. Degree-within-varga can be added if the KP
  work in Phase 3 needs it.
- **No varga-specific strength calculations yet** (vargottama, shadbala).
  Those belong with the Phase 2 dasha work.
