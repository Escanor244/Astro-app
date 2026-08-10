# 02 — Dasha: the astrology of *when*

*Assumes you have read [00-orientation.md](00-orientation.md). No prior Jyotish
knowledge beyond that.*

---

## The problem dasha solves

A birth chart is a photograph. It says what a life contains — but a photograph
has no clock in it. Two people with nearly identical charts do not have the same
thing happen to them in the same year.

Vedic astrology answers this with **dasha** (தசை / திசை): the life is divided
into planetary periods, each ruled by one graha, running in a fixed order from
birth to death. Whatever a graha promises in the chart is understood to *arrive*
during its period.

This is the part of Jyotish that has no real Western equivalent, and in Tamil
practice it is where a consultation actually spends its time. A Tamil almanac
prints a newborn's dasha balance next to its birth star, and it follows the
person for life.

There are dozens of dasha systems. **Vimshottari** (விம்சோத்தரி) is the one
everybody uses — it is the default in every Tamil almanac and every serious
program, and it is what this engine implements.

---

## The mechanism, in one page

### 1. Nine lords, 120 years

*Vimshottari* means "one hundred and twenty". Each graha owns a fixed number of
years, and they sum to exactly 120:

| Order | Graha | Tamil | Years |
|---|---|---|---|
| 1 | Ketu | கேது | 7 |
| 2 | Venus | சுக்கிரன் | 20 |
| 3 | Sun | சூரியன் | 6 |
| 4 | Moon | சந்திரன் | 10 |
| 5 | Mars | செவ்வாய் | 7 |
| 6 | Rahu | ராகு | 18 |
| 7 | Jupiter | குரு | 16 |
| 8 | Saturn | சனி | 19 |
| 9 | Mercury | புதன் | 17 |
| | | **total** | **120** |

That order is fixed and cyclic. After Mercury comes Ketu again.

### 2. Your birth star picks the starting lord

The 27 nakshatras are assigned to those nine lords in that same repeating
order — Ashwini to Ketu, Bharani to Venus, Krittika to the Sun, and so on around
three times. So each graha owns exactly three nakshatras, 120° apart.

**The dasha running at your birth is the lord of the nakshatra your Moon was
in.** Not the Sun, not the lagna. The Moon.

This is why your birth star (ஜென்ம நட்சத்திரம்) is the single most-quoted fact
about a Tamil horoscope.

### 3. You are born partway through it

The Moon does not politely arrive at the start of a nakshatra when you are born.
It is usually somewhere in the middle — and *how far through the star it has
travelled is how much of that period is already spent*.

```
Moon at 40% through Rohini  →  Moon dasha, 60% of its 10 years remaining
                            →  balance = 6 years
```

That remaining piece is the **dasha balance** (திசை இருப்பு), and it is printed
on every horoscope. It is the one number that fixes the entire timeline of your
life: get it wrong and every date afterwards is wrong by the same amount.

> **The classic bug.** It is the *remaining* fraction, not the elapsed one. Using
> elapsed gives you the years that ran out **before** you were born. Every
> reference implementation warns about this, which tells you how often it
> happens.

### 4. Then it just runs

After your first (partial) mahadasha ends, the next lord in the cycle takes over
for its full term, then the next, and so on. Nine of them covers 120 years, which
is one complete cycle.

---

## The five levels

Each mahadasha is subdivided by the same nine lords, in the same order, in the
same proportions — and then each of *those* is subdivided again, five levels
deep.

| Level | Sanskrit | Tamil | Typical length |
|---|---|---|---|
| 1 | Mahadasha | **தசை** | 6–20 years |
| 2 | Antardasha / Bhukti | **புத்தி** | months to 3 years |
| 3 | Pratyantardasha | **அந்தரம்** | days to months |
| 4 | Sookshma | **சூட்சுமம்** | hours to days |
| 5 | Prana | **பிராணன்** | minutes to hours |

One rule generates every level:

```
duration(level n) = duration(level n−1) × lord's years / 120
```

and every sequence **starts with its own parent's lord**. Venus mahadasha opens
with Venus–Venus, then Venus–Sun, Venus–Moon, and around the cycle.

> **A naming trap if you read North Indian books.** North Indian usage calls
> level 2 *antardasha*. Tamil usage calls level 2 **புத்தி** and reserves
> **அந்தரம்** for level **3**. Same arithmetic, shifted vocabulary. This app
> labels the Tamil column in the Tamil convention, so a Tamil astrologer reading
> the second column sees புத்தி where they expect it.

The app fetches one level per click rather than the whole tree, for a boring but
absolute reason: five levels of nine lords is **59,049 periods**.

---

## Reading the table in the app

Cast a chart and scroll to **விம்சோத்தரி தசை**.

- **Dasha balance at birth** — the amber box. Fixed for life.
- **Running** — the five-level chain for a date you choose. Change the date and
  it re-resolves. This is the question a consultation actually asks.
- **The table** — click any row to open its sub-periods. The breadcrumb above
  walks back up. The row highlighted amber with a `now` badge is the one
  containing your chosen date; greyed rows are already past.

Dates are shown in **local time at the birth place**, which is what a printed
jathagam uses — even if the person now lives somewhere else.

---

## The one setting: how long is a dasha year?

This is the only genuine convention choice in the whole module, and it is worth
five minutes of your attention because it is the thing most likely to make this
app disagree with a printed almanac.

A "year" of dasha has to be converted into days at some point. Traditions differ:

| Setting | Days | What it is |
|---|---|---|
| **julian** *(default)* | 365.25 | The classical 365¼ |
| sidereal | 365.256364 | The Sun's return to the same star. Jagannatha Hora's default |
| gregorian | 365.2425 | The civil calendar's mean year |
| tropical | 365.242190 | Equinox to equinox |
| savana | 360 | The older 360-day sacrificial civil year |

**The first four do not matter.** Their worst-case disagreement is 0.85 days at
sixty years and 1.7 days across a whole cycle. Pick any of them and no
practitioner will ever notice.

**Savana matters enormously.** It lands about **315 days — ten months —** away at
sixty years. It is a real minority tradition rather than a mistake, and some
Tamil software offers it, but it is not what almanacs print. If your app suddenly
disagrees with a panchangam by most of a year, this is the first thing to check.

The default is the classical 365¼: it is what the textbook worked examples you
will check against use, it is the figure Tamil software vendors name first, and
it sits within half a day of Jagannatha Hora even sixty years out.

The classical justification for using a *solar* year at all comes from Phala
Deepika: one dasha year is the Sun's return to the position it held at birth.

---

## Why accuracy matters more here than anywhere else

This is the part worth internalising.

A dasha date is the Moon's position inside its nakshatra, **scaled up by the
length of the whole period**. For a 20-year Venus mahadasha:

```
20 years × 365.25 days ÷ 13°20′  =  548 days of dasha date per degree of Moon
```

So:

| Error in the Moon | Error in a printed dasha date |
|---|---|
| 1 arcsecond | **3.7 hours** |
| 1 arcminute | 9 days |
| 0.1° (a sloppy ayanamsa) | 55 days |

Nothing else in this engine amplifies an input error by three orders of
magnitude. It is why the Phase 0 accuracy work was worth doing, and the factor is
pinned by a test (`test_dasha_dates_amplify_moon_error`) so it cannot quietly
drift.

Two practical consequences:

- **Birth time matters more for dasha than for the chart.** The Moon moves about
  0.55° per hour, so one hour of doubt in the birth time moves a Saturn balance
  by roughly **nine months**. An AM/PM slip is catastrophic here.
- **Ayanamsa mismatch, not year length, is the realistic cause of disagreement**
  with another program. Check that first. See [ayanamsa.md](ayanamsa.md).

---

## Cross-checking against another program

If our dasha dates differ from Jagannatha Hora or a Tamil site, work down this
list in order:

1. **Ayanamsa.** Both must be on Lahiri (or both on KP). A different ayanamsa
   moves the Moon and therefore the balance. *Biggest single cause.*
2. **Birth time and timezone.** Confirm the AM/PM reading, the offset actually
   applied, and any DST warning the app showed. An hour is months of balance.
3. **Year length.** If you are out by roughly ten months, the other program is on
   savana 360. If you are out by a day or less, it is one of the solar variants
   and neither of you is wrong.
4. **Date truncation.** Some programs compute the balance from whole *dates*,
   discarding the time of day, which can shift a printed balance by a day. We
   keep full precision.
5. **The Moon itself.** Compare the Moon's longitude to the arcsecond before
   comparing dates. If the Moons differ, the dates were never going to agree —
   and 548 days per degree tells you exactly how much difference to expect.

---

## Try it

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1 --dasha
```

Then find your own birth star and its lord, and check the balance by hand:

```
balance years = (1 − fraction of the star already crossed) × the lord's years
```

If that matches what the app prints, you have understood the whole system.

---

**Next:** [03-panchangam.md](03-panchangam.md) — the daily almanac: tithi,
natchathiram, yogam, karanam, rahu kalam and nalla neram.
