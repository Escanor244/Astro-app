# பாவகங்கள் — bhava, karaka, maraka and badhaka sources

Companion to [drishti-sources.md](drishti-sources.md), and written for the same
purpose: **so an astrologer can check these tables offline without reading
code.**

Audited 11 August 2026 · 8 agents · every table independently re-sourced by a
challenger who was asked specifically to flag any Tamil term the researcher
*reconstructed* rather than found.

> **Why the tables get audited before the code now.** Bhava names, karakas and
> lordships are pure lookup — no arithmetic, so a wrong entry never fails a test,
> it just prints the wrong word forever. Two Tamil transcription errors have
> already been caught in this project (தைதுளை for தைதுலை; நாமாட்சரம் where Tamil
> sources say பெயர் எழுத்து), and a drishti rule shipped on one snippet had to be
> retracted. This audit ran first.

---

## 1. Two Tamil registers, and they do not cross

The single most useful finding.

| To name a house by… | Tamil uses | Example |
|---|---|---|
| its **meaning** | *name* + **ஸ்தானம்** | தன ஸ்தானம், லாப ஸ்தானம் |
| its **number** | ordinal + **பாவகம்** / **வீடு** / **இடம்** | இரண்டாம் பாவகம், 6ம் வீடு |

**No Tamil source was found writing a meaning-name with பாவம்.** "தன பாவம்" is
fluent-looking Tamil that nobody writes. The engine generates the ஸ்தானம் form
for names and `2ஆம் பாவகம்` for numbers, and never crosses them.

Note **பாவகம்**, not only பாவம் — four sources use பாவகம் as their default word
for the house-slot. Pan-Indian material only ever says *bhāva*.

---

## 2. The twelve bhavas

| # | Tamil | Romanised | English | Also called |
|---|---|---|---|---|
| 1 | **லக்னம்** | Lagnam | Ascendant | இலக்கினம், உயிர் ஸ்தானம் |
| 2 | **தன ஸ்தானம்** | Thana sthaanam | Wealth, family, speech | வாக்கு ஸ்தானம், குடும்ப ஸ்தானம் |
| 3 | **சகோதர ஸ்தானம்** | Sagothara sthaanam | Younger siblings, courage | தைரிய ஸ்தானம், வீரிய ஸ்தானம் |
| 4 | **சுக ஸ்தானம்** | Suga sthaanam | Mother, home, comfort | மாத்ரு ஸ்தானம் |
| 5 | **புத்திர ஸ்தானம்** | Puththira sthaanam | Children, past merit | பூர்வ புண்ணிய ஸ்தானம் |
| 6 | **ரோக ஸ்தானம்** | Roga sthaanam | Disease, enemies, debt | சத்ரு ஸ்தானம், ருண ஸ்தானம் |
| 7 | **களத்திர ஸ்தானம்** | Kalaththira sthaanam | Spouse, partnership | காம ஸ்தானம் |
| 8 | **ஆயுள் ஸ்தானம்** | Aayul sthaanam | Longevity, death | அஷ்டம ஸ்தானம் |
| 9 | **பாக்கிய ஸ்தானம்** | Paakkiya sthaanam | Fortune, father, dharma | பிதுர் ஸ்தானம் |
| 10 | **கர்ம ஸ்தானம்** | Karma sthaanam | Profession, status | ஜீவன ஸ்தானம், தொழில் ஸ்தானம் |
| 11 | **லாப ஸ்தானம்** | Laaba sthaanam | Gains, income | இலாப ஸ்தானம் |
| 12 | **விரய ஸ்தானம்** | Viraya sthaanam | Loss, expenditure, moksha | விரைய ஸ்தானம், மோட்ச ஸ்தானம் |

**ஆயுள், not ஆயுஷ்.** Tamil sources use the native form, not the grantha one.

### Groups

| Group | Tamil | Houses | Confidence |
|---|---|---|---|
| Kendra | **கேந்திரம்** | 1, 4, 7, 10 | Settled |
| Trikona | **திரிகோணம்** | 1, 5, 9 | Settled |
| Upachaya | **உபசய ஸ்தானம்** | 3, 6, 10, 11 | Group settled; spelling splits with உபஜெய |
| Dusthana | **மறைவு ஸ்தானம்** | **6, 8, 12** *(disputed)* | Term settled; membership disputed |

**மறைவு ஸ்தானம்** is the native Tamil term and dominates; துர்ஸ்தானம் occurs but
is less common.

> **Question for the astrologer:** is the **3rd** a மறைவு ஸ்தானம்? Some Tamil
> sources include it, others give only 6, 8 and 12. The engine takes the narrow
> set, since the 3rd is also an உபசயம் and counting it simply malefic
> contradicts that.

---

## 3. Karakas — **Settled, and grantha-free**

Every one of these was found verbatim in a Tamil source, and the whole set uses
no ஸ, ஷ, ஜ or ஹ — which is a good sign it is the almanac register.

| Graha | Karaka | Signifies |
|---|---|---|
| சூரியன் | **பிதுர் காரகன்** | father |
| சந்திரன் | **தாய் காரகன்** · **மனோ காரகன்** | mother · the mind |
| செவ்வாய் | **சகோதர காரகன்** · **பூமி காரகன்** | siblings · land |
| புதன் | **புத்தி காரகன்** · **கல்வி காரகன்** · **வாக்கு காரகன்** | intellect · education · speech |
| குரு | **புத்திர காரகன்** · **தன காரகன்** · **குடும்ப காரகன்** | children · wealth · family |
| சுக்கிரன் | **களத்திர காரகன்** · **வாகன காரகன்** | spouse · vehicles |
| சனி | **ஆயுள் காரகன்** · **கர்ம காரகன்** | longevity · profession |
| ராகு | **போக காரகன்** · **பாட்டன் காரகன்** | indulgence · paternal grandfather |
| கேது | **ஞான காரகன்** | wisdom |

Spelling checks worth recording, because these are where a slip hides:

- **களத்திர** has the retroflex ள *and* doubled த்த. Not களத்ர, not களதிர.
- **பிதுர்** puts the vowel on the second syllable — distinct from பித்ரு.
- **ஞான** is one syllable shorter than PyJHora's ஞானி, and a different word.

### On the father and mother karakas

Sources genuinely split on whether the Sun or Jupiter is the father-karaka, and
whether the Moon or Venus is the mother-karaka. Tamil sources give **சூரியன் =
பிதுர்** and **சந்திரன் = தாய்**, and that is what the engine uses.

**A correction to my own reasoning:** I first recorded மாத்ரு காரகன் as
unattested. It *is* attested — sitharsastrology.com prints
*"ஜோதிடப்படி மாத்ரு காரகன் சந்திரன்."* The decision to ship **தாய் காரகன்** is
still right, but for the register reason (native over Sanskritised, as with
வளர்பிறை over சுக்ல பக்ஷம்), **not** because the other form is an error. Filing a
real word as a transcription error teaches the wrong lesson.

---

## 4. Badhaka — **Verified two ways**

**பாதக ஸ்தானம்** depends only on the lagna's modality:

| Lagna modality | Tamil | Badhaka house |
|---|---|---|
| Movable — மேஷம், கடகம், துலாம், மகரம் | சர ராசி | **11th** |
| Fixed — ரிஷபம், சிம்மம், விருச்சிகம், கும்பம் | ஸ்திர ராசி | **9th** |
| Dual — மிதுனம், கன்னி, தனுசு, மீனம் | உபய ராசி | **7th** |

Transposing 11/9/7 would be silent — every lagna still gets *a* badhaka. So it
was checked a second way, by the resulting **signs**, which the classical text
names outright for movable lagnas: Mesham→Kumbam, Kadagam→Rishabam,
Thulam→Simmam, Magaram→Viruchigam. The engine has a test on exactly that.

**பாதகாதிபதி** is the lord of that house (35 attestations). Note the defective
**பாதகதிபதி**, missing the ா, appears in a subheading *on a page whose body uses
the correct form* — do not copy it.

---

## 5. Maraka — **one open question**

The engine uses the **2nd and 7th** for every lagna, which is what the classical
rule gives and what every source states as the general case.

> **Question for the astrologer, and the biggest open item in this document.**
> One researcher found three Tamil sources making maraka **modality-dependent**
> like badhaka — movable 2/7, fixed 3/8, dual 7/11. If that is what Tamil
> practice uses, the engine is wrong for **eight of the twelve lagnas**. It did
> not survive re-check, so the universal 2/7 stands for now. This is the one
> place where a wrong answer would be substantive rather than cosmetic.

**மாரகாதிபதி** is solid (48 attestations, including URL slugs and page titles).
**மாரகர் is not attested** in that form — Tamil prints **மாரகன்** (singular) or
**மாரகர்கள்** (plural). Also **பாதகம்** and **மாரகம்** appear only in oblique
forms (பாதகமான, பாதகத்தை), never as bare citation forms.

**ஸ்தானம் and ஸ்திர keep the grantha ஸ.** Unlike அஸ்வினி/அசுவினி there is no
competing native spelling in actual use, so the almanac-Tamil rule does not bite.

---

## 6. Reading from the Moon — **the calque was an invention**

**சந்திர லக்னம் is not Tamil.** Zero hits across 99 deduplicated Tamil pages, for
சந்திர லக்ன, சந்திரலக்ன, சந்திர லக்கின and சந்திரலக்கின. It is the obvious
translation of "Chandra lagna" and nobody writes it.

What Tamil actually says:

| Concept | Tamil | Note |
|---|---|---|
| The Moon-based reading pass | **ராசிப்படி** | Always adverbial, never stands alone |
| The lagna-based pass | **லக்னப்படி** | Its counterpart |
| The Moon's sign | **சந்திர ராசி** · **ஜென்ம ராசி** | ஜென்ம ராசி dominates ஜெனன ராசி 12:1 |
| Nth house from the Moon | **ராசிக்கு …ஆம் இடம்** | |
| Everyday proof Tamil counts from the Moon | **சந்திராஷ்டமம்** | The 8th from the Moon |

The engine names the two passes `லக்னப்படி` and `ராசிப்படி`, and a test asserts
that சந்திர லக்னம் never appears.

---

## 7. வர்க்கோத்தமம் — not yet implemented

Attested in four Tamil sources; the single-க **வர்கோத்தமம்** is a genuine rival,
not a typo, and appears in five more. Ship the doubled form — Adityaguruji
derives it: வர்க்கம் + உத்தமம் → வர்க்கோத்தமம்.

**நீச வர்க்கோத்தமம்** (debilitated yet vargottama, holding its strength anyway)
is attested. Tamil prices vargottama against **ஆட்சி பலம்**, own-sign strength.

Scheduled next, alongside the drishti-dependent doshas.

---

## 8. What we could not verify

- **No printed Tamil textbook.** Everything Tamil here is a web source. Same gap
  as the drishti audit, and the same recommendation: **ஜாதக அலங்காரம்** (கீரனூர்
  நடராஜன்) is the book most likely to settle several of these.
- **The maraka modality question (§5)** — the most consequential open item.
- **Whether the 3rd is a மறைவு ஸ்தானம்** (§2).
- Whether Tamil practice uses **Jaimini chara karakas** at all. A Tamil source
  (karthicknayakastro, 2018) does give the full set with Tamil names, so the
  earlier "not used in Tamil" reading was too strong. Not implemented either
  way; it needs its own audit before it would be.

---

*Corrections welcome and expected. Record them against the section number.*
