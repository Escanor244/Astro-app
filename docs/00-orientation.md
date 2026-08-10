# 00 — Orientation: what makes this Vedic

*First doc in the learning path. Assumes no prior Jyotish knowledge.*

---

## The one difference that causes all the others

Western and Vedic astrology both divide a circle into twelve 30° signs. They
disagree about **where the circle starts**.

- **Western (tropical)** starts the zodiac at the March equinox — the point
  where the Sun crosses the celestial equator going north. This is defined by
  Earth's *seasons*.
- **Vedic (sidereal)** starts the zodiac at a fixed point against the *stars*.

Those two starting points used to coincide, roughly 1,700 years ago. They no
longer do, because Earth's axis wobbles like a spinning top — a 25,772-year
cycle called **precession of the equinoxes**. The equinox drifts backward
through the constellations at about 50.3 arcseconds per year.

Today the gap is about **24°13′**. That is most of a whole sign.

This is why someone is "a Leo" in a Western app and Kadagam (Cancer) in a Vedic
one. Neither is a mistake; they are measuring from different origins.

## Ayanamsa — the number that bridges them

**Ayanamsa** (*ayana* = solstice/movement, *amsa* = portion) is that gap.

```
sidereal longitude = tropical longitude − ayanamsa
```

That is the single most consequential number in this engine. It applies to
*every* graha equally, so an error moves the entire chart rigidly.

How much precision matters? A **pada** (quarter of a nakshatra) is 3°20′. An
ayanamsa error of 0.3° will push grahas across pada boundaries near the edges.
Our engine agrees with the reference implementation to **0.004 arcseconds**,
which is roughly one part in three million of a pada.

### Why there are several ayanamsas

Everyone agrees on the *concept* and disagrees on the *anchor point*. We support
four, in `jyotish/core/ayanamsa.py`:

| System | Anchor | Use it for |
|---|---|---|
| **Lahiri** (Chitrapaksha) | India's official standard, fixed by the Calendar Reform Committee in 1955 | Default. All Parashari work, everything a consumer sees |
| **True Chitrapaksha** | Spica (Chitra) held exactly at 180°, recomputed dynamically | Purists who want the star itself as the anchor |
| **KP** (Krishnamurti) | K.S. Krishnamurti's own value, ~5′49″ less than Lahiri | **Mandatory** for KP work |
| **Raman** | B.V. Raman's value, ~1°12′ less than Lahiri | Following Raman's published work |

That KP row matters more than it looks. Running KP analysis on Lahiri ayanamsa
shifts every cusp by nearly six arcminutes, which silently corrupts sub-lord
results — and sub-lords are the entire point of KP. This is a common bug in
consumer apps.

**→ [ayanamsa.md](ayanamsa.md) is the full guide**: what each of the four
systems is, how much the choice actually changes, and which to pick. Worth
reading before you cast charts you intend to compare against anything else.

There is a structural difference worth noticing: Lahiri, KP and Raman are
**fixed-epoch** systems. Each pins a value at 1900 and adds accumulated
precession, so they differ only by a constant. True Chitrapaksha is **dynamic** —
it tracks a real star, and Spica has proper motion, so its rate differs slightly.
The test suite asserts exactly this.

## The vocabulary

Vedic astrology is Sanskrit-and-Tamil, not Greek. There are no "fire signs" or
"elements" in the Western sense.

| Concept | Sanskrit | Tamil | What it is |
|---|---|---|---|
| Planet | graha | கிரகம் | The nine "seizers" — Sun through Saturn, plus Rahu and Ketu |
| Sign | rasi | ராசி | One of twelve 30° divisions |
| Lunar mansion | nakshatra | நட்சத்திரம் | One of **27** divisions of 13°20′ each |
| Quarter | pada | பாதம் | A quarter of a nakshatra, 3°20′ |
| House | bhava | பாவம் | One of twelve life areas, counted from the lagna |
| Ascendant | lagna | லக்னம் | The rasi rising on the eastern horizon at birth |

### Nine grahas, not ten planets

| # | English | Tamil | Note |
|---|---|---|---|
| 1 | Sun | சூரியன் (Suriyan) | |
| 2 | Moon | சந்திரன் (Chandran) | Far more central than in Western astrology |
| 3 | Mars | செவ்வாய் (Sevvai) | The "Sevvai dosham" planet |
| 4 | Mercury | புதன் (Budhan) | |
| 5 | Jupiter | குரு (Guru) | |
| 6 | Venus | சுக்கிரன் (Sukkiran) | |
| 7 | Saturn | சனி (Sani) | |
| 8 | Rahu | ராகு (Raagu) | North lunar node — a point, not a body |
| 9 | Ketu | கேது (Kethu) | South node, always exactly opposite Rahu |

**Uranus, Neptune and Pluto are not used.** They were invented after the
classical texts, and the rule systems make no reference to them.

**Rahu and Ketu are not objects.** They are the two points where the Moon's
orbit crosses the ecliptic — where eclipses happen. That is why they are always
180° apart and always move backwards (retrograde). Our engine computes Rahu from
a published formula and *defines* Ketu as Rahu + 180°, rather than computing it
separately, because that is what it means.

## The 27 nakshatras

The nakshatras are arguably more important than the rasis in South Indian
practice. Your **birth star** (ஜென்ம நட்சத்திரம்) is your Moon's nakshatra, and
it drives:

- your dasha sequence (which planetary period you were born into),
- **thirumana porutham** — Tamil marriage matching works primarily on
  nakshatra and rasi, not on the 36-guna system used in the north,
- the naming syllable traditionally given to a child.

27 nakshatras × 4 padas = 108 divisions. Both 27 and 108 are exact divisors of
the circle, so our code derives them by division rather than by table lookup —
that is what makes pada assignment boundary-safe.

## The South Indian square chart

The chart you grew up seeing is a 4×4 grid with a hollow centre — and it works
in the opposite way to the North Indian diamond.

```
+----------+----------+----------+----------+
| Meenam   | Mesham   | Rishabam | Mithunam |
+----------+----------+----------+----------+
| Kumbam   |                     | Kadagam  |
+----------+                     +----------+
| Magaram  |                     | Simmam   |
+----------+----------+----------+----------+
| Dhanusu  | Viruchigam| Thulam  | Kanni    |
+----------+----------+----------+----------+
```

- **The rasis never move.** Mesham is always in that same cell, in every chart
  ever drawn.
- **The houses rotate.** Whichever cell holds the lagna becomes house 1, and you
  count clockwise from there.

The North Indian chart does the reverse: houses fixed, signs move. Same
information, opposite convention — and a frequent source of confusion when
reading books written for the other tradition.

Because houses are whole rasis here, the South Indian chart *is* the whole-sign
house system, drawn directly. This is why `ChartPositions.house_of()` is simply
`(graha_rasi − lagna_rasi) mod 12 + 1`.

## What comes next

**[02-dasha.md](02-dasha.md)** is the astrology of *when*: your birth star does
not only name you, it starts a 120-year sequence of planetary periods that runs
for life. That is the technique a Tamil consultation actually spends its time on.

**[03-panchangam.md](03-panchangam.md)** is the daily almanac — tithi,
natchathiram, yogam, karanam, rahu kalam and நல்ல நேரம் — and the Tamil
calendar date.

Then **KP (Krishnamurti Paddhati)** — a Tamil system, created in Chennai, that
subdivides each nakshatra by those same Vimshottari proportions to get 249
"subs", and predicts from cuspal sub-lords rather than from sign placement. It is
the most precise branch of Jyotish, it is badly served by existing apps, and
`docs/04-kp-system.md` will teach it from zero.

Notice that the dasha proportions and the KP subs are the *same* nine numbers.
Learning [02-dasha.md](02-dasha.md) properly is most of the way to understanding
KP.

---

**Try it:** cast your own chart and find your birth star. (Activate the venv
first — see the [README](../README.md#quick-start).)

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1
```

Your birth star is the Moon's nakshatra. Tamil place names work too, so
`--place "மதுரை"` is a valid way to enter Madurai.

Then run the same chart with `--ayanamsa kp` and watch every longitude shift by
the same ~5′49″. That is ayanamsa, made visible.
