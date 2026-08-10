"""Names and fixed tables for the Tamil panchangam.

Separated from the arithmetic in :mod:`panchangam` so this file can be read and
checked by someone who knows Tamil and no Python. Every table here is data a
practitioner can verify line by line against a printed almanac; nothing in it is
computed.

Two orthography decisions, made once and applied throughout.

**Almanac Tamil, not Sanskritised Tamil.** Several terms have two forms in real
use -- வளர்பிறை vs சுக்ல பக்ஷம், அசுவினி vs அஸ்வினி, சுவாதி vs ஸ்வாதி. Tamil
almanacs (Pambu Panchangam and its descendants) favour the native forms and
software often uses the grantha ones. Both are correct; only inconsistency looks
wrong. These tables take the almanac column.

**No mechanical truncation, ever.** Tamil letters are a base character plus
combining marks, so cutting a name at a fixed length can drop a mark and produce
a different word. Short forms are authored, exactly as in
:mod:`jyotish.core.zodiac`.

Where the traditions genuinely disagree -- and for the ritu they do, by a whole
month -- the choice is stated in the comment above the table rather than left for
a reader to discover from output that looks slightly wrong.
"""

from __future__ import annotations

from ..core.zodiac import Term

# --- tithi -------------------------------------------------------------------
#
# Thirty lunar days, each 12 degrees of elongation. The names run 1-14 in each
# paksha with a special name for the full and new moons, so the list is really
# fourteen names used twice plus two singletons. Paksha is carried separately
# rather than baked into the name, because an almanac prints it as its own word:
# "வளர்பிறை ஏகாதசி", not "Shukla-Ekadashi" as one token.

_TITHI_CORE: tuple[Term, ...] = (
    Term("Pratipada", "பிரதமை", "Prathamai", "1", "பிர"),
    Term("Dwitiya", "துவிதியை", "Thuvithiyai", "2", "துவி"),
    Term("Tritiya", "திருதியை", "Thiruthiyai", "3", "திரு"),
    Term("Chaturthi", "சதுர்த்தி", "Chathurthi", "4", "சது"),
    Term("Panchami", "பஞ்சமி", "Panchami", "5", "பஞ்"),
    Term("Shashthi", "சஷ்டி", "Shashti", "6", "சஷ்"),
    Term("Saptami", "சப்தமி", "Sapthami", "7", "சப்"),
    Term("Ashtami", "அஷ்டமி", "Ashtami", "8", "அஷ்"),
    Term("Navami", "நவமி", "Navami", "9", "நவ"),
    Term("Dashami", "தசமி", "Thasami", "10", "தச"),
    Term("Ekadashi", "ஏகாதசி", "Ekathasi", "11", "ஏகா"),
    Term("Dwadashi", "துவாதசி", "Thuvathasi", "12", "துவா"),
    Term("Trayodashi", "திரயோதசி", "Thirayothasi", "13", "திர"),
    Term("Chaturdashi", "சதுர்த்தசி", "Chathurthasi", "14", "சதுர்"),
)

PURNIMA = Term("Purnima", "பௌர்ணமி", "Pournami", "FM", "பௌ")
AMAVASYA = Term("Amavasya", "அமாவாசை", "Amavasai", "NM", "அமா")

#: All thirty, index 0 = first tithi of the waxing fortnight.
TITHIS: tuple[Term, ...] = (
    *_TITHI_CORE, PURNIMA, *_TITHI_CORE, AMAVASYA,
)

#: Waxing then waning. The native Tamil forms are what almanacs print; the
#: Sanskrit-derived சுக்ல பக்ஷம் / கிருஷ்ண பக்ஷம் appear in some software.
PAKSHAS: tuple[Term, ...] = (
    Term("Shukla paksha", "வளர்பிறை", "Valarpirai", "S", "வளர்"),
    Term("Krishna paksha", "தேய்பிறை", "Theipirai", "K", "தேய்"),
)


# --- vaara -------------------------------------------------------------------
#
# Index 0 is Sunday, matching the Jyotish convention rather than Python's
# Monday-first weekday(). The Jyotish day runs sunrise to sunrise, so which
# weekday applies to a given instant is a question for panchangam.jyotish_day,
# not for this table.

VAARAS: tuple[Term, ...] = (
    Term("Sunday", "ஞாயிற்றுக்கிழமை", "Nyayitrukkizhamai", "Sun", "ஞாயிறு"),
    Term("Monday", "திங்கட்கிழமை", "Thingatkizhamai", "Mon", "திங்கள்"),
    Term("Tuesday", "செவ்வாய்க்கிழமை", "Sevvaaykkizhamai", "Tue", "செவ்வாய்"),
    Term("Wednesday", "புதன்கிழமை", "Puthankizhamai", "Wed", "புதன்"),
    Term("Thursday", "வியாழக்கிழமை", "Viyazhakkizhamai", "Thu", "வியாழன்"),
    Term("Friday", "வெள்ளிக்கிழமை", "Vellikkizhamai", "Fri", "வெள்ளி"),
    Term("Saturday", "சனிக்கிழமை", "Sanikkizhamai", "Sat", "சனி"),
)

#: Graha ruling each weekday, which is where the names come from -- ஞாயிறு is
#: the Sun, திங்கள் the Moon, and so on around the classical week.
VAARA_LORDS: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6)


# --- yoga --------------------------------------------------------------------
#
# The sum of the two luminaries' sidereal longitudes, in 13 deg 20 min steps.
# Being a SUM rather than a difference, the ayanamsa enters twice: computing yoga
# from tropical longitudes is wrong by about 48 degrees, which is three and a
# half yogas. It is the classic fatal bug in panchangam code.

YOGAS: tuple[Term, ...] = (
    Term("Vishkambha", "விஷ்கம்பம்", "Vishkambam"),
    Term("Priti", "பிரீதி", "Preethi"),
    Term("Ayushman", "ஆயுஷ்மான்", "Ayushmaan"),
    Term("Saubhagya", "சௌபாக்கியம்", "Saubaakkiyam"),
    Term("Shobhana", "சோபனம்", "Sobanam"),
    Term("Atiganda", "அதிகண்டம்", "Athikandam"),
    Term("Sukarma", "சுகர்மம்", "Sukarmam"),
    Term("Dhriti", "திருதி", "Thiruthi"),
    Term("Shula", "சூலம்", "Soolam"),
    Term("Ganda", "கண்டம்", "Kandam"),
    Term("Vriddhi", "விருத்தி", "Virutthi"),
    Term("Dhruva", "துருவம்", "Thuruvam"),
    Term("Vyaghata", "வியாகதம்", "Viyaakatham"),
    Term("Harshana", "ஹர்ஷணம்", "Harshanam"),
    Term("Vajra", "வஜ்ரம்", "Vajram"),
    Term("Siddhi", "சித்தி", "Siddhi"),
    Term("Vyatipata", "வியதீபாதம்", "Vyatheepatham"),
    Term("Variyana", "வரியான்", "Variyaan"),
    Term("Parigha", "பரிகம்", "Parigam"),
    Term("Shiva", "சிவம்", "Sivam"),
    Term("Siddha", "சித்தம்", "Siddham"),
    Term("Sadhya", "சாத்தியம்", "Saathiyam"),
    Term("Shubha", "சுபம்", "Subam"),
    Term("Shukla", "சுக்கிலம்", "Sukkilam"),
    Term("Brahma", "பிரம்மம்", "Pirammam"),
    Term("Indra", "ஐந்திரம்", "Aindhiram"),
    Term("Vaidhriti", "வைதிருதி", "Vaithiruthi"),
)

#: The nine yogas the muhurta texts call malefic, 0-based. Vyatipata (16) and
#: Vaidhriti (26) are the two treated as outright dosha and flagged explicitly by
#: Tamil almanacs; the other seven are conventionally malefic only for an opening
#: stretch of their duration, which is why this is a flag and not a verdict.
MALEFIC_YOGAS: frozenset[int] = frozenset({0, 5, 8, 9, 12, 14, 16, 18, 26})
SEVERE_YOGAS: frozenset[int] = frozenset({16, 26})


# --- karana ------------------------------------------------------------------
#
# Half a tithi: 6 degrees of elongation, so 60 per lunar month. Seven "movable"
# karanas cycle eight times to fill 56 of those slots; four "fixed" ones occupy
# the remaining four, and they are not adjacent -- Kimstughna opens the month and
# the other three close it.

KARANAS: tuple[Term, ...] = (
    # movable (chara), in cycle order
    Term("Bava", "பவம்", "Bavam"),
    Term("Balava", "பாலவம்", "Baalavam"),
    Term("Kaulava", "கௌலவம்", "Kaulavam"),
    # ல, not ள. Sanskrit तैतिल has the dental la, and every attested Tamil
    # source prints தைதுலை / தைதுலம் / தைத்தூலம். The two letters are adjacent
    # code points and this is the classic Tamil transcription slip.
    Term("Taitila", "தைதுலை", "Thaithulai"),
    Term("Gara", "கரசை", "Karasai"),
    Term("Vanija", "வணிசை", "Vanisai"),
    Term("Vishti", "பத்திரை", "Baththirai"),
    # fixed (sthira)
    Term("Shakuni", "சகுனி", "Sakuni"),
    Term("Chatushpada", "சதுஷ்பாதம்", "Chathushpaatham"),
    Term("Naga", "நாகவம்", "Naagavam"),
    Term("Kimstughna", "கிம்ஸ்துக்நம்", "Kimsthuknam"),
)

MOVABLE_KARANAS = 7
#: Vishti, better known as Bhadra -- the one karana Tamil practice genuinely
#: avoids for any auspicious act.
VISHTI = 6


def karana_index(slot: int) -> int:
    """Which of the eleven karanas occupies half-tithi ``slot`` (0-59).

    The mapping is irregular and is the part implementations get wrong, so it is
    written out as a rule with its boundaries visible:

    ===========  ==========================================
    slot 0       Kimstughna -- the *first* half-tithi of the
                 lunar month, not the last
    slots 1-56   the seven movable karanas, eight times round
    slot 57      Shakuni
    slot 58      Chatushpada
    slot 59      Naga
    ===========  ==========================================

    The check that this is right: Vishti/Bhadra must land on slots 7, 14, 21, 28,
    35, 42, 49 and 56, which reproduces the classical Bhadra rule exactly.
    """
    slot %= 60
    if slot == 0:
        return 10                          # Kimstughna
    if slot <= 56:
        return (slot - 1) % MOVABLE_KARANAS
    return 7 + (slot - 57)                 # Shakuni, Chatushpada, Naga


# --- the inauspicious periods ------------------------------------------------
#
# Rahu kalam, yamagandam and kuligai are each one eighth of the interval from
# sunrise to sunset, selected by weekday. The familiar "1.5 hours" is only true
# on a day with exactly twelve hours of light -- in Chennai the eighth runs from
# about 85 to 95 minutes across the year.
#
# Indices below are 0-based into the eight daylight parts, and the clock times in
# the comments assume a 06:00 sunrise and 18:00 sunset, which is how these are
# always taught.

#: Graha ruling each weekday: Sun rules Sunday, Moon Monday, and so on. This is
#: the classical week, and it is the input to the rule below.
_WEEKDAY_LORDS = (0, 1, 2, 3, 4, 5, 6)  # graha indices, Sunday first


def portion_of(weekday: int, graha: int, night: bool = False) -> int:
    """Which eighth of the day belongs to a graha. Brihat Parashara Hora III.

    The rule, and it is worth knowing rather than memorising eight tables:

        The day is divided into eight equal parts. The **first** goes to the lord
        of the weekday, and the rest follow in weekday-lord order. The eighth
        part is lordless. At night the count starts instead from the lord of the
        *fifth* weekday from the one in question.

    So yamagandam is simply Jupiter's portion, kuligai is Saturn's, and the
    familiar clock times fall out of arithmetic rather than being learned. Three
    more named periods -- காலன் காலம் (the Sun's), மிருத்யு (Mars's) and
    அர்த்தபிரகணன் (Mercury's) -- come from the same rule and can be added here
    without a new table.

    Rahu is the exception and has to stay a literal table: it is a chaya graha
    with no weekday lordship, so the rule cannot reach it.
    """
    start = (weekday + 4) % 7 if night else weekday
    return (_WEEKDAY_LORDS.index(graha) - start) % 7


def _portions(graha: int, night: bool = False) -> tuple[int, ...]:
    return tuple(portion_of(w, graha, night) for w in range(7))


#: ராகு காலம். Sun 16:30, Mon 07:30, Tue 15:00, Wed 12:00, Thu 13:30,
#: Fri 10:30, Sat 09:00 on a 06:00-18:00 day. Note that part 0 never appears:
#: rahu kalam never begins at sunrise.
RAHU_PART: tuple[int, ...] = (7, 1, 6, 4, 5, 3, 2)

#: எமகண்டம் -- Jupiter's portion. Derived, not typed: a table written out by hand
#: is a table that can disagree with the rule that is supposed to produce it.
YAMA_PART: tuple[int, ...] = _portions(4)

#: குளிகை -- Saturn's portion. Comes out as a clean descending walk from
#: Sunday 15:00 to Saturday 06:00, which is how Tamil almanacs teach it.
KULIGAI_PART: tuple[int, ...] = _portions(6)

RAHU_KALAM = Term("Rahu kalam", "ராகு காலம்", "Raagu kaalam", "RK", "ராகு")
YAMAGANDAM = Term("Yamagandam", "எமகண்டம்", "Emakandam", "YG", "எம")
KULIGAI = Term("Kuligai", "குளிகை", "Kuligai", "KG", "குளி")


# --- gowri panchangam --------------------------------------------------------
#
# கௌரி பஞ்சாங்கம். Eight named windows across the day and eight more across the
# night, each owned by a graha. This is where நல்ல நேரம் comes from.
#
# The eight are Sun-Uthiyogam, Moon-Amirtham, Mars-Rogam, Mercury-Laabam,
# Jupiter-Dhanam, Venus-Sugam, Saturn-Soram and Rahu-Visham, so the index below
# is the graha index for the first seven and Rahu takes the eighth slot.

GOWRI: tuple[Term, ...] = (
    Term("Udyoga", "உத்தியோகம்", "Uthiyogam", "Ud", "உத்தி"),
    Term("Amrita", "அமிர்தம்", "Amirtham", "Am", "அமிர்"),
    Term("Roga", "ரோகம்", "Rogam", "Ro", "ரோ"),
    Term("Labha", "லாபம்", "Laabam", "La", "லா"),
    Term("Dhana", "தனம்", "Dhanam", "Dh", "தன"),
    Term("Sukha", "சுகம்", "Sugam", "Su", "சுக"),
    Term("Chora", "சோரம்", "Soram", "Ch", "சோ"),
    Term("Visha", "விஷம்", "Visham", "Vi", "விஷ"),
)

#: Five of the eight are sought out, three avoided. Amirtham is the best.
AUSPICIOUS_GOWRI: frozenset[int] = frozenset({0, 1, 3, 4, 5})

#: The day sequences, sunrise to sunset, one row per weekday from Sunday.
#:
#: Written out literally rather than generated, and that is a deliberate choice
#: about *where* the risk sits. These fourteen rows are exactly what Drik
#: Panchang, ePanchang and Dinamalar print, so a Tamil reader can check them
#: against an almanac without reading any code. They are not a single list
#: rotated by weekday -- Visham sits at a weekday-dependent place in the wheel,
#: so naive rotation reproduces Sunday and gets the other six days wrong.
#: ``test_panchangam`` re-derives every row from the underlying rule and asserts
#: it matches, which is the check without the risk.
GOWRI_DAY: tuple[tuple[int, ...], ...] = (
    (0, 1, 2, 3, 4, 5, 6, 7),   # ஞாயிறு  Sunday
    (1, 7, 2, 3, 4, 5, 6, 0),   # திங்கள்  Monday
    (2, 3, 4, 5, 6, 0, 7, 1),   # செவ்வாய் Tuesday
    (3, 4, 5, 6, 7, 0, 1, 2),   # புதன்    Wednesday
    (4, 5, 6, 0, 1, 7, 2, 3),   # வியாழன்  Thursday
    (5, 6, 0, 7, 1, 2, 3, 4),   # வெள்ளி   Friday
    (6, 0, 7, 1, 2, 3, 4, 5),   # சனி      Saturday
)

#: The night sequences, sunset to the next sunrise. The row is the weekday of the
#: *preceding* sunrise -- Monday night begins at Monday's sunset.
GOWRI_NIGHT: tuple[tuple[int, ...], ...] = (
    (4, 5, 6, 7, 0, 1, 2, 3),   # Sunday night
    (5, 6, 0, 1, 7, 2, 3, 4),   # Monday night
    (6, 0, 7, 1, 2, 3, 4, 5),   # Tuesday night
    (0, 1, 2, 3, 4, 5, 6, 7),   # Wednesday night
    (1, 7, 2, 3, 4, 5, 6, 0),   # Thursday night
    (2, 3, 4, 5, 6, 0, 7, 1),   # Friday night
    (3, 4, 5, 6, 0, 7, 1, 2),   # Saturday night
)

#: The three wheels the sequences above are rotations of, differing only in where
#: Visham is inserted. Saturday takes wheel C rather than A, which breaks an
#: otherwise tidy period-3 pattern -- it is the single most likely place to
#: introduce a bug by "simplifying" the table, so the exception is named here.
GOWRI_WHEELS: tuple[tuple[int, ...], ...] = (
    (0, 1, 2, 3, 4, 5, 6, 7),   # A: Visham after Saturn -- Sunday, Wednesday
    (0, 1, 7, 2, 3, 4, 5, 6),   # B: Visham after the Moon -- Monday, Thursday
    (0, 7, 1, 2, 3, 4, 5, 6),   # C: Visham after the Sun -- Tue, Fri, SATURDAY
)

#: Which wheel each weekday uses, Sunday first.
GOWRI_WHEEL_OF: tuple[int, ...] = (0, 1, 2, 0, 1, 2, 2)

NALLA_NERAM = Term("Nalla neram", "நல்ல நேரம்", "Nalla neram", "NN", "நல்ல")


# --- the Tamil solar calendar ------------------------------------------------
#
# A pure sidereal solar calendar: the month IS the Sun's rasi, so the index here
# is the rasi index and nothing needs mapping. Month lengths run from 29 to 32
# days and are computed, never assumed -- in 2026-27 Karthigai is 29 days and
# Aani is 32.

TAMIL_MONTHS: tuple[Term, ...] = (
    Term("Chithirai", "சித்திரை", "Chithirai"),
    Term("Vaikasi", "வைகாசி", "Vaikasi"),
    Term("Aani", "ஆனி", "Aani"),
    Term("Aadi", "ஆடி", "Aadi"),
    Term("Aavani", "ஆவணி", "Aavani"),
    Term("Purattasi", "புரட்டாசி", "Purattasi"),
    Term("Aippasi", "ஐப்பசி", "Aippasi"),
    Term("Karthigai", "கார்த்திகை", "Karthigai"),
    Term("Margazhi", "மார்கழி", "Margazhi"),
    Term("Thai", "தை", "Thai"),
    Term("Maasi", "மாசி", "Maasi"),
    Term("Panguni", "பங்குனி", "Panguni"),
)

#: The first month whose sankranti falls in the *next* Gregorian year relative to
#: the Chithirai that opened the Tamil year. Thai starts in mid-January, so
#: months 9, 10 and 11 carry a Gregorian year one higher than their own year's
#: name. See :func:`panchangam.samvatsara`.
MONTHS_INTO_NEXT_YEAR = 9

#: Gregorian year whose Chithirai opened cycle year 0 (Prabhava). Anchored on the
#: running year: Chithirai 2026 began பராபவ, the 40th name, so 2026 - 39 = 1987.
SAMVATSARA_EPOCH_YEAR = 1987

#: The sixty year-names, in order. South Indian reckoning is a plain mod-60 count
#: with no expunged years -- the kshaya samvatsara of the northern Barhaspatya
#: system does not apply and must not be implemented here.
SAMVATSARAS: tuple[Term, ...] = (
    Term("Prabhava", "பிரபவ", "Pirabava"),
    Term("Vibhava", "விபவ", "Vibava"),
    Term("Shukla", "சுக்ல", "Sukla"),
    Term("Pramoduta", "பிரமோதூத", "Piramodhootha"),
    Term("Prajotpatti", "பிரசோற்பத்தி", "Pirasotpatti"),
    Term("Angirasa", "ஆங்கீரச", "Aangeerasa"),
    Term("Srimukha", "ஸ்ரீமுக", "Srimuka"),
    Term("Bhava", "பவ", "Bava"),
    Term("Yuva", "யுவ", "Yuva"),
    Term("Dhatu", "தாது", "Dhaathu"),
    Term("Ishvara", "ஈஸ்வர", "Eesvara"),
    Term("Bahudhanya", "வெகுதானிய", "Veguthaaniya"),
    Term("Pramadi", "பிரமாதி", "Piramaadhi"),
    Term("Vikrama", "விக்கிரம", "Vikkirama"),
    Term("Vishu", "விஷு", "Vishu"),
    Term("Chitrabhanu", "சித்திரபானு", "Chithirabaanu"),
    Term("Subhanu", "சுபானு", "Subaanu"),
    Term("Tarana", "தாரண", "Thaarana"),
    Term("Parthiva", "பார்த்திப", "Paarthiba"),
    Term("Vyaya", "விய", "Viya"),
    Term("Sarvajit", "சர்வசித்து", "Sarvasithu"),
    Term("Sarvadhari", "சர்வதாரி", "Sarvadhaari"),
    Term("Virodhi", "விரோதி", "Virodhi"),
    Term("Vikriti", "விக்ருதி", "Vikruthi"),
    Term("Khara", "கர", "Kara"),
    Term("Nandana", "நந்தன", "Nandhana"),
    Term("Vijaya", "விஜய", "Vijaya"),
    Term("Jaya", "ஜய", "Jaya"),
    Term("Manmatha", "மன்மத", "Manmatha"),
    Term("Durmukhi", "துன்முகி", "Dhunmugi"),
    Term("Hevilambi", "ஹேவிளம்பி", "Hevilambi"),
    Term("Vilambi", "விளம்பி", "Vilambi"),
    Term("Vikari", "விகாரி", "Vikaari"),
    Term("Sharvari", "சார்வரி", "Saarvari"),
    Term("Plava", "பிலவ", "Pilava"),
    Term("Shubhakrit", "சுபகிருது", "Subakiruthu"),
    Term("Shobhakrit", "சோபகிருது", "Sobakiruthu"),
    Term("Krodhi", "குரோதி", "Kurodhi"),
    Term("Vishvavasu", "விசுவாவசு", "Visuvaavasu"),
    Term("Parabhava", "பராபவ", "Paraabava"),
    Term("Plavanga", "பிலவங்க", "Pilavanga"),
    Term("Kilaka", "கீலக", "Keelaga"),
    Term("Saumya", "சௌமிய", "Saumiya"),
    Term("Sadharana", "சாதாரண", "Saadhaarana"),
    Term("Virodhikrit", "விரோதிகிருது", "Virodhikiruthu"),
    Term("Paridhavi", "பரிதாபி", "Paridhaabi"),
    Term("Pramadicha", "பிரமாதீச", "Piramaadheesa"),
    Term("Ananda", "ஆனந்த", "Aanandha"),
    Term("Rakshasa", "ராட்சச", "Raatchasa"),
    Term("Nala", "நள", "Nala"),
    Term("Pingala", "பிங்கள", "Pingala"),
    Term("Kalayukti", "காளயுக்தி", "Kaalayukthi"),
    Term("Siddharthi", "சித்தார்த்தி", "Siddhaarthi"),
    Term("Raudri", "ரௌத்திரி", "Raudhiri"),
    Term("Durmati", "துன்மதி", "Dhunmathi"),
    Term("Dundubhi", "துந்துபி", "Dhundhubi"),
    Term("Rudhirodgari", "ருத்ரோத்காரி", "Rudhrothgaari"),
    Term("Raktakshi", "ரக்தாட்சி", "Rakthaatchi"),
    Term("Krodhana", "குரோதன", "Kurodhana"),
    Term("Akshaya", "அட்சய", "Atchaya"),
)

#: Sidereal, as Tamil almanacs print it -- Uttarayanam begins at Makara
#: sankranti (Thai 1, about 14 January), which is roughly 24 days after the true
#: tropical solstice. Using the tropical definition would put the turn in
#: December and disagree with every almanac.
AYANAS: tuple[Term, ...] = (
    Term("Uttarayana", "உத்தராயணம்", "Uttaraayanam"),
    Term("Dakshinayana", "தட்சிணாயனம்", "Thatchinaayanam"),
)

#: The six seasons, on the Surya-Siddhanta saura scheme that computed Tamil
#: panchangams print. Note the offset: Vasanta is **Meena and Mesha**, not Mesha
#: and Rishaba. This is a live disagreement -- the classical Tolkappiyam
#: paruvakkaalam of Tamil literature runs one month later -- and picking the
#: wrong one is the easiest way to ship a value that is confidently wrong.
#: See :func:`panchangam.ritu_of`.
RITUS: tuple[Term, ...] = (
    Term("Vasanta", "வசந்த ருது", "Vasantha ruthu"),
    Term("Grishma", "கிரீஷ்ம ருது", "Greeshma ruthu"),
    Term("Varsha", "வர்ஷ ருது", "Varsha ruthu"),
    Term("Sharad", "சரத் ருது", "Sarath ruthu"),
    Term("Hemanta", "ஹேமந்த ருது", "Hemantha ruthu"),
    Term("Shishira", "சிசிர ருது", "Sisira ruthu"),
)
