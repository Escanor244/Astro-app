# 01 — Dignity: உச்சம், நீசம், and how well a graha sits

*Read [00-orientation.md](00-orientation.md) first. Nothing else assumed.*

---

## The question this answers

A chart tells you *where* each graha is. It does not yet tell you whether that
placement is a good one.

Jyotish answers with **dignity**: every graha has signs it thrives in and signs
it struggles in, and the same graha can be a very different thing in each. A
Saturn in Thulam builds; a Saturn in Mesham grinds. Both are Saturn.

This is the second thing anyone reads off a jathagam, and on a printed chart it
is marked right beside the graha.

---

## The ladder

Nine states, best to worst:

| State | Tamil | What it means |
|---|---|---|
| **Exalted** | **உச்சம்** | Its single best sign. Delivers what it promises |
| Moolatrikona | மூலத்திரிகோணம் | A favoured degree range, just below exaltation |
| Own sign | ஆட்சி | It rules this sign. Comfortable, in charge |
| Friend | நட்பு | Ruled by a graha it gets on with |
| Neutral | சமம் | Ruled by a graha it neither likes nor dislikes |
| Enemy | பகை | Ruled by a graha it is at odds with |
| **Debilitated** | **நீசம்** | The sign opposite its exaltation. Struggles to deliver |

The app colours these, so the two extremes stand out the way they do on paper:
green for உச்சம், red for நீசம்.

---

## Exaltation and debilitation

Each graha has one **exact degree** of deep exaltation. The whole sign counts as
the exaltation sign; the degree is where the strength peaks.

| Graha | Exalted at | Debilitated at |
|---|---|---|
| Sun / சூரியன் | Mesham 10° | Thulam 10° |
| Moon / சந்திரன் | Rishabam 3° | Viruchigam 3° |
| Mars / செவ்வாய் | Magaram 28° | Kadagam 28° |
| Mercury / புதன் | Kanni 15° | Meenam 15° |
| Jupiter / குரு | Kadagam 5° | Magaram 5° |
| Venus / சுக்கிரன் | Meenam 27° | Kanni 27° |
| Saturn / சனி | Thulam 20° | Mesham 20° |

**Debilitation is always exactly 180° from exaltation.** Not a second list to
memorise — one fact with two names. The engine *derives* it rather than storing
it, so the two can never disagree.

The app also reports how far a graha sits from its deep exaltation point. A
Venus at Meenam 27° is exalted in a way that a Venus at Meenam 2° is not, even
though both carry the label.

### Rahu and Ketu have none

You will see other apps confidently print an exaltation for the nodes. **We
don't**, and that is deliberate.

Brihat Parashara Hora assigns them no exaltation at all. Later practice split
two ways — some hold Rahu exalted in Rishabam, others in Mithunam — and neither
won. Picking one silently would hand you a dignity that looks authoritative and
is a coin toss. The app shows `—` and says why on hover.

The nodes still have a **dispositor** (the lord of the sign they occupy), and
that *is* real information about them.

---

## The other two marked states

Dignity is not the only thing marked on a graha, and the three are independent —
a graha can be all three at once, and each says something different:

| Mark | Tamil | Meaning |
|---|---|---|
| **℞** | வக்ரம் | Retrograde — apparently moving backwards |
| **☌** | அஸ்தங்கதம் | Combust — burnt by sitting too close to the Sun |
| colour | நீசம் / உச்சம் | The dignity ladder above |

**Combustion** happens when a graha is within a certain distance of the Sun:
Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°. Mercury and
Venus get tighter bounds when retrograde (12° and 8°), which matters because
those two spend much of their retrograde time near the Sun — exactly the case
the tighter bound exists to separate.

The Sun is never combust, and the nodes are not bodies, so they are not either.

---

## Two exceptions worth knowing

Both are real classical irregularities that look like bugs.

**The Moon's moolatrikona is not in its own sign.** Six of the seven grahas have
their moolatrikona inside the sign they rule. The Moon's is Rishabam 4°–30° —
its *exaltation* sign — while the whole of its own sign Kadagam is plain ஆட்சி.
Any "surely this is uniform" tidy-up breaks it.

**Kanni is three things at once for Mercury.** It is Mercury's exaltation sign,
its moolatrikona, and its own sign. The app lets exaltation win for the whole
sign, which is what most software does. Some texts subdivide it: exaltation to
15°, moolatrikona to 20°, own sign beyond.

---

## Friendships are not symmetric

The natural (naisargika) friendships come from Brihat Parashara Hora:

| Graha | Friends | Enemies |
|---|---|---|
| Sun | Moon, Mars, Jupiter | Venus, Saturn |
| Moon | Sun, Mercury | *(none)* |
| Mars | Sun, Moon, Jupiter | Mercury |
| Mercury | Sun, Venus | Moon |
| Jupiter | Sun, Moon, Mars | Mercury, Venus |
| Venus | Mercury, Saturn | Sun, Moon |
| Saturn | Mercury, Venus | Sun, Mars, Moon |

Look at the Moon and Mercury. **The Moon counts Mercury a friend; Mercury counts
the Moon an enemy.** That is not a typo in this table — the classical relation
genuinely runs one way. A refactor that makes the table symmetric would look
like a clean-up and would change the dignity of real placements, so a test
asserts the asymmetry.

---

## "Why?" is always available

Hover any dignity in the app and it tells you which rule fired:

> *Saturn is in its debilitation sign, the rasi opposite its exaltation, 8.5
> degrees from the deepest point of debilitation*

That is this project's third commitment — show your work — applied to the
smallest thing on the page. "Exalted" and "in a sign ruled by a graha it counts
a friend" are very different claims, and a label alone hides which one you got.

---

## What is not here yet

**நீச பங்கம் (neechabhanga)** — debilitation cancellation. A debilitated graha
can have that debility lifted by several classical conditions, and a chart with
neechabhanga is read completely differently from one without. The rules are
numerous and the sources disagree on several, so it belongs with the **Phase 5**
explainable rule base, where each condition can cite its source and show which
one fired.

Until then: a நீசம் in this app means the placement, not the final verdict.

**Shadbala** — six-fold numerical strength — also comes later. Dignity is the
qualitative version of the same question.

---

## Try it

```bash
python scripts\chart.py --date 1990-05-15 --time 06:30 --place "Chennai" --pick 1
```

The rightmost columns are the dignity. In that chart Venus sits in Meenam at
18°34′ — **உச்சம்**, nine degrees short of its deep exaltation — and Saturn is in
Magaram, its own sign, retrograde.

---

**Next:** [02-dasha.md](02-dasha.md) — when any of this actually arrives.
