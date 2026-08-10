"""Environment diagnostics for the developer entry points.

This module exists because of a real setup failure, and it is deliberately
dependency-free so it can still run when nothing else can.

The trap: you install into the virtualenv with an explicit interpreter path,
then run everything afterwards as plain ``python`` -- which is the *system*
interpreter, with none of the project's packages. What you get is::

    ModuleNotFoundError: No module named 'skyfield'

which says nothing about the actual cause. Worse, ``scripts/build_places_db.py``
uses only the standard library, so it runs perfectly under system Python and
makes the environment look correctly set up right before the next command fails.

So: detect the situation and say what to do about it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

#: services/jyotish -- the directory that must be on sys.path for `import
#: jyotish` to resolve, and the one holding .venv.
PROJECT_ROOT = Path(__file__).resolve().parent

#: Third-party packages the engine cannot start without.
REQUIRED_PACKAGES = ("skyfield", "numpy", "timezonefinder")


def in_virtualenv() -> bool:
    """True when running inside any virtualenv (the standard check)."""
    return sys.prefix != sys.base_prefix


def venv_python() -> Path | None:
    """Path to the project venv's interpreter, if it has been created."""
    for candidate in (
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
        PROJECT_ROOT / ".venv" / "bin" / "python",          # POSIX
    ):
        if candidate.exists():
            return candidate
    return None


def missing_packages() -> list[str]:
    """Which required packages are absent.

    Uses ``find_spec`` rather than importing, so this check cannot itself blow
    up on a half-installed environment.
    """
    missing = []
    for name in REQUIRED_PACKAGES:
        try:
            if importlib.util.find_spec(name) is None:
                missing.append(name)
        except (ImportError, ValueError):
            missing.append(name)
    return missing


def activation_help() -> str:
    """Per-shell activation instructions."""
    return (
        "  cmd.exe         .venv\\Scripts\\activate\n"
        "  PowerShell      .venv\\Scripts\\Activate.ps1\n"
        "  Git Bash        source .venv/Scripts/activate\n"
        "  macOS / Linux   source .venv/bin/activate"
    )


def dependency_error(missing: list[str] | None = None) -> str:
    """A diagnostic naming the interpreter actually in use and how to fix it."""
    missing = missing if missing is not None else missing_packages()
    expected = venv_python()

    lines = [
        "",
        "Project dependencies are missing: " + ", ".join(missing),
        "",
    ]

    if not in_virtualenv():
        lines.append("You are running the system Python, not the project virtualenv.")
    else:
        lines.append("You are in a virtualenv, but it does not have the packages installed.")

    lines += [
        "",
        f"  interpreter : {sys.executable}",
        f"  expected    : {expected}" if expected else
        "  expected    : .venv has not been created yet",
        "",
        f"From {PROJECT_ROOT}:",
        "",
    ]

    if expected is None:
        lines.append("  python -m venv .venv")

    lines += [
        activation_help(),
        "",
        "then:",
        "",
        "  python -m pip install -r requirements-dev.txt",
        "",
        "PowerShell may refuse to run the activation script. If so:",
        "  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned",
        "",
    ]
    return "\n".join(lines)


def ensure_dependencies() -> None:
    """Exit with a readable diagnostic if the environment is not usable.

    Called by the CLI entry points. pytest goes through ``conftest.py`` instead,
    so it can abort collection cleanly.
    """
    missing = missing_packages()
    if missing:
        sys.stderr.write(dependency_error(missing))
        raise SystemExit(1)
