# Ayanamsa — the four choices, and which one to use

*Written from zero. If you only read one line: **use Lahiri**, unless you are
doing KP work, in which case use KP.*

---

## 1. What ayanamsa actually is

Western and Vedic astrology both cut the sky into twelve 30° signs. They
disagree about **where the circle starts**.

- **Western (tropical)** starts at the March equinox — the point where the Sun
  crosses the celestial equator going north. That is defined by Earth's
  *seasons*.
- **Vedic (sidereal)** starts at a fixed point among the *stars*.

Those two starting points coincided about 1,700 years ago. They no longer do,
because Earth's axis wobbles like a slowing top — a 25,772-year cycle called
**precession of the equinoxes**. The equinox drifts backwards through the
constellations at roughly 50.3 arcseconds a year.

**Ayanamsa is the size of that gap.** Today it is about **24°13′**.

```
sidereal longitude  =  tropical longitude  −  ayanamsa
```

The word is Sanskrit: *ayana* (movement, or solstice) + *amsa* (portion). In
Tamil you will see it as **அயனாம்சம்**.

That single subtraction is why you are "a Leo" in a Western app and கடகம்
(Cancer) in this one. Neither is wrong. They are measuring from different
origins.

## 2. Why there is more than one

Everyone agrees on the *idea*: ayanamsa is the distance from the equinox to the
start of the sidereal zodiac. Everyone disagrees on **exactly where the sidereal
zodiac starts**, because the sky does not come with a painted line on it.

Different astronomers anchored it differently — usually to a bright star, or to
a value fixed at a particular date. Each choice gives a slightly different
number, and the differences persist forever.

The four this app supports:

| System | Value on 1 Jan 2025 | Difference from Lahiri |
|---|---|---|
| **Lahiri** (Chitrapaksha) | 24°12′23″ | — |
| **True Chitrapaksha** | 24°11′20″ | −1′03″ |
| **KP** (Krishnamurti) | 24°06′34″ | −5′49″ |
| **Raman** | 22°45′36″ | −1°26′47″ |

## 3. How much does the choice actually change?

This is the question that matters, and the honest answer is: **usually very
little, occasionally everything.**

An ayanamsa difference shifts *every* graha by the *same* amount. It never
changes the relationships between planets — aspects, conjunctions and yogas
survive untouched. What it can change is which **rasi**, **nakshatra** or
**pada** a graha falls into, and only when that graha already sits near a
boundary.

The relevant boundary sizes:

| Division | Width | A 5′49″ shift is… |
|---|---|---|
| Rasi (sign) | 30° | 0.3% of it |
| Nakshatra | 13°20′ | 0.7% |
| **Pada** | **3°20′** | **2.9%** |

So switching Lahiri → KP moves a graha across a pada boundary roughly 3% of the
time. Switching Lahiri → **Raman** shifts by 1°26′ — that crosses a pada
boundary about **43%** of the time, and a whole rasi about 5% of the time. Raman
is not a small adjustment.

**Try it yourself.** Cast a chart, then change only the ayanamsa:

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1 --ayanamsa kp
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1 --ayanamsa raman
```

Every longitude moves by exactly the same amount. Watch which padas survive it.

---

## 4. The four systems

### Lahiri (Chitrapaksha) — **the default, and what you should use**

Named after **N. C. Lahiri**, who sat on the Indian government's Calendar Reform
Committee. In **1955** that committee adopted it as India's **official**
ayanamsa, and it has been the national standard ever since.

It anchors the sidereal zodiac so that the star **Chitra** (Spica, α Virginis)
sits at **180°** — the exact opposite of the zodiac's start. *Chitrapaksha*
means "the Chitra side". The value is fixed at a reference epoch and then
carried forward by the accumulated precession.

**Use it when:** almost always. It is the default in this app.

- Every Indian panchangam and government almanac uses it.
- AstroSage, Clickastro, ProKerala, Jagannatha Hora all default to it.
- If you compare a chart against an online Tamil source, that source is
  overwhelmingly likely to be using Lahiri.
- All classical Parashari technique — vargas, dashas, yogas — is taught against
  it in modern practice.

**Choose this unless you have a specific reason not to.**

### True Chitrapaksha — the purist's version

Same idea as Lahiri, computed differently. Rather than fixing a value at an
epoch and adding precession, it **recomputes Spica's actual position every
time** and places the zodiac 180° from wherever the star truly is.

That sounds like it should give the same answer, and nearly does — they differ
by about **1 arcminute** today. The gap exists because Spica has **proper
motion**: it is genuinely drifting across the sky, and the fixed-epoch
formulation cannot follow it.

Which is "right" depends on what you think the definition means. If the
tradition intends *the star itself* as the anchor, True Chitrapaksha is more
faithful. If it intends *the number the committee adopted*, Lahiri is.

**Use it when:** you specifically want the star-tracking definition, or you are
reproducing work by someone who used it. A 1′ difference will change a pada
about 0.5% of the time.

### KP (Krishnamurti) — **mandatory for KP work, wrong for everything else**

**K. S. Krishnamurti** was a Tamil astrologer from Chennai who built an entire
predictive system — Krishnamurti Paddhati — in the 1950s and 60s. He derived his
own ayanamsa for it, about **5′49″ less than Lahiri**.

This one is not a matter of taste. **KP technique only works with KP ayanamsa.**

Here is why. KP does not predict from sign placement; it subdivides each
nakshatra into unequal **sub-lords** using the Vimshottari proportions, giving
**249 divisions** of the zodiac. The smallest of those subs is under 15
arcminutes wide.

A 5′49″ error is **more than a third** of the smallest sub. Run KP on Lahiri and
a large fraction of your sub-lords are simply the wrong planet — while the chart
still looks completely normal, because the rasis and even most nakshatras are
unchanged. This is one of the most common silent errors in consumer astrology
software.

**Use it when:** doing anything KP — sub-lords, ruling planets, cuspal
significators, horary (prashna). **Never** mix it with Parashari work.

*(KP is Phase 3 of this project. `docs/04-kp-system.md` will teach it from
zero.)*

### Raman — B. V. Raman's value

**B. V. Raman** (1912–1998) was one of the most influential astrologers of the
20th century, and his *Hindu Predictive Astrology* is still a standard text. He
used an ayanamsa about **1°26′ lower** than Lahiri.

That is a big difference — nearly a full pada and a half. Charts cast in Raman
differ visibly from Lahiri charts.

**Use it when:** you are working through Raman's books and want your charts to
match his worked examples, or following a lineage that teaches his value. It is
a minority position in modern practice.

---

## 5. How to choose

```
Are you doing KP — sub-lords, ruling planets, horary?
    └─ yes → KP
    └─ no  → Are you reproducing B. V. Raman's published examples?
                 └─ yes → Raman
                 └─ no  → Do you specifically want the star-tracking definition?
                              └─ yes → True Chitrapaksha
                              └─ no  → Lahiri     ← this is you
```

**The rule that matters more than the choice: be consistent.** Never compare two
charts computed with different ayanamsas, and never mix a Parashari reading with
a KP one. If a chart here disagrees with another program, the ayanamsa setting
is the *first* thing to check — before suspecting a bug.

## 6. Accuracy, and why you can trust the number

Ayanamsa is the single most consequential value in the engine, because it
applies to *every* graha equally. An error here moves the entire chart.

This app computes all four independently and validates them against Swiss
Ephemeris, an unrelated implementation:

| System | Worst disagreement |
|---|---|
| Lahiri | **0.004 arcsec** |
| KP | 0.004 arcsec |
| Raman | 0.004 arcsec |
| True Chitrapaksha | 0.27 arcsec |

For scale: a pada is 12,000 arcseconds. A 0.004″ disagreement is one part in
three million of a pada.

There is a structural difference worth knowing, and the test suite asserts it:
Lahiri, KP and Raman are **fixed-epoch** systems — each pins a value at 1900 and
adds accumulated precession, so they differ only by a constant and their
increments over any interval are identical. True Chitrapaksha is **dynamic**: it
follows a real star, and Spica's proper motion makes its rate measurably
different.

## 7. Common questions

**Does changing ayanamsa change my Sun sign?**
Only if your Sun was already within the shift of a boundary. Lahiri → KP moves
everything 5′49″; Lahiri → Raman moves it 1°26′.

**Does it change aspects, conjunctions or yogas?**
No. Every graha moves by the same amount, so the angles between them are
untouched. Only placements relative to *fixed* divisions — rasi, nakshatra, pada,
bhava — can change.

**Does it affect dasha periods?**
Yes, indirectly and sometimes substantially. Vimshottari dasha is calculated
from the Moon's exact position within its nakshatra. Shifting the Moon shifts
that fraction, which shifts your dasha balance at birth — and therefore every
period start date for the rest of the chart.

**Why does my chart differ from another website?**
In order of likelihood: (1) different ayanamsa, (2) mean vs true lunar node —
this app uses **mean**, as KP and most Vedic practice do, (3) a timezone or
daylight-saving difference, (4) an AM/PM slip. See
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Which do professional Tamil astrologers use?**
Lahiri for Parashari work, KP ayanamsa for KP work. Many practise both and
switch deliberately depending on the question.

**Is one of them "true"?**
No. They are different conventions for locating a line that nature did not draw.
Each is internally consistent; a tradition's results are calibrated against the
ayanamsa it was developed with. That is the real argument for consistency —
technique and ayanamsa are a matched pair.

---

## Where this lives in the code

- `services/jyotish/jyotish/core/ayanamsa.py` — all four, with the defining
  constants and the reasoning in the docstrings.
- `services/jyotish/tests/validation/test_ayanamsa_vs_swisseph.py` — the
  accuracy gate quoted above.
- CLI: `--ayanamsa {lahiri,true_chitrapaksha,kp,raman}`
- API: `"ayanamsa"` in the `/api/chart` request body.
- Web: the **Ayanamsa** selector, with the short version behind its ⓘ button.

Next in the learning path: [00-orientation.md](00-orientation.md) if you have
not read it, and `04-kp-system.md` when Phase 3 lands.
