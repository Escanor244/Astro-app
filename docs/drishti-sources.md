# கிரக பார்வை — sources and verification

**A document to check with an astrologer, not a code comment.** Every rule the
engine applies for planetary aspects is listed here with the sources behind it,
quoted, so a practising Tamil astrologer can confirm or correct it without
reading any code.

Audited 10–11 August 2026 · 62 research and challenge agents · every claim
re-sourced by an independent challenger who had to *locate the quoted text*.

> **Why this document exists.** The engine originally shipped the claim *"ராகு
> and கேது have no பார்வை in Tamil practice"* on the strength of a single web
> search snippet. The user challenged it. It turned out to be one of at least
> five live positions, not a settled fact. This document is the correction, and
> the standard the project now holds itself to: **contested things are labelled
> contested.**

---

## How to read the confidence ratings

| Rating | Means |
|---|---|
| **Settled** | Multiple independent classical texts agree, and no credible source dissents |
| **Well supported** | Good sources agree, but there is a gap — one translator, or no Tamil printed source |
| **Contested** | Real practitioners genuinely disagree. The engine picks a default and says so |
| **Unverified** | We looked and could not confirm. Listed openly at the end |

A **source ranking** is applied throughout: a named translation of a classical
text outranks a modern authority, which outranks a Tamil website, which outranks
an unattributed page. Pages that copy one another are counted **once** — several
were caught doing exactly that.

---

## 1. Every graha aspects the 7th — **Settled**

**The rule:** every graha casts a full aspect on the 7th place from itself.
Counting is *inclusive* — the graha's own rasi is the 1st, so the 7th is five
signs further on. The 7th aspect is **mutual**: if A looks at B, B looks back.

Four textually independent Sanskrit works state it:

> **Brihat Parashara Hora Shastra 26.2–5** (tr. R. Santhanam, Ranjan
> Publications, 1984, Vol. I pp. 254–255):
> *"…All planets aspect the 7th fully. Saturn, Jupiter and Mars have special
> aspects respectively on 3rd and 10th, 5th and 9th, and 4th and 8th."*

> **Brihat Jataka 2.13** (Varāhamihira; tr. N. Chidambaram Iyer, Thompson & Co.,
> Madras, 1905, p. 13):
> *"All the planets aspect the 3rd and 10th houses with a quarter sight; the 5th
> and 9th houses with half a sight, the 4th and 8th houses with three-quarters
> of a sight, and the 7th house with a full sight…"*
>
> Sanskrit: *tridaśatrikoṇacaturasrasaptamānyavalokayanti caraṇābhivṛddhitaḥ |
> ravijāmarejyarudhirāḥ pare ca ye kramaśo bhavanti kila vīkṣaṇe adhikāḥ ||*

> **Saravali 4.32–33** (Kalyāṇa Varma; tr. R. Santhanam) — same rule.
> **Jataka Parijata II.30–31** (Vaidyanātha Dīkṣita; tr. V. Subrahmanya Sastri,
> 1932) — same rule.

**Caveat on independence.** R. Santhanam translated *both* the BPHS and the
Saravali passages quoted. The underlying Sanskrit works are independent; those
two English renderings share a hand. Brihat Jataka is quoted from a different
translator *and* with its Sanskrit, which is why the word order can be checked.

**No graha is excluded** from the 7th aspect by any text found.

---

## 2. The three special aspects — **Settled**

| Graha | Tamil | Also aspects |
|---|---|---|
| செவ்வாய் (Mars) | | the **4th and 8th** |
| குரு (Jupiter) | | the **5th and 9th** |
| சனி (Saturn) | | the **3rd and 10th** |

These are *additions* to the 7th, never replacements.

**The obvious way to get this wrong** is to swap Mars 4/8 with Saturn 3/10 —
they are mirror images, and a transcription error would be easy to inherit. It
was checked specifically: the Sanskrit of Brihat Jataka 2.13 locks the pairing
by word order plus **kramaśaḥ** ("respectively"), so the order is not a
translator's arrangement.

**No credible source gives the Sun, Moon, Mercury or Venus a special aspect.**
Every source checked gives them the 7th only.

### But "agreed by everyone" was too strong — corrected

The engine's docstring said the six special aspects are agreed by everyone. Their
*existence* is. Their being *full strength* is not:

> **Phaladeepika 4.9** (Mantreśvara — whom tradition places in **Tirunelveli**,
> which makes him a Tamil-country authority):
> *"The aspect from the 7th house is the only one that should be considered as
> most effective in all cases. But some learneds are of the view that the special
> aspects of Jupiter…, of Mars… and of Saturn… are equally competent…"*

Mantreśvara records the opposing camp rather than settling it. Corrected in the
code.

---

## 3. Graded aspects — the engine ships the exception without the rule

**This is the most important finding against the current implementation.**

The *same verse* that grants the three special aspects also grants **every**
graha a partial aspect everywhere else:

| From the graha | Strength | Virupas |
|---|---|---|
| 3rd and 10th | quarter (கால்) | 15 |
| 5th and 9th | half (அரை) | 30 |
| 4th and 8th | three-quarters (முக்கால்) | 45 |
| 7th | full (பூரண) | 60 |

The special aspects are defined as the *exception* to that scale — Saturn's 3rd
and 10th are promoted from ¼ to full, and so on. The engine implements the
exceptions and drops the scale.

**The texts disagree with each other about the middle of the scale.** BPHS,
Brihat Jataka and Jataka Parijata give 5/9 = ½ and 4/8 = ¾. **Saravali reverses
them**: 4/8 = ½ and 5/9 = ¾. Anyone implementing graded aspects has to choose.

### Is that a defect? **No — but the reasoning had to change**

Two findings, both well supported:

- **No Tamil source uses graded aspects in ordinary chart reading.** Searched
  extensively, including a Tamil page literally titled **திருஷ்டி பலம்** (aspect
  *strength*) which turns out to describe a presence/absence test.
- **Both reference implementations keep chart-level drishti binary** and put
  virupas in a separate shadbala module — PyJHora (the readable port of
  Jagannatha Hora) and jyotishganit both do this.

So binary full-aspect at rasi level is **faithful to Tamil practice**, and graded
drishti belongs later as *drik bala* inside shadbala. That is what the engine
does. What was wrong was the *justification* — the docstring called grading "a
strength refinement", when BPHS presents it as aspect doctrine and says the
effects "will also be proportionate". Corrected.

### One popular claim that is unsourced

Many sites assert Saturn's 3rd aspect is weaker than its 10th, or Mars's 4th
weaker than its 8th. **No classical text checked makes that distinction.** BPHS
applies the promotion symmetrically and both members of each pair reach 60
virupas. The sites asserting a difference cite no verse and contradict each other
about which one is stronger.

---

## 4. ராகு and கேது — **Contested. Five positions.**

**This is the section to take to an astrologer.** The engine must pick something,
because doshas and yogas consume it — but nothing here is settled.

| Position | Who holds it |
|---|---|
| **7th only** | Plain reading of BPHS ("all Grahas", and BPHS 3.10 counts nine grahas including the nodes); **Jagannatha Hora / PyJHora** implement exactly this; B.V. Raman implicitly — he states the rule without exception and writes "aspected by Rahu" in his own worked charts |
| **3rd, 7th and 11th** | **The most commonly printed Tamil answer** — three independent Tamil sources including *Daily Thanthi* |
| **No aspect at all** | The plurality on the Tamil web (நிழல் கிரகம் — a shadow has no light to cast a look with); Gopesh Kumar Ojha |
| **5th, 7th and 9th** (like Jupiter) | V.K. Choudhry (Systems Approach). **Not** classical — nobody quoting BPHS for this has ever produced a verse |
| **Asymmetric** | Sanjay Rath: Ketu none; Rahu the 7th, 5th/9th, *and* uniquely the 2nd |

### The strongest classical argument on each side

**For the nodes aspecting:** BPHS's aspect chapter says "All Grahas", and BPHS
3.10 itself counts nine grahas including Rahu and Ketu.

**Against:** BPHS Ch. 27 confines Shadbala — of which **Drik Bala**, aspectual
strength, is one of the six — to the seven grahas from Surya to Sani. The nodes
never appear in vv. 24–25, 32–33 or 34–36.

Neither text names the nodes in the aspect passage itself. The silence is real
and both readings have purchase.

### Two things being said about KP that are false

Since KP is a Chennai system and this project implements it in Phase 3, this
matters:

**K.S. Krishnamurti is not on any of the five positions.** KP replaces Parashari
drishti with *Western degree aspects*, and treats the nodes as **agents** of
their conjoined planet, aspecting planet, star lord and sign lord. The widely
repeated claim that *"KP teaches 5/7/9 for the nodes"* appears to be a
**fabrication circulating on AI-generated SEO pages** — no primary KP source
supports it.

### The split that matters in practice

**Doctrinal Tamil statements deny node drishti. Operational Tamil rules use it.**
Tamil செவ்வாய் தோஷம் cancellation rules do turn on Rahu/Ketu aspect. Meanwhile
BPHS's own node yoga rules (Ch. 34) speak only of the nodes *receiving* aspect,
never casting it.

A defensible position, which this project may adopt when doshas are built: **the
nodes receive aspect everywhere; they cast aspect only where a dosha rule
explicitly names them.**

### What the engine does

`NodeDrishti` is a setting, not a constant. Default **SEVENTH**, because it is
what Jagannatha Hora computes and the plain reading of the classical text — but
it is a default, not a finding. **THREE_SEVEN_ELEVEN** was added after this
audit, since it is the most common Tamil answer and the enum previously could not
express it. **NONE** and **FIVE_SEVEN_NINE** are also available.

> **Question for the astrologer:** in your practice, do ராகு and கேது cast
> பார்வை? If so, on which houses — 7 only, or 3/7/11? And does your answer change
> between reading a yoga and testing a dosham?

### A bug found in a third-party library

**jyotishganit** (installed here as a cross-check for divisional charts) gives
Rahu and Ketu `[5, 9]` — the 5th and 9th **with no 7th**. No school in this audit
teaches that; every camp that grants the nodes 5 and 9 keeps the 7th too. It
looks like a transcription slip. It does not affect AstroApp, which implements
drishti independently, but anyone cross-checking aspects against that library
will see a mismatch and should know why.

---

## 5. Whole-sign or degree-based? — **Well supported, with a real dissent**

The engine treats a graha as aspecting the **whole rasi**, not a degree.

**In favour:** every popular Tamil source states it in whole houses — *"தான்
இருக்கும் இடத்தில் இருந்து ஏழாவது வீட்டை பார்க்கும்"* — and both PyJHora and
jyotishganit compute interpretive drishti as pure integer rasi arithmetic.

**Against, and it was stated too confidently before:** BPHS Ch. 26 gives
*longitude* arithmetic for aspects and explicitly calls the house-only method the
**"ordinary"** one. So whole-sign is a defensible reading, not the only classical
reading.

**And one Tamil source dissents directly.** ஆதித்ய குருஜி holds that a full
aspect requires the two bodies within **15°** of exact; beyond 20° there is only
*"குறைந்த அளவு தொடர்பே"* even when the grahas sit in directly opposite rasis —
because *"there is no wall in the sky"* at a sign boundary. No Tamil source was
found defending strict whole-sign once that case is put to it; the popular
sources simply never raise it.

**Bhava chalit is moot here.** Tamil sources treat the rasi chakra as primary and
call predicting from a relocated bhava *"தவறான பலன்"*. But that settles *which
house*, not *how strongly it looks* — so it does not dissolve the degree
question.

> **Question for the astrologer:** if செவ்வாய் is at 29° of one rasi and a graha
> is at 1° of the opposite rasi — nominally a 7th aspect, but 32° apart — do you
> count that as a full பார்வை?

---

## 6. ராசி பார்வை (rasi drishti) — correctly **not** implemented

Rasi drishti is sign-aspects-sign: movable signs aspect the three fixed signs
except the adjacent one, fixed aspect the three movable except the adjacent one,
dual aspect the other three dual. Stated identically in **BPHS Ch. 8.1–3** and
**Jaimini Sutras 1.1.2–4**.

**A correction to something commonly said:** rasi drishti is *not* "Jaimini, not
Parashari". BPHS — the root Parashari text — gives it in Ch. 8, and then at
26.2–5 calls graha drishti *"the other kind"*. Parashara presents both.

**But it is absent from Tamil practice material.** Tamil pages on பார்வை teach
only the graha rule; **ராசி பார்வை does not function as a technical term** in
Tamil search; and the one apparently-Tamil BPHS Ch. 8 online turns out to be
Santhanam's English pasted under a Tamil heading. **Argala** (BPHS Ch. 31) has no
Tamil footprint at all.

Verdict: graha drishti only is right for this audience. Rasi drishti belongs in a
Jaimini module if one is ever built, at low priority, and must never be merged
into the graha drishti path.

---

## 7. Tamil terminology — **Well supported**

| English | Tamil | Note |
|---|---|---|
| Aspect | **பார்வை** | Settled. Every Tamil source uses it |
| Special aspect | **சிறப்புப் பார்வை** | Well attested |
| Mutual aspect | **சமசப்தம்** / சம சப்தம பார்வை | **Not** "பரஸ்பர பார்வை", which no source used |
| Full aspect | **பூரண பார்வை** | |

**Do not use திருஷ்டி for graha drishti in Tamil.** In Tamil, திருஷ்டி means the
*evil eye* — கண் திருஷ்டி. Tamil keeps the two words apart, and no Tamil source
found uses திருஷ்டி for planetary aspect.

**Does a printed Tamil jathagam show a drishti table?** No Tamil jathagam product
was found that prints one. This is strong-but-indirect: no actual printed
jathagam was inspected.

---

## 8. What we could NOT verify

Listed openly, because these are the questions to put to a practising astrologer.
**This section is as important as the rest of the document.**

1. **No printed Tamil textbook was read.** Every Tamil source cited here is a
   website, blog or forum answer. This is the most serious gap in a
   Tamil-practice audit. The book most likely to settle several of these is
   **ஜாதக அலங்காரம்** (கீரனூர் நடராஜன், 17th c., in print with செ.
   தேவசேனாதிபதி's commentary). Its verse on பார்வை could not be obtained.

2. **No clean Sanskrit of BPHS 26.2–5.** The archive.org Devanagari is OCR noise;
   sanskritdocuments.org lacks that chapter range. So for BPHS we rely on one
   translator. **This is load-bearing for the nodes**: whether the sloka reads
   *sarve grahāḥ* ("all grahas") or enumerates the seven decides whether BPHS's
   silence about Rahu and Ketu is inclusive or exclusive. Someone with a printed
   Sanskrit BPHS could settle it in five minutes.

3. **Jyotishtatwam** (S. Ganesan, Madras, 1927, p. 65) — the sole citation behind
   a competing *permuted* strength table. Could not obtain the book.

4. **No primary source for K.N. Rao** on node aspects; the report that he declines
   5/9 for the nodes is second-hand via a forum.

5. **Nothing found for C.S. Patel** on this question. Not guessed at.

6. **The Tamil BPHS translation** (Allur Venkatramaiyar, 2 vols) was not
   obtainable, and it almost certainly contains Ch. 8 and Ch. 26.

---

## 9. What the engine does today

Implemented in [`services/jyotish/jyotish/core/drishti.py`](../services/jyotish/jyotish/core/drishti.py),
tested in `services/jyotish/tests/test_drishti.py`.

| Rule | Status |
|---|---|
| Every graha aspects the 7th, inclusive counting | Settled — §1 |
| செவ்வாய் 4/8, குரு 5/9, சனி 3/10 | Settled — §2 |
| Sun, Moon, Mercury, Venus: 7th only | Settled — §2 |
| Whole-sign, not degree-based | Well supported, with dissent — §5 |
| Binary, not graded | Faithful to Tamil practice; grading deferred to shadbala — §3 |
| ராகு/கேது: `NodeDrishti`, default SEVENTH | **Contested — §4.** A default, not a finding |
| No rasi drishti | Correct for this audience — §6 |

---

## 10. Sources

**Classical texts and translations**
- Brihat Parashara Hora Shastra, tr. R. Santhanam, Ranjan Publications, 1984 — Ch. 8, Ch. 26, Ch. 27, Ch. 34
- Brihat Jataka (Varāhamihira), tr. N. Chidambaram Iyer, Thompson & Co., Madras, 1905 — 2.13; Sanskrit via wisdomlib (Neely ed., 2017)
- Saravali (Kalyāṇa Varma), tr. R. Santhanam — 4.32–33
- Jataka Parijata (Vaidyanātha Dīkṣita), tr. V. Subrahmanya Sastri, 1932 — II.30–31
- Phaladeepika (Mantreśvara) — 2.23, 4.9
- Jaimini Sutras — 1.1.2–4, 1.1.5–10

**Modern authorities**
- B.V. Raman; Sanjay Rath; V.K. Choudhry; Gopesh Kumar Ojha; K.S. Krishnamurti (*Readers*, esp. III); P.V.R. Narasimha Rao

**Software read as source**
- PyJHora — `src/jhora/const.py` line 532 (`graha_drishti`), `horoscope/chart/house.py`, `horoscope/chart/strength.py`
- jyotishganit 0.1.3 — `components/aspects.py` lines 13–23

**Tamil-language web sources**
- tamizhdb.com; vedajothidam.blogspot.com; Daily Thanthi (dailythanthi.com); Dinakaran; Astrosiva; ஆதித்ய குருஜி; ta.quora.com (ராம. சுப்ரமணியன்); HosurOnline

**Sources deliberately discounted** — yourastroguide.com and astroshastra.com present
near-identical phrasing and were counted as one lineage, not two witnesses.
Several pages asserting a KP position on node aspects show the marks of
AI-generated SEO content and were discarded.

---

*Corrections welcome and expected. If an astrologer disagrees with anything here,
that disagreement is more valuable than the entry it corrects — please record it
against the section number.*
