# செவ்வாய் தோஷம் — sources, and why this app gives no verdict

Third in the series with [drishti-sources.md](drishti-sources.md) and
[bhava-sources.md](bhava-sources.md), and the most consequential of the three:
this is the question a Tamil client asks most often, and the answer gets told to
someone about their marriage.

Audited 11 August 2026 · 8 agents · every answer independently re-sourced, and
each challenger additionally asked: **ship with a default, ship with a setting,
or do not ship until an astrologer decides?**

All four came back the same way.

---

## The decision: the app computes, it does not conclude

**There is no `present` flag, no percentage, and no sentence about marriage.**
The app reports where Mars is, which conventions flag that, and which exemptions
apply — each named and attributed. An astrologer weighs them.

This is not caution for its own sake. Three specific findings force it:

**1. Three incompatible Tamil house sets, all mainstream.**

| Set | Who |
|---|---|
| **{2, 4, 7, 8, 12}** | The plurality — Maalaimalar, arivomayiram, hosuronline, Sakthi Vikatan |
| **{1, 2, 4, 7, 8, 12}** | Dinakaran, which calls it **பாரம்பரிய முறை**, the traditional method |
| {1, 4, 7, 8, 12} | The classical Sanskrit verse — *lagne vyaye ca pātāle jāmitre cāṣṭame kuje* |

A chart with Mars in the lagna is clean under the first and flagged under the
second. Mars in the 2nd is the reverse. **Roughly a sixth of all charts change
status on this choice alone**, before a single cancellation rule runs.

**2. Four mutually incompatible cancellation stacks**, which disagree on ordinary
charts. Mars in Meenam in the 4th is cancelled under one and not another.

**3. The exception list does almost all the work.** A Tamil practitioner
(hosuronline) states that applying it takes **100 dosham-positives down to 3
survivors**.

Put together: a boolean would not be reporting the chart. It would be reporting
*the implementer's choice of exception list*, with the app's name on it. And a
setting does not fix that — a setting still ships a default, the default still
decides, and the user still reads a yes.

> One agent put it exactly right: *"Setting-ification is how a minority reading
> launders itself into a default."*

---

## Three things that overturn what is widely repeated

**The lagna reading is primary — not the Moon.** I went in assuming Tamil
practice weights the Moon heavily. The Tamil sources that actually rank the three
references put **லக்னம் first**, then the Moon, then Venus. The widely-quoted
"full from Lagna, ½ from Moon, ¼ from Venus" fractional scheme **failed to verify
at any reachable page** and is not implemented.

**Debilitation cancels.** *நீச்ச செவ்வாய்க்கு பலம் இல்லை* — a debilitated Mars
has no strength with which to do harm. So **Kadagam exempts for the same reason
Mesham and Magaram do**. This is the most counterintuitive rule here and the one
most likely to be implemented wrong; there is a test on it.

**Venus as a third reference is not a Tamil signature.** I had it noted as one.
It is used pan-Indially, including in Hindi sources. It is here because Tamil
sources use it — not because it distinguishes Tamil practice.

---

## What the app computes

| Layer | Status |
|---|---|
| Mars's house from **லக்னம்**, **ராசி** and **சுக்கிரன்** | Shipped. Every Tamil source agrees on the arithmetic |
| Which of the three conventions flag each reading | Shipped, side by side |
| Severity: **7 and 8 severe**, others moderate | Shipped as one tier — no Tamil source ranks the 7th against the 8th, so neither does this |
| Exemptions, each named and attributed | Shipped as line items |
| A yes/no answer | **Not shipped, and will not be** |

### The exemptions computed, and why only these four

| Exemption | Provenance |
|---|---|
| Mars in own, exalted **or debilitated** sign | Widely attested |
| Mars yogakaraka for the lagna (Kadagam, Simmam) | Attested (Sakthi Vikatan); a wider variant adds Mesham and Viruchigam |
| Jupiter conjunct or aspecting Mars | Attested in Tamil, in a broad three-limb form |
| Mars in Rishabam or Thulam (Venus's signs) | Attested (Maalaimalar), corroborated once |

**Deliberately not computed:** "Mars conjunct any malefic." One source gives it,
and it is so broad it would cancel most charts. An exemption that almost always
fires is not information. A test asserts that no shipped exemption fires on every
chart in a month-long sample.

---

## Gender

**The house test is genderless**, and the app treats it that way. K.P.
Vidyatharan states the rule with no gender at all.

The asymmetry Tamil practice does carry lives in **மாங்கல்ய தோஷம்** and in
பொருத்தம் matching — not in where Mars sits. That is a Phase 4 question.

---

## கால சர்ப்ப தோஷம் — researched, not yet built

Findings recorded now so they are not re-litigated:

- **Both directions are கால சர்ப்ப தோஷம் in Tamil practice**, labelled
  **சவ்ய** (Rahu-first) and **அபசவ்ய** (Ketu-first). The clean
  dosham/Kala-Amrita split is one author's minority position and could not be
  confirmed from any substantive Tamil source. *(Corrected: this is a
  majority/minority split, not a Tamil/North Indian one.)*
- Tamil states it in **rasis** — seven occupied, five empty — not in degrees.
  Degree mode has zero Tamil attestation.
- **Whether the lagna must fall inside the arc is flatly contradicted** between
  two Tamil sources. That must be a setting, defaulting to ignore.
- **Partial kala sarpa** — one graha outside — has no Tamil term and Tamil
  sources say it is simply no dosham.
- It is **absent from BPHS, Brihat Jataka, Saravali and Phaladeepika** and is
  most likely a 20th-century accretion. It is nonetheless **entirely standard in
  Tamil Nadu today**, run as routine copy by Daily Thanthi and Maalai Malar.

---

## The other doshams, ranked

**Blocked on gochara** — and they are *one* feature, not four, since each is
`bhava_of(Saturn's transit rasi, natal Moon rasi)`: **ஏழரைச் சனி** with its legs
விரைய / ஜென்ம / பாத சனி, **அஷ்டமச் சனி**, **அர்த்தாஷ்டமச் சனி**, **கண்டக சனி**.
Scoping "gochara" down to a Saturn ingress table unlocks the highest-demand group
cheaply.

**Cheap now:** கேந்திராதிபத்ய தோஷம் (internal only, never surfaced) and
சண்டாள யோகம்.

**Tables ready, verdict deferred:** ரஜ்ஜு and நாடி. Ship each person's rajju limb
and nadi and whether they coincide — but **not** PASS/FAIL, and never the harm
attributions the sources print, which say *"புருஷன் மரணம்"*. An app must not say
that to a couple.

> **A finding that will matter in Phase 4:** Tamil Wikipedia's canonical ten
> poruthams include **ரச்சு** and **exclude நாடி** — the exact inverse of North
> Indian Ashtakoota, where Nadi carries the heaviest weight and Rajju does not
> exist. Relative severity must be Tamil-configured, not inherited.

---

## Questions for the astrologer

1. **Which house set?** {2,4,7,8,12}, {1,2,4,7,8,12}, or the classical
   {1,4,7,8,12}? We report all three; you would tell us which to lead with.
2. **Is the 7th or the 8th worse?** No Tamil source found ranks them. We treat
   them as one tier.
3. **Which exemptions do you actually apply?** Four are computed. Sources list at
   least a dozen, and one practitioner's list reduces 100 flagged charts to 3.
4. **Should the app ever print a conclusion here at all**, or is
   "here are the inputs" the right permanent answer?

---

## What we could not verify

- **The graded 1 / ¾ / ½ reference weighting.** Attested in one Tamil source
  (suryajeyavel69), which confirms the Lagna > Moon > Venus *ordering* — but not
  enough to implement as a score.
- **A percentage.** Tamil practice quantifies with fractions
  (கால் / அரை / முக்கால் / முழு) and with a comparative **பாபசாம்யம** between two
  charts. The "X% Manglik" display is a software convention, not a tradition;
  **தோஷ சதவீதம் is a coinage appearing in no source** and must never be rendered.
- **A printed Tamil textbook**, again. Same gap as the other two audits.

---

*Corrections welcome and expected. Record them against the section.*
