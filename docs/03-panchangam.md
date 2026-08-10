# 03 — Panchangam: the Tamil daily almanac

*Assumes [00-orientation.md](00-orientation.md). Everything else is explained
here.*

---

## What a panchangam is

Every Tamil household that keeps a calendar keeps a **panchangam** (பஞ்சாங்கம்).
It is the daily almanac: what lunar day it is, which star the Moon is in, which
stretches of the day to avoid, and when the good hours fall.

*Pancha-anga* means **five limbs**, and those five are the whole system:

| Limb | Tamil | What it is |
|---|---|---|
| **Tithi** | திதி | The lunar day — how far the Moon has pulled ahead of the Sun |
| **Vaara** | கிழமை | The weekday |
| **Nakshatra** | நட்சத்திரம் | The Moon's star |
| **Yoga** | யோகம் | Sun and Moon added together |
| **Karana** | கரணம் | Half a tithi |

Everything else an almanac prints — rahu kalam, gowri panchangam, nalla neram,
the Tamil date — is built on those five plus sunrise and sunset.

---

## The one rule that changes everything: the day starts at sunrise

The civil day rolls over at midnight. **The Jyotish day rolls over at sunrise.**

So a child born at 03:00 on a Tuesday is born on **Monday's** vaara. Monday's
rahu kalam is the one that applied. Monday's gowri windows are the ones in force.

This is not a technicality. It is stated plainly in every Tamil almanac, and
consumer apps get it wrong constantly — they read the weekday off the calendar
date and everything downstream shifts by a day. This engine takes the vaara from
the sunrise-to-sunrise day, and there is a test
(`test_a_birth_before_sunrise_belongs_to_the_previous_weekday`) that fails if
anyone changes it back.

---

## The five limbs, one at a time

### Tithi (திதி) — the lunar day

The Moon moves faster than the Sun. A **tithi** is each 12° it gains:

```
tithi = ⌊ (Moon − Sun) / 12° ⌋      →  30 per lunar month
```

Thirty tithis make a lunar month, split into two fortnights (**paksha**):

- **வளர்பிறை** (Shukla, waxing) — tithis 1 to 14, ending at **பௌர்ணமி** (full moon)
- **தேய்பிறை** (Krishna, waning) — tithis 1 to 14, ending at **அமாவாசை** (new moon)

Because the Moon's speed varies, a tithi is not a fixed length — anywhere from
about 20 to 27 hours. That is why an almanac prints an *ending time* rather than
a duration.

### Vaara (கிழமை) — the weekday

Seven days, each ruled by a graha, which is where the names come from: ஞாயிறு is
the Sun, திங்கள் the Moon, செவ்வாய் Mars, and so on. Sunrise-to-sunrise, per
above.

### Nakshatra (நட்சத்திரம்) — the Moon's star

The Moon's sidereal longitude in 13°20′ steps — the same 27 nakshatras as the
birth chart, asked of *today's* Moon rather than the birth Moon.

### Yoga (யோகம்)

The Sun and Moon **added**, in the same 13°20′ steps:

```
yoga = ⌊ (Moon + Sun) / 13°20′ ⌋    →  27 of them
```

Nine of the 27 are conventionally inauspicious, and two — **வியதீபாதம்**
(Vyatipata) and **வைதிருதி** (Vaidhriti) — are treated as outright dosha.

### Karana (கரணம்) — half a tithi

Six degrees of elongation, so 60 per lunar month. Eleven names fill those 60
slots in a deliberately irregular pattern: **seven "movable" karanas cycle eight
times** to fill 56 slots, and **four "fixed" ones** take the rest — Kimstughna
opens the lunar month, and Shakuni, Chatushpada and Naga close it.

The one that matters in practice is **விஷ்டி / பத்திரை** (Vishti, also called
Bhadra). Nothing auspicious is begun during Bhadra. It lands on exactly eight of
the sixty slots, and reproducing that pattern is the correctness check for the
whole mapping — `test_bhadra_falls_exactly_where_the_classical_rule_says`.

---

## Why the ayanamsa matters for two limbs and not the other two

This is the single most common fatal bug in panchangam code, so it is worth
being precise.

| Limb | Formula | Ayanamsa? |
|---|---|---|
| Tithi | Moon **−** Sun | **Cancels exactly.** Same answer in any system |
| Karana | Moon **−** Sun | **Cancels exactly** |
| Nakshatra | Moon | Enters **once** |
| Yoga | Moon **+** Sun | Enters **twice** |

Because yoga is a *sum*, computing it from tropical longitudes is wrong by
**2 × 24° ≈ 48°** — three and a half yogas out, and confidently plausible.
Both properties are pinned by tests
(`test_tithi_and_karana_do_not_depend_on_the_ayanamsa` and its complement).

---

## The periods to avoid

Sunrise to sunset is divided into **eight equal parts**, and three of them have
names:

| Tamil | Ruled by | Sunday | Monday | Tuesday | Wednesday | Thursday | Friday | Saturday |
|---|---|---|---|---|---|---|---|---|
| **ராகு காலம்** | — | 16:30 | 07:30 | 15:00 | 12:00 | 13:30 | 10:30 | 09:00 |
| **எமகண்டம்** | Jupiter | 12:00 | 10:30 | 09:00 | 07:30 | 06:00 | 15:00 | 13:30 |
| **குளிகை** | Saturn | 15:00 | 13:30 | 12:00 | 10:30 | 09:00 | 07:30 | 06:00 |

Those clock times assume a 06:00 sunrise and 18:00 sunset, which is how they are
always taught. **The real windows are not 90 minutes.** An eighth of the daylight
in Chennai runs from about 85 to 97 minutes across the year, and in London from
about 59 to 125. The engine computes the actual interval.

Yamagandam and kuligai are not arbitrary tables — Brihat Parashara Hora gives a
rule: the first eighth belongs to the weekday's lord and the rest follow in
weekday-lord order, with the eighth part lordless. Yamagandam is simply
*Jupiter's* portion, kuligai *Saturn's*. Rahu is the exception, having no weekday
lordship, so its table is genuinely a table.

---

## Gowri panchangam and நல்ல நேரம்

**கௌரி பஞ்சாங்கம்** names all eight parts of the day, and eight more across the
night. Each belongs to a graha:

| Tamil | Graha | Meaning | |
|---|---|---|---|
| **அமிர்தம்** | Moon | nectar | ✔ best |
| **உத்தியோகம்** | Sun | employment | ✔ |
| **லாபம்** | Mercury | profit | ✔ |
| **தனம்** | Jupiter | wealth | ✔ |
| **சுகம்** | Venus | comfort | ✔ |
| **ரோகம்** | Mars | disease | ✘ |
| **சோரம்** | Saturn | theft | ✘ |
| **விஷம்** | Rahu | poison | ✘ |

Two traps worth naming, because both are common in circulation:

- **சோரம், not சோகம்.** சோரம் is theft (from *chora*). சோகம् (sorrow) is a
  corruption that appears in no Tamil primary source.
- **தனம், not தானம்.** தனம் is wealth (*dhana*). தானம் is charity — a different
  word entirely.
- A set printed by many English astrology sites — *Amrit, Shubha, Kala, Ugra* —
  is **Choghadiya**, a North Indian system. It is not Gowri.

### It is not a single list rotated

This is the part that looks simple and is not. Naive rotation of the eight names
by weekday reproduces Sunday correctly and gets **all six other weekdays wrong**,
because Visham sits at a weekday-dependent position. There are three wheels:

| Wheel | Visham sits… | Used by |
|---|---|---|
| A | after Saturn | Sunday, Wednesday |
| B | after the Moon | Monday, Thursday |
| C | after the Sun | Tuesday, Friday, **Saturday** |

Saturday takes wheel C rather than A, which breaks an otherwise tidy pattern. The
engine stores all fourteen sequences literally — so a Tamil reader can check them
against an almanac without reading code — and a test re-derives every one of the
112 cells from the rule to catch a transcription slip.

### What நல்ல நேரம் means here

**On this app's screens, நல்ல நேரம் is the auspicious gowri windows** — அமிர்தம்,
உத்தியோகம், லாபம், தனம் and சுகம். That is what panchangam software universally
means by it.

A printed tear-off Tamil calendar prints something *different* under the same
heading: fixed one-hour bands, quantised to a notional 06:00–18:00 grid, near
constant per weekday with a seasonal shift. They are demonstrably not a readout
of the good gowri slots — sample any week and you will find two days where the
printed band lands on Soram or Rogam. We compute the software definition and say
so on screen, rather than silently picking one and letting you discover the
difference against your wall calendar.

---

## The Tamil calendar

A pure **sidereal solar** calendar. The month *is* the Sun's rasi:

| # | Month | Sun enters | # | Month | Sun enters |
|---|---|---|---|---|---|
| 1 | சித்திரை | Mesha (~14 Apr) | 7 | ஐப்பசி | Thula |
| 2 | வைகாசி | Rishabam | 8 | கார்த்திகை | Viruchigam |
| 3 | ஆனி | Mithunam | 9 | மார்கழி | Dhanusu |
| 4 | ஆடி | Kadagam | 10 | தை | Magaram |
| 5 | ஆவணி | Simmam | 11 | மாசி | Kumbam |
| 6 | புரட்டாசி | Kanni | 12 | பங்குனி | Meenam |

**Month lengths are computed, never assumed** — they run from 29 to 32 days. In
2026–27, Karthigai is 29 days and Aani is 32.

**Which day is the 1st?** A sankranti happens at an arbitrary instant, so some
day has to be numbered one. Tamil Nadu uses the **sunset rule**: sankranti before
sunset, that day is the 1st; after sunset, the next day is. Kerala switches on
mid-afternoon and Bengal at midnight, so a Tamil and a Malayalam almanac can
print different dates for the same instant and both be right for their own
tradition.

**The year** carries one of sixty names, cycling with no gaps. Chithirai 2026
opened **பராபவ** (Parabhava), the fortieth. The app anchors the whole cycle on
that one checkable fact.

**Ayanam** is sidereal here: உத்தராயணம் begins at Makara sankranti, roughly 24
days after the astronomical solstice, and Tamil almanacs print that sidereal
turn rather than the tropical one.

Note that the ayanam and the month turn on **different rules**, so they need not
change on the same day. The month follows the sunset rule above; the ayanam
follows the Sun's rasi at daybreak. On 14 January 2026 the two disagree — Makara
sankranti fell at 15:07, before sunset, so that whole day is **தை 1** while the
ayanam was still **தட்சிணாயனம்** because the Sun was in Dhanus when the day
dawned. That is what Drik Panchang prints for the day, and it is not a bug in
either of us.

**Ritu** (season) uses the Surya-Siddhanta *saura* scheme keyed to the sidereal
solar month, in which Vasanta is **Meena *and* Mesha** — Panguni and Chithirai
together. Be aware that this is the one field where we cannot point at a
published source that computes it the same way: Drik's "Ritu" tracks the
*tropical* Sun and its "Vedic Ritu" tracks the *lunar* month, and the classical
Tolkappiyam paruvakkaalam of Tamil literature runs a month later again. All four
are real; the sidereal saura phase is independently attested for nirayana saura
masa, which is why it is the one implemented, but expect this line to differ from
other sites more often than any other on the page.

---

## Two traditions, and why you may see different times

Tamil Nadu has two live almanac traditions:

- **திருக்கணித (Thirukanitha / drik)** — modern ephemeris with Lahiri ayanamsa.
  Introduced through the Madras Observatory, and what all software, the Rashtriya
  Panchang and most practising astrologers use. **This is what we implement.**
- **வாக்கிய (Vakya)** — Surya-Siddhanta mnemonic tables, as in the Pambu
  Panchangam. Still used for temple ritual.

They can differ by several hours on a tithi or nakshatra ending, and by a day on
festivals. If our times disagree with a temple almanac by hours rather than
minutes, this is why, and neither is a bug.

---

## When there is no sunrise

Above the Arctic Circle the Sun does not rise for weeks in winter or set for
weeks in summer. Rahu kalam, the gowri windows and nalla neram are all **fractions
of the interval between sunrise and sunset** — with no such interval they have no
definition.

The app says so and omits them, rather than fabricating a 06:00. The five limbs
are unaffected: they are longitudes, and longitudes do not care about the
horizon.

---

## Try it

```bash
python scripts\chart.py --date 2026-08-10 --time 12:00 --place "Chennai" --pick 1 --panchangam
```

Then check it against a Tamil calendar for the same day. The gowri windows should
match to the minute; if the *names* match but the times are a minute or two out,
that is sunrise rounding, not a disagreement.

---

**Next:** Phase 3 is **KP (Krishnamurti Paddhati)**, and
`docs/04-kp-system.md` will teach it from zero.
