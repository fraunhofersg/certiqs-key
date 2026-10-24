"""The platform-keyed pin helper behaves as its rule reads.

Pins are keyed by platform: exact wherever a value was recorded on that
platform; a new platform records its own pins. So: a recorded
value is compared exactly and a mismatch fails, and an unrecorded platform,
case or field skips with a message that says how to record it.
"""

from __future__ import annotations

import platform
import re

import pytest
from tests.support import platform_pins
from tests.support.platform_pins import PinTable, assert_pinned

TABLE: PinTable = {
    "Recorded-x86-blas": {
        "case": {"objective": "0x1.8p+0", "gap": "0x1.0p-10"},
        "partial": {"objective": "0x1.8p+0"},
    },
}
OBSERVED = {"objective": "0x1.8p+0", "gap": "0x1.0p-10"}


def _on(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    monkeypatch.setattr(platform_pins, "platform_key", lambda: key)


def test_a_recorded_platform_compares_exactly(monkeypatch: pytest.MonkeyPatch) -> None:
    _on(monkeypatch, "Recorded-x86-blas")
    assert_pinned(TABLE, "case", OBSERVED, where="TABLE")
    with pytest.raises(AssertionError, match=re.escape("pinned '0x1.0p-10'")):
        assert_pinned(
            TABLE, "case", {**OBSERVED, "gap": "0x1.0000000000001p-10"}, where="TABLE"
        )


def test_an_unrecorded_platform_skips_with_the_values_to_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _on(monkeypatch, "Other-arm64-accelerate")
    with pytest.raises(pytest.skip.Exception) as failed:
        assert_pinned(TABLE, "case", OBSERVED, where="tests/x.py, TABLE")
    message = str(failed.value)
    assert "no bit-for-bit pins are recorded" in message
    assert "'Other-arm64-accelerate'" in message
    assert "tests/x.py, TABLE" in message
    assert "'objective': '0x1.8p+0'" in message


def test_an_unrecorded_field_skips_after_the_recorded_ones_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _on(monkeypatch, "Recorded-x86-blas")
    with pytest.raises(pytest.skip.Exception) as failed:
        assert_pinned(TABLE, "partial", OBSERVED, where="TABLE")
    message = str(failed.value)
    assert "no pin recorded for ['gap']" in message
    assert "the recorded fields matched" in message
    # A recorded field that differs is the failure, before any recording hint.
    with pytest.raises(AssertionError):
        assert_pinned(
            TABLE, "partial", {**OBSERVED, "objective": "0x1.9p+0"}, where="TABLE"
        )


def test_the_key_names_system_machine_and_blas() -> None:
    key = platform_pins.platform_key()
    assert key.startswith(f"{platform.system()}-{platform.machine()}-")
    assert key.split("-", 2)[2]
