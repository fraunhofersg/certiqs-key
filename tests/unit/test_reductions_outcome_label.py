"""The one join of a joint outcome ``(y, t)``, and the probe-off spelling.

The probe setting of ``receiver/def:probe`` is an add-on: a probe-free
receiver declares ``T = {off}``, and its labels are its detection letters
alone. A probe-bearing declaration keeps ``y,t``. The mathematics
(``V = Y x T``) is the same in both cases; only the spelling differs.
"""

from __future__ import annotations

import pytest

from certiqs_key.receiver.settings import OFF_SETTING as RECEIVER_OFF_SETTING
from certiqs_key.reductions import docking
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    OFF_SETTING,
    outcome_label,
    probe_settings_of,
)


def test_the_off_setting_is_the_receivers_own_string() -> None:
    """The reductions package names the setting without importing the receiver."""
    assert OFF_SETTING == RECEIVER_OFF_SETTING


def test_a_probe_free_declaration_spells_the_detection_letter_alone() -> None:
    settings = (OFF_SETTING,)
    assert outcome_label(("H", OFF_SETTING), settings) == "H"
    assert outcome_label(("nc", OFF_SETTING), settings) == "nc"


def test_a_probe_bearing_declaration_keeps_the_setting_component() -> None:
    settings = (OFF_SETTING, "led")
    assert outcome_label(("H", OFF_SETTING), settings) == "H,off"
    assert outcome_label(("H", "led"), settings) == "H,led"
    # A single setting other than `off` is not the probe-free case either.
    assert outcome_label(("a", "t"), ("t",)) == "a,t"


def test_the_join_is_injective_on_a_declared_alphabet() -> None:
    for settings in ((OFF_SETTING,), (OFF_SETTING, "led"), ("t",)):
        alphabet = [(y, t) for t in settings for y in ("H", "V", "nc")]
        labels = [outcome_label(v, settings) for v in alphabet]
        assert len(set(labels)) == len(labels)


def test_a_setting_outside_the_declaration_is_refused() -> None:
    with pytest.raises(MalformedInputError, match="not one of the declared"):
        outcome_label(("H", "led"), (OFF_SETTING,))


def test_the_settings_are_read_off_the_declared_alphabet_in_order() -> None:
    alphabet = [("a", "t1"), ("b", "t1"), ("a", "t0"), ("b", "t0")]
    assert probe_settings_of(alphabet) == ("t1", "t0")
    assert probe_settings_of([("a", OFF_SETTING)]) == (OFF_SETTING,)


def test_the_docking_spells_through_the_same_function() -> None:
    assert docking.outcome_label is outcome_label
    assert docking.probe_settings_of is probe_settings_of
