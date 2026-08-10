"""End-to-end CLI behaviour, run as a real subprocess.

These run `scripts/chart.py` the way a user does, because several of the defects
they guard against only exist outside the interpreter: stdout encoding, sys.path
resolution, and argument validation. Importing the module would hide all three.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
CHART = ENGINE / "scripts" / "chart.py"

CHENNAI = ["--place", "Chennai", "--pick", "1"]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run the CLI with a deliberately non-UTF-8 stdout, capturing bytes.

    ``capture_output`` gives the child a pipe rather than a console, which is
    exactly the redirect case. PYTHONIOENCODING is cleared so the child falls
    back to the platform default -- cp1252 on this machine -- rather than
    inheriting a setting that would mask the bug.
    """
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, str(CHART), *args],
        capture_output=True, cwd=str(cwd or ENGINE), env=env, timeout=300,
    )


def test_redirected_output_does_not_crash(tmp_path: Path) -> None:
    """`chart.py ... > chart.txt` must produce a complete file.

    Tamil is printed regardless of --lang, and a redirected stdout on Windows
    defaults to the ANSI code page, which cannot encode it. This died with
    UnicodeEncodeError after six lines and left the file truncated -- precisely
    the redirect-and-compare workflow the script exists to support.
    """
    p = run("--date", "1990-05-15", "--time", "06:30", *CHENNAI, "--varga", "d1,d9")
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")

    text = p.stdout.decode("utf-8")
    assert "Lagna" in text
    assert "நவாம்சம்" in text, "Tamil missing from redirected output"
    # The full chart must be present, not a prefix ending at the first Tamil.
    assert text.count("kattam") == 2
    assert text.rstrip().endswith("+")


def test_runs_from_any_directory(tmp_path: Path) -> None:
    """sys.path is bootstrapped from __file__, not the working directory."""
    p = run("--date", "1990-05-15", "--time", "06:30", *CHENNAI, cwd=tmp_path)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    assert b"Lagna" in p.stdout


# --- birth time -------------------------------------------------------------

def _lagna_line(p: subprocess.CompletedProcess) -> str:
    for line in p.stdout.decode("utf-8").splitlines():
        if line.startswith("Lagna"):
            return line
    raise AssertionError("no Lagna line in output")


def test_twelve_and_twenty_four_hour_agree() -> None:
    a = run("--date", "1990-05-15", "--time", "6:30 PM", *CHENNAI)
    b = run("--date", "1990-05-15", "--time", "18:30", *CHENNAI)
    assert a.returncode == b.returncode == 0
    assert _lagna_line(a) == _lagna_line(b)


def test_am_pm_error_is_visible_in_the_header() -> None:
    """The echoed 12-hour reading is the user's chance to catch a slip."""
    p = run("--date", "1990-05-15", "--time", "06:30", *CHENNAI)
    assert "(6:30 AM)" in p.stdout.decode("utf-8")


def test_morning_and_evening_are_opposite_rasis() -> None:
    morning = _lagna_line(run("--date", "1990-05-15", "--time", "6:30 AM", *CHENNAI))
    evening = _lagna_line(run("--date", "1990-05-15", "--time", "6:30 PM", *CHENNAI))
    assert "Taurus" in morning and "Scorpio" in evening


@pytest.mark.parametrize("bad", ["13:30 PM", "25:00", "six thirty", "630"])
def test_unreadable_times_are_rejected_cleanly(bad: str) -> None:
    p = run("--date", "1990-05-15", "--time", bad, *CHENNAI)
    assert p.returncode != 0
    assert b"Traceback" not in p.stderr, "should be a clean error, not a crash"


# --- argument validation ----------------------------------------------------

def test_place_or_coordinates_required() -> None:
    p = run("--date", "1990-05-15", "--time", "06:30")
    assert p.returncode != 0
    assert b"--place" in p.stderr


def test_unknown_varga_is_rejected() -> None:
    p = run("--date", "1990-05-15", "--time", "06:30", *CHENNAI, "--varga", "d5")
    assert p.returncode != 0
    assert b"unknown varga" in p.stderr.lower()


def test_unknown_place_is_a_clean_message() -> None:
    p = run("--date", "1990-05-15", "--time", "06:30", "--place", "Zzzzqqqq")
    assert b"Traceback" not in p.stderr
    assert b"No place matching" in p.stdout + p.stderr


def test_pick_out_of_range_is_rejected() -> None:
    p = run("--date", "1990-05-15", "--time", "06:30", "--place", "Chennai",
            "--pick", "999")
    assert b"Traceback" not in p.stderr
    assert b"--pick" in p.stdout + p.stderr
