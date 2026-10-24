"""BBM92's selectable acceptance maps, the pattern of decoy BB84's own.

Each map compiles; each is a function of the public transcript and a
coarse-graining of the default ``pair-resolved`` map; generation publishes no
key bit under any of them; and the honest statistics of a coarse map are the
honest statistics of the default map summed over the grouped values. The
default is the map a BBM92 run declares, transcript for transcript.

The maps are the template's (``instances/bbm92/protocol.yaml``): the
instance's ``acceptance_label`` is read off the compiled acceptance statistic,
and ``ACCEPTANCE_MAPS`` and ``DEFAULT_ACCEPTANCE_MAP`` are written out below as
the expectation the template's table is held to.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from instances.bbm92.surface import PARAMETERS, default_config, preparation

from certiqs_key.runs.errors import RunInputValueError
from certiqs_key.runs.pipeline import Preparation

#: The acceptance maps BBM92 declares, in the table's order, named as decoy
#: BB84 names its own; every one is a function of the public transcript.
ACCEPTANCE_MAPS = ("merged-discard", "announcement-resolved", "pair-resolved")
#: The default map.
DEFAULT_ACCEPTANCE_MAP = "pair-resolved"

_PREPARED: dict[str, Preparation] = {}


def _prepared(acceptance_map: str) -> Preparation:
    if acceptance_map not in _PREPARED:
        config = default_config()
        config = config.with_(
            device={**config.device, "acceptance_map": acceptance_map}
        )
        outcome = preparation(config)
        assert isinstance(outcome, Preparation), outcome
        _PREPARED[acceptance_map] = outcome
    return _PREPARED[acceptance_map]


def acceptance_label(
    first: str, second: str, passing: bool, acceptance_map: str
) -> str:
    """Return the acceptance value of one transcript ``(first, second)``.

    Read off the compiled declaration's acceptance statistic under
    ``acceptance_map``; ``passing`` (whether the transcript passes sifting) is
    checked against the declaration rather than taken on trust.
    """
    statistic = _prepared(acceptance_map).declaration.accept_statistic_general
    assert statistic is not None
    value = statistic[(first, second)]
    assert (value == "gen") is passing, (first, second, value)
    return value


def _honest(outcome: Preparation) -> dict[str, Fraction]:
    declaration = outcome.declaration
    raw = outcome.raw_joint_distribution
    assert raw is not None
    honest = dict.fromkeys(declaration.acceptance_alphabet, Fraction(0))
    for (x, v), probability in raw.items():
        honest[declaration.acceptance_value(declaration.announcement(x, v))] += (
            probability
        )
    return honest


def test_the_default_is_the_map_every_earlier_run_declared() -> None:
    """``pair-resolved``: ``gen`` for a sifted class, ``first|second`` else."""
    assert DEFAULT_ACCEPTANCE_MAP == "pair-resolved"
    assert default_config().device["acceptance_map"] == "pair-resolved"
    spec = next(row for row in PARAMETERS if row.name == "acceptance_map")
    assert tuple(name for name, _ in spec.domain.options) == ACCEPTANCE_MAPS
    declaration = _prepared("pair-resolved").declaration
    statistic = declaration.accept_statistic_general
    assert statistic is not None
    for (first, second), value in statistic.items():
        passing = first in ("gen:Z", "gen:X") and second == first[len("gen:") :]
        assert value == ("gen" if passing else f"{first}|{second}")
    assert len(declaration.acceptance_alphabet) == 79


@pytest.mark.parametrize("acceptance_map", ACCEPTANCE_MAPS)
def test_each_map_compiles_and_is_a_coarsening_of_the_transcript(
    acceptance_map: str,
) -> None:
    """A function of the public transcript, factoring through the default."""
    declaration = _prepared(acceptance_map).declaration
    statistic = declaration.accept_statistic_general
    finest = _prepared("pair-resolved").declaration.accept_statistic_general
    assert statistic is not None and finest is not None
    assert set(statistic) == set(finest)
    grouping: dict[str, str] = {}
    for transcript, value in statistic.items():
        assert grouping.setdefault(finest[transcript], value) == value
    for x, v in declaration.outcome_pairs():
        transcript = declaration.announcement(x, v)
        assert declaration.acceptance_value(transcript) == statistic[transcript]
    assert statistic[("gen:Z", "Z")] == statistic[("gen:X", "X")] == "gen"


def test_the_coarse_maps_group_test_rounds_by_basis_pair() -> None:
    """The labels the README documents, read off the label function."""
    for coarse in ("merged-discard", "announcement-resolved"):
        assert acceptance_label("test:H", "H", False, coarse) == "test-Z-ok"
        assert acceptance_label("test:H", "V", False, coarse) == "test-Z-error"
        assert acceptance_label("test:D", "D", False, coarse) == "test-X-ok"
        assert acceptance_label("test:A", "D", False, coarse) == "test-X-error"
    assert acceptance_label("test:H", "D", False, "announcement-resolved") == (
        "test-Z-X"
    )
    assert acceptance_label("test:nc", "mc", False, "announcement-resolved") == (
        "test-nc-mc"
    )
    assert acceptance_label("gen:Z", "X", False, "announcement-resolved") == ("gen:Z|X")
    for transcript in (("test:H", "D"), ("test:nc", "H"), ("gen:Z", "X")):
        assert acceptance_label(*transcript, False, "merged-discard") == "disc"
    assert set(_prepared("merged-discard").declaration.acceptance_alphabet) == {
        "gen",
        "disc",
        "test-Z-ok",
        "test-Z-error",
        "test-X-ok",
        "test-X-error",
    }
    with pytest.raises(RunInputValueError, match="acceptance_map is 'finest'"):
        acceptance_label("gen:Z", "Z", True, "finest")


@pytest.mark.parametrize("acceptance_map", ACCEPTANCE_MAPS)
def test_generation_announces_no_key_bit(acceptance_map: str) -> None:
    """A generation round's transcript, hence its value, hides Alice's bit."""
    declaration = _prepared(acceptance_map).declaration
    by_transcript: dict[tuple[str, ...], set[object]] = {}
    for x, v in declaration.outcome_pairs():
        transcript = declaration.announcement(x, v)
        if (
            transcript[0].startswith("gen:")
            and declaration.acceptance_value(transcript) == "gen"
        ):
            by_transcript.setdefault(transcript, set()).add(declaration.key_map[x, v])
    assert by_transcript
    assert all(bits == {0, 1} for bits in by_transcript.values())


@pytest.mark.parametrize("acceptance_map", ACCEPTANCE_MAPS)
def test_honest_statistics_are_the_default_ones_summed_over_each_group(
    acceptance_map: str,
) -> None:
    """Coarse honest frequencies are the fine ones summed, exactly."""
    coarse = _prepared(acceptance_map)
    fine = _prepared("pair-resolved")
    coarse_statistic = coarse.declaration.accept_statistic_general
    fine_statistic = fine.declaration.accept_statistic_general
    assert coarse_statistic is not None and fine_statistic is not None
    grouping = {
        fine_statistic[transcript]: value
        for transcript, value in coarse_statistic.items()
    }
    expected = dict.fromkeys(coarse.declaration.acceptance_alphabet, Fraction(0))
    for value, probability in _honest(fine).items():
        expected[grouping[value]] += probability
    honest = _honest(coarse)
    assert honest == expected
    assert sum(honest.values()) == 1
    assert honest["gen"] > 0
