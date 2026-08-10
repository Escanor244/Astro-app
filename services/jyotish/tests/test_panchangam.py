"""The Tamil panchangam: the five limbs, the kalams, and the gowri windows.

The strategy has three layers, because the risks are different in kind.

**Table integrity.** Most of a panchangam is fixed data — 30 tithis, 27 yogas, 11
karanas, 14 gowri sequences — and a table with a missing row is invisible until a
user hits that day. So the tables are counted, checked for duplicates, and in the
gowri case *re-derived from the underlying rule* and compared, which catches a
transcription slip in any of the 112 cells.

**Independent implementation.** jyotishganit computes the five limbs from its own
ephemeris, so agreement on names is evidence rather than self-consistency. Where
we deliberately differ — it takes the weekday from the civil date, we take it
from sunrise — the test asserts the *disagreement*, so nobody later "fixes" us
into being wrong.

**A published day.** Monday 10 August 2026 at Chennai is checked against Drik
Panchang's printed values for all sixteen gowri windows. That is the one test
that would catch a wheel rotated the wrong way while every structural property
still held.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from jyotish.core import ayanamsa as ay
from jyotish.core.zodiac import NAKSHATRAS
from jyotish.panchanga import daylight as dl
from jyotish.panchanga import lexicon as lex
from jyotish.panchanga import panchangam as pg

IST = ZoneInfo("Asia/Kolkata")
CHENNAI = (13.0827, 80.2707, "Asia/Kolkata")

#: Monday 10 August 2026, noon at Chennai. Chosen because an independent
#: reference (Drik Panchang) publishes every gowri window for exactly this day
#: and place, so the expected values below are not our own output written down.
REFERENCE_DAY = datetime(2026, 8, 10, 12, 0)


def _utc(local: datetime, zone: ZoneInfo = IST) -> datetime:
    return local.replace(tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)


def _hhmm(moment: datetime | None, zone: ZoneInfo = IST) -> str:
    if moment is None:
        return "--"
    return moment.replace(tzinfo=timezone.utc).astimezone(zone).strftime("%H:%M")


@pytest.fixture(scope="module")
def reference():
    """The Drik-published day. Module-scoped: each compute costs ~0.3 s."""
    return pg.compute(_utc(REFERENCE_DAY), *CHENNAI)


@pytest.fixture(scope="module")
def jg():
    return pytest.importorskip(
        "jyotishganit.components.panchanga",
        reason="cross-validation reference; declared in requirements-dev.txt",
    )


# --- table integrity ---------------------------------------------------------


def test_the_tables_have_the_right_number_of_entries():
    assert len(lex.TITHIS) == 30
    assert len(lex.YOGAS) == 27
    assert len(lex.KARANAS) == 11
    assert len(lex.VAARAS) == 7
    assert len(lex.PAKSHAS) == 2
    assert len(lex.TAMIL_MONTHS) == 12
    assert len(lex.SAMVATSARAS) == 60
    assert len(lex.AYANAS) == 2
    assert len(lex.RITUS) == 6
    assert len(lex.GOWRI) == 8


def test_every_table_entry_carries_a_tamil_name():
    for table in (lex.TITHIS, lex.YOGAS, lex.KARANAS, lex.VAARAS, lex.PAKSHAS,
                  lex.TAMIL_MONTHS, lex.SAMVATSARAS, lex.AYANAS, lex.RITUS,
                  lex.GOWRI):
        for entry in table:
            assert entry.ta.strip(), entry
            assert entry.ta_latin.strip(), entry


def test_names_that_must_be_distinct_are_distinct():
    """A duplicated row is a transcription slip that silently renames a day."""
    for table in (lex.YOGAS, lex.KARANAS, lex.VAARAS, lex.TAMIL_MONTHS,
                  lex.SAMVATSARAS, lex.GOWRI):
        tamil = [t.ta for t in table]
        assert len(set(tamil)) == len(tamil), tamil
    # Tithis repeat by design: fourteen names in each paksha, plus two singletons.
    assert len(set(t.ta for t in lex.TITHIS)) == 16


def test_the_two_moon_tithis_sit_at_the_paksha_boundaries():
    assert lex.TITHIS[14] is lex.PURNIMA
    assert lex.TITHIS[29] is lex.AMAVASYA


def test_the_running_tamil_year_is_parabhava():
    """Anchors the 60-year cycle to a checkable fact.

    Chithirai 2026 opened பராபவ, the fortieth name, which Drik Panchang and the
    printed 2026-27 almanacs both carry. Everything else in the cycle follows
    from this one anchor, so if it is right the other 59 are too.
    """
    assert pg.samvatsara(2026, 3) == 39
    assert lex.SAMVATSARAS[39].ta == "பராபவ"
    assert lex.SAMVATSARAS[39].en == "Parabhava"
    # A month in the January-to-April tail belongs to the year that began the
    # previous Chithirai, so its later Gregorian year has to be walked back.
    assert pg.samvatsara(2027, 10) == 39


def test_the_cycle_advances_by_one_name_a_year():
    for year in range(1900, 2100):
        assert (pg.samvatsara(year + 1, 0) - pg.samvatsara(year, 0)) % 60 == 1


# --- karana ------------------------------------------------------------------


def test_the_four_fixed_karanas_sit_where_the_texts_put_them():
    assert lex.KARANAS[lex.karana_index(0)].en == "Kimstughna"
    assert lex.KARANAS[lex.karana_index(57)].en == "Shakuni"
    assert lex.KARANAS[lex.karana_index(58)].en == "Chatushpada"
    assert lex.KARANAS[lex.karana_index(59)].en == "Naga"


def test_bhadra_falls_exactly_where_the_classical_rule_says():
    """The correctness check for the whole 60-slot map.

    Vishti (Bhadra) must occupy slots 7, 14, 21, 28, 35, 42, 49 and 56 — the
    second half of Shukla Chaturthi, the first half of Shukla Ashtami, and so on.
    If the movable cycle is offset by even one slot this fails, and nothing else
    in a panchangam would show it.
    """
    vishti = {s for s in range(60) if lex.karana_index(s) == lex.VISHTI}
    assert vishti == {7, 14, 21, 28, 35, 42, 49, 56}


def test_the_movable_karanas_fill_fifty_six_slots_eight_times_each():
    counts = {}
    for slot in range(60):
        counts[lex.karana_index(slot)] = counts.get(lex.karana_index(slot), 0) + 1
    for movable in range(lex.MOVABLE_KARANAS):
        assert counts[movable] == 8
    for fixed in range(7, 11):
        assert counts[fixed] == 1
    assert sum(counts.values()) == 60


def test_karana_index_wraps_rather_than_indexing_off_the_end():
    assert lex.karana_index(60) == lex.karana_index(0)


# --- the kalams --------------------------------------------------------------


def test_the_kalam_tables_match_what_almanacs_print():
    """The familiar clock times, on the 06:00-18:00 day they are taught with."""
    assert lex.RAHU_PART == (7, 1, 6, 4, 5, 3, 2)
    assert lex.YAMA_PART == (4, 3, 2, 1, 0, 6, 5)
    assert lex.KULIGAI_PART == (6, 5, 4, 3, 2, 1, 0)


def test_rahu_kalam_never_starts_at_sunrise():
    assert 0 not in lex.RAHU_PART


def test_the_parashari_portion_rule_is_self_consistent():
    """Each graha owns exactly one of the seven lorded portions, every weekday."""
    for weekday in range(7):
        for night in (False, True):
            owned = [lex.portion_of(weekday, g, night) for g in range(7)]
            assert sorted(owned) == list(range(7))


# --- gowri -------------------------------------------------------------------


def test_every_gowri_sequence_uses_all_eight_windows_once():
    for table in (lex.GOWRI_DAY, lex.GOWRI_NIGHT):
        assert len(table) == 7
        for row in table:
            assert sorted(row) == list(range(8)), row


def test_every_gowri_sequence_is_a_rotation_of_its_declared_wheel():
    """Re-derives all 112 cells from the rule and compares to the printed grid.

    The rule: the day sequence opens at the window owned by the weekday's own
    lord, the night sequence at the lord of the fifth weekday from it, and both
    then walk that weekday's wheel. Writing the grid out literally keeps it
    checkable against an almanac by someone who reads Tamil and no Python; this
    test is what stops a transcription slip in any one of those cells.
    """
    for weekday in range(7):
        wheel = lex.GOWRI_WHEELS[lex.GOWRI_WHEEL_OF[weekday]]

        for night, table in ((False, lex.GOWRI_DAY), (True, lex.GOWRI_NIGHT)):
            start = (weekday + 4) % 7 if night else weekday
            offset = wheel.index(start)
            derived = tuple(wheel[(offset + i) % 8] for i in range(8))
            assert derived == table[weekday], (weekday, night)


def test_saturday_uses_the_wheel_that_breaks_the_pattern():
    """Named explicitly because it is the one exception someone will 'tidy'."""
    assert lex.GOWRI_WHEEL_OF == (0, 1, 2, 0, 1, 2, 2)
    assert lex.GOWRI_WHEEL_OF[6] == 2, "Saturday takes wheel C, not A"
    assert lex.GOWRI_DAY[6] != lex.GOWRI_DAY[3]


def test_five_of_the_eight_gowri_windows_are_auspicious():
    assert len(lex.AUSPICIOUS_GOWRI) == 5
    good = {lex.GOWRI[i].en for i in lex.AUSPICIOUS_GOWRI}
    assert good == {"Udyoga", "Amrita", "Labha", "Dhana", "Sukha"}


def test_the_gowri_names_are_the_tamil_ones_not_the_choghadiya_set():
    """Guards against a real contamination seen across astrology sites.

    Several English-language sources print a Choghadiya-derived set — Kala,
    Ugra, Shubha — under the Gowri heading. They are a different system. So is
    சோகம் (sorrow), a common corruption of சோரம் (theft, from Chora).
    """
    tamil = {t.ta for t in lex.GOWRI}
    assert "சோரம்" in tamil and "சோகம்" not in tamil
    assert "தனம்" in tamil and "தானம்" not in tamil   # wealth, not charity
    english = {t.en for t in lex.GOWRI}
    assert english.isdisjoint({"Kala", "Ugra", "Shubha", "Amrit"})


# --- the reference day -------------------------------------------------------


def test_sunrise_and_sunset_match_the_published_day(reference):
    assert _hhmm(reference.sun.rising) in ("05:55", "05:56")
    assert _hhmm(reference.sun.setting) in ("18:32", "18:33")


def test_all_sixteen_gowri_windows_match_drik_panchang(reference):
    """Names and order, against an independent publisher for a real date."""
    assert [w.name.en for w in reference.gowri_day] == [
        "Amrita", "Visha", "Roga", "Labha", "Dhana", "Sukha", "Chora", "Udyoga",
    ]
    assert [w.name.en for w in reference.gowri_night] == [
        "Sukha", "Chora", "Udyoga", "Amrita", "Visha", "Roga", "Labha", "Dhana",
    ]


def test_the_gowri_windows_tile_the_day_without_gap(reference):
    assert reference.gowri_day[0].start == reference.sun.rising
    assert reference.gowri_day[-1].end == reference.sun.setting
    for a, b in zip(reference.gowri_day, reference.gowri_day[1:]):
        assert a.end == b.start
    assert reference.gowri_night[0].start == reference.sun.setting
    assert reference.gowri_night[-1].end == reference.next_sunrise


def test_rahu_kalam_on_a_monday_is_the_second_eighth(reference):
    assert reference.vaara == 1
    assert _hhmm(reference.rahu_kalam.start) == "07:30"
    assert reference.rahu_kalam.auspicious is False


def test_rahu_kalam_is_the_visham_gowri_window():
    """They are the same eighth of the day, on every weekday. Not a coincidence.

    Visham is Rahu's gowri portion, and rahu kalam is Rahu's eighth of the
    daylight — one division, two names, and Drik prints the identical clock times
    for both. Pinned because the two tables reach it by completely different
    routes: RAHU_PART is a literal lookup (Rahu has no weekday lordship, so the
    Parashari portion rule cannot produce it) while the gowri grid is a rotation
    of a wheel. If a future edit breaks either, this diverges.
    """
    for weekday in range(7):
        assert lex.GOWRI_DAY[weekday].index(7) == lex.RAHU_PART[weekday], weekday


def test_the_kalams_never_collide_with_each_other():
    for weekday in range(7):
        parts = {lex.RAHU_PART[weekday], lex.YAMA_PART[weekday],
                 lex.KULIGAI_PART[weekday]}
        assert len(parts) == 3, weekday


def test_the_tamil_date_matches_the_almanac(reference):
    """Aadi 2026 began on 17 July by the sunset rule, so 10 August is day 25."""
    assert reference.tamil_month_name.ta == "ஆடி"
    assert reference.tamil_day == 25
    assert reference.tamil_year_name.ta == "பராபவ"
    assert reference.ayana_name.ta == "தட்சிணாயனம்"
    assert reference.ritu_name.en == "Varsha"


def test_the_tamil_date_never_skips_or_repeats_across_a_sankranti():
    """Walks the Thai and Aadi 2026 boundaries day by day.

    These two are the awkward cases in opposite directions, and each produced a
    real defect. Makara sankranti fell at 15:13 on 14 January -- between sunrise
    and sunset -- so by the sunset rule that whole day is **Thai 1**, even though
    the Sun was still in Dhanus when it dawned. Karka sankranti fell at 23:39 on
    16 July, after sunset, so 17 July is Aadi 1 and 16 July is the 32nd and last
    day of Aani.
    """
    def date_on(day: int, month: int, hour: int = 9) -> tuple[str, int]:
        p = pg.compute(_utc(datetime(2026, month, day, hour)), *CHENNAI)
        return p.tamil_month_name.en, p.tamil_day

    assert date_on(13, 1) == ("Margazhi", 29)
    assert date_on(14, 1) == ("Thai", 1)      # sankranti before sunset
    assert date_on(15, 1) == ("Thai", 2)
    assert date_on(16, 7) == ("Aani", 32)     # Aani really has 32 days in 2026
    assert date_on(17, 7) == ("Aadi", 1)      # sankranti after sunset
    # And before sunrise on the 17th the previous Jyotish day is still running.
    assert date_on(17, 7, hour=3) == ("Aani", 32)


def test_the_ayana_turns_on_its_own_rule_not_the_months():
    """They coincide only when the sankranti misses the daylight hours.

    The Tamil month follows the sunset rule; the ayana follows the Sun's rasi at
    daybreak. On 14 January 2026 those disagree -- it is Thai 1 and still
    Dakshinayanam -- which is exactly what Drik Panchang prints. Deriving the
    ayana from the month would have made it Uttarayanam a day early.
    """
    fourteenth = pg.compute(_utc(datetime(2026, 1, 14, 9)), *CHENNAI)
    fifteenth = pg.compute(_utc(datetime(2026, 1, 15, 9)), *CHENNAI)

    assert (fourteenth.tamil_month_name.en, fourteenth.tamil_day) == ("Thai", 1)
    assert fourteenth.ayana_name.en == "Dakshinayana"
    assert fifteenth.ayana_name.en == "Uttarayana"


def test_every_limb_contains_the_moment_it_was_computed_for(reference):
    moment = _utc(REFERENCE_DAY)
    for limb in (reference.tithi, reference.nakshatra, reference.yoga,
                 reference.karana):
        assert limb.start <= moment < limb.end, limb
        assert 0.0 <= limb.elapsed < 1.0


def test_limb_durations_are_the_right_order_of_magnitude(reference):
    """A karana is half a tithi; nakshatra and yoga are each about a day."""
    assert timedelta(hours=19) < reference.tithi.duration < timedelta(hours=27)
    assert reference.karana.duration < reference.tithi.duration
    assert timedelta(hours=19) < reference.nakshatra.duration < timedelta(hours=28)
    assert timedelta(hours=17) < reference.yoga.duration < timedelta(hours=25)


# --- properties of the limbs -------------------------------------------------


def test_tithi_and_karana_do_not_depend_on_the_ayanamsa():
    """They are differences of two longitudes, so the ayanamsa cancels exactly.

    This is not a rounding claim — it is algebraic, and asserting it stops
    someone "fixing" the tithi by feeding it sidereal values in one place and
    tropical in another.
    """
    lahiri = pg.compute(_utc(REFERENCE_DAY), *CHENNAI, ay.Ayanamsa.LAHIRI)
    raman = pg.compute(_utc(REFERENCE_DAY), *CHENNAI, ay.Ayanamsa.RAMAN)
    assert lahiri.tithi.index == raman.tithi.index
    assert lahiri.karana.index == raman.karana.index
    assert abs((lahiri.tithi.end - raman.tithi.end).total_seconds()) < 1.0


def test_nakshatra_and_yoga_do_depend_on_the_ayanamsa():
    """The complement of the test above, and the reason it matters.

    A yoga is the *sum* of two longitudes, so the ayanamsa enters twice —
    computing it from tropical values is about 48 degrees out, three and a half
    yogas. Raman differs from Lahiri by roughly 1.2 degrees, which is enough to
    move the yoga boundary by hours.
    """
    lahiri = pg.compute(_utc(REFERENCE_DAY), *CHENNAI, ay.Ayanamsa.LAHIRI)
    raman = pg.compute(_utc(REFERENCE_DAY), *CHENNAI, ay.Ayanamsa.RAMAN)
    assert abs((lahiri.yoga.end - raman.yoga.end).total_seconds()) > 600.0
    assert abs((lahiri.nakshatra.end - raman.nakshatra.end).total_seconds()) > 600.0


def test_the_paksha_follows_the_tithi_number(reference):
    assert (reference.tithi.index < 15) == (reference.paksha == 0)


# --- the sunrise day boundary ------------------------------------------------


def test_a_birth_before_sunrise_belongs_to_the_previous_weekday():
    """The Jyotish day starts at sunrise, not midnight.

    A child born at 03:00 on a Tuesday is born on Monday's vaara, and Monday's
    rahu kalam is the one that applied. Consumer apps get this wrong constantly,
    and it silently shifts every window in the module.
    """
    before = pg.compute(_utc(datetime(2026, 8, 11, 3, 0)), *CHENNAI)
    after = pg.compute(_utc(datetime(2026, 8, 11, 9, 0)), *CHENNAI)
    assert before.vaara == 1 and before.vaara_name.en == "Monday"
    assert after.vaara == 2 and after.vaara_name.en == "Tuesday"
    # And the windows come from the previous day's sunrise/sunset pair.
    assert before.sun.rising < _utc(datetime(2026, 8, 11, 0, 0))


def test_the_vaara_is_the_weekday_of_the_day_its_sunrise_falls_in():
    assert dl.vaara_of(date(2026, 8, 9)) == 0    # Sunday
    assert dl.vaara_of(date(2026, 8, 10)) == 1   # Monday
    assert dl.vaara_of(date(2026, 8, 15)) == 6   # Saturday


def test_the_vaara_takes_a_local_date_not_an_instant():
    """Guards the double-counting bug this replaced.

    Deriving the weekday from a UTC instant is wrong east of Greenwich: 03:00
    IST is 22:00 UTC on the *previous* UTC date, so a "step back one day for
    before sunrise" rule lands two days back. It happened to give the right
    answer for India, which is the worst kind of wrong.
    """
    pre_dawn_ist = datetime(2026, 8, 11, 3, 0)          # Tuesday, before sunrise
    as_utc = _utc(pre_dawn_ist)
    assert as_utc.date() == date(2026, 8, 10)           # a different UTC date
    assert pg.compute(as_utc, *CHENNAI).vaara == 1      # still Monday's vaara


# --- high latitude -----------------------------------------------------------


def test_the_midnight_sun_is_reported_rather_than_invented():
    """Tromso in June has no sunrise, and a fabricated 06:00 would be a lie."""
    rs = dl.sun_rise_set(69.6492, 18.9553,
                         dl.local_midnight_utc(date(2026, 6, 21), ZoneInfo("Europe/Oslo")))
    assert rs.condition == "always_up"
    assert rs.rising is None and rs.setting is None
    assert not rs.has_daylight
    assert rs.day_length is None


def test_the_polar_night_is_reported_too():
    rs = dl.sun_rise_set(69.6492, 18.9553,
                         dl.local_midnight_utc(date(2026, 12, 21), ZoneInfo("Europe/Oslo")))
    assert rs.condition == "always_down"
    assert rs.rising is None


def test_a_panchangam_without_daylight_omits_the_windows_it_cannot_define():
    """Rahu kalam is a fraction of the daylight interval. With no daylight there
    is no such fraction, so the honest answer is nothing rather than a guess."""
    p = pg.compute(_utc(datetime(2026, 6, 21, 12, 0), ZoneInfo("Europe/Oslo")),
                   69.6492, 18.9553, "Europe/Oslo")
    assert not p.has_daylight
    assert p.rahu_kalam is None
    assert p.yamagandam is None
    assert p.kuligai is None
    assert p.gowri_day == ()
    assert p.nalla_neram == ()
    # The limbs are longitudes and do not care about the horizon.
    assert 0 <= p.tithi.index < 30
    assert 0 <= p.nakshatra.index < 27


def test_a_day_with_daylight_still_works_at_high_latitude():
    p = pg.compute(_utc(datetime(2026, 3, 15, 12, 0), ZoneInfo("Europe/Oslo")),
                   69.6492, 18.9553, "Europe/Oslo")
    assert p.has_daylight
    assert p.rahu_kalam is not None
    assert len(p.gowri_day) == 8


# --- cross-validation --------------------------------------------------------


def test_the_five_limbs_match_jyotishganit(jg, reference):
    """Names, against an implementation with its own ephemeris and ayanamsa."""
    local = REFERENCE_DAY
    offset = 5.5
    ayan = ay.compute(
        __import__("jyotish.core.birthdata", fromlist=["civil_to_time"])
        .civil_to_time(_utc(local)),
        ay.Ayanamsa.LAHIRI,
    )

    theirs_tithi = jg.calculate_tithi(local, offset)
    ours_tithi = (
        f"{'Shukla' if reference.paksha == 0 else 'Krishna'} "
        f"{reference.tithi.name.en}"
    )
    # Their list spells the two moon tithis without a paksha word.
    if reference.tithi.index in (14, 29):
        ours_tithi = reference.tithi.name.en
    assert theirs_tithi == ours_tithi

    assert jg.calculate_yoga(local, offset, ayan) == reference.yoga.name.en
    assert jg.calculate_karana(local, offset) == reference.karana.name.en
    assert (
        jg.calculate_nakshatra(local, offset, ayan)
        == NAKSHATRAS[reference.nakshatra.index].en
    )


def test_we_deliberately_disagree_with_jyotishganit_about_the_weekday(jg):
    """They take the vaara from the civil date; we take it from sunrise.

    Asserted rather than tolerated, so that "matching the reference" can never
    become an argument for removing the sunrise rule. Tamil almanacs are explicit
    that the day turns at sunrise, and a 03:00 birth is the case that shows it.
    """
    before_sunrise = datetime(2026, 8, 11, 3, 0)
    assert jg.calculate_vaara(before_sunrise) == "Tuesday"

    ours = pg.compute(_utc(before_sunrise), *CHENNAI)
    assert ours.vaara_name.en == "Monday"
