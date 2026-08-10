"""pytest configuration.

Its one job is to turn a wrong-interpreter run into a readable message.

Without this, running the suite under the system Python produces four separate
collection errors, each a `ModuleNotFoundError` with a traceback through
importlib, and none of them mentioning the virtualenv. That is a genuinely
confusing first experience, and it is the most likely way for a newcomer to this
repo to get stuck.
"""

from __future__ import annotations

import pytest

import _env


def pytest_configure(config: pytest.Config) -> None:
    missing = _env.missing_packages()
    if missing:
        # pytest.exit stops before collection, so the diagnostic is the only
        # thing printed rather than being buried under import tracebacks.
        pytest.exit(_env.dependency_error(missing), returncode=1)
