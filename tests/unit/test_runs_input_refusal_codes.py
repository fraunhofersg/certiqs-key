"""The run tier's input refusals carry one closed vocabulary of codes.

A consumer must not have to show the exception class name as the reason or
tell input errors apart by the module that raised them. Every input check a
caller reaches before a run raises a
:class:`~certiqs_key.runs.errors.RunInputError` whose ``reason`` is a member of
:class:`~certiqs_key.runs.errors.RunInputReason`.

What is held here:

* every code is raised by at least one REAL input path -- an instance's
  ``default_config`` or ``preparation``, or the run tier's public preparation
  and configuration functions -- and no code exists that nothing raises;
* each code's error is still the builtin its check raised before the codes
  existed, so ``except KeyError`` / ``except ValueError`` keep working;
* the vocabulary is closed: no input-check site raises a bare builtin, no
  ``reason=`` is a string literal, and the table in ``instances/NOTES.md`` lists
  exactly the enum's members.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import math
import re
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path

import pytest

from certiqs_key.runs.config import (
    AdvancedSolverSettings,
    AlphaSearchSettings,
    RunConfig,
    SolverSettings,
    WarmStartSeed,
)
from certiqs_key.runs.errors import (
    RunInputError,
    RunInputKeyError,
    RunInputReason,
    RunInputTypeError,
    RunInputValueError,
)
from certiqs_key.runs.inputs import prepare_bound, prepare_probabilities
from certiqs_key.runs.iterate_file import load_warm_start, seed_of

ROOT = Path(__file__).resolve().parents[2]
R = RunInputReason


def _bb84(**overrides: object) -> RunConfig:
    from instances.bb84.surface import default_config

    return default_config(**overrides)


def _bb84_prepare(section: str, values: dict[str, object]) -> object:
    """Run bb84's preparation on its default config with one section replaced."""
    from instances.bb84.surface import preparation

    config = _bb84()
    return preparation(dataclasses.replace(config, **{section: values}))


def _bb84_device(**changes: object) -> object:
    return _bb84_prepare("device", {**_bb84().device, **changes})


def _optical_device(**changes: object) -> object:
    from instances.optical_bb84.surface import default_config, preparation

    config = default_config()
    return preparation(dataclasses.replace(config, device={**config.device, **changes}))


def _seed_file(tmp_path: Path, payload: object) -> WarmStartSeed:
    path = tmp_path / "final-iterate.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return seed_of(path)


def _wrong_hash(tmp_path: Path) -> object:
    seed = _seed_file(tmp_path, {"kind": "joint-final-iterate"})
    return load_warm_start(dataclasses.replace(seed, sha256="0" * 64))


def _not_an_iterate(tmp_path: Path) -> object:
    return load_warm_start(_seed_file(tmp_path, {"kind": "something-else"}))


#: code -> (the builtin its error also is, a real input path that raises it).
PATHS: dict[RunInputReason, tuple[type[Exception], Callable[[Path], object]]] = {
    # The instance's parameter table (runs.surface.check_keys).
    R.UNKNOWN_PARAMETER: (
        KeyError,
        lambda _: _bb84_prepare("model", {"qber": Fraction(0), "extra": 0}),
    ),
    R.MISSING_PARAMETER: (KeyError, lambda _: _bb84_prepare("model", {})),
    R.WRONG_KIND: (ValueError, lambda _: _optical_device(efficiency=Fraction(1))),
    R.NOT_AN_INTEGER: (
        ValueError,
        lambda _: _optical_device(photon_cutoff=Fraction(3, 2)),
    ),
    R.OUTSIDE_DOMAIN: (ValueError, lambda _: _bb84_prepare("model", {"qber": 1})),
    R.PORT_LABELS_MISMATCH: (
        KeyError,
        lambda _: _optical_device(efficiency={"not-a-port": Fraction(1)}),
    ),
    # Reading one number (runs.inputs).
    R.NOT_A_NUMBER: (TypeError, lambda _: _bb84(model={"qber": True})),
    R.UNREADABLE_NUMBER: (ValueError, lambda _: _bb84(model={"qber": "abc"})),
    R.NOT_FINITE: (ValueError, lambda _: _bb84(model={"qber": math.nan})),
    R.OUTSIDE_BINARY64: (
        ValueError,
        lambda _: _bb84(declared_tolerance=Fraction(10**400)),
    ),
    # Preparing a probability family or bound (runs.inputs).
    R.PROBABILITY_FAMILY_EMPTY: (
        ValueError,
        lambda _: prepare_probabilities(
            [], tolerance=0.0, lattice_exponent=24, site="empty"
        ),
    ),
    R.PROBABILITY_OUTSIDE_UNIT_INTERVAL: (
        ValueError,
        lambda _: _bb84_device(alice_z=Fraction(2), alice_x=Fraction(-1)),
    ),
    R.NORMALIZATION_EXCEEDS_TOLERANCE: (
        ValueError,
        lambda _: _bb84_device(alice_z=Fraction(1, 2), alice_x=Fraction(1, 4)),
    ),
    R.POSITIVE_SUPPORT_LOST: (
        ValueError,
        lambda _: prepare_probabilities(
            [Fraction(1, 2**60), 1 - Fraction(1, 2**60)],
            tolerance=0.0,
            lattice_exponent=24,
            site="tiny",
        ),
    ),
    R.PREPARATION_ARGUMENT_INVALID: (
        ValueError,
        lambda _: prepare_bound(
            Fraction(1, 2), direction="lower", lattice_exponent=99, site="b"
        ),
    ),
    # The configuration record (runs.config).
    R.DECLARED_TOLERANCE_ABSENT: (
        ValueError,
        lambda _: RunConfig(
            rounds=1_000,
            completeness_budget=Fraction(1, 1_000),
            parameters=_bb84().parameters,
        ),
    ),
    R.DECLARED_TOLERANCE_NOT_BINARY64: (
        ValueError,
        lambda _: dataclasses.replace(_bb84(), declared_tolerance=0),
    ),
    R.DECLARED_TOLERANCE_OUT_OF_DOMAIN: (
        ValueError,
        lambda _: _bb84(declared_tolerance=1.5),
    ),
    R.ENDPOINT_RULE_NOT_ADMITTED: (
        ValueError,
        lambda _: _bb84(endpoint_rule="no-such-rule"),
    ),
    R.TAIL_EVALUATION_NOT_ADMITTED: (
        ValueError,
        lambda _: _bb84(tail_evaluation="no-such-evaluation"),
    ),
    # A-AUTH's two run inputs (record schema 0.20.0).
    R.AUTHENTICATION_PARAMETER_OUT_OF_DOMAIN: (
        ValueError,
        lambda _: _bb84(eps_auth=1.0),
    ),
    # The snap run parameters (record schema 0.28.0): a setting that is not a
    # boolean.
    R.SNAP_SETTING_OUT_OF_DOMAIN: (
        ValueError,
        lambda _: _bb84(strict_snaps="yes"),
    ),
    # The check of the acceptance set against the feasible statistics (record
    # schema 0.37.0): an option that is neither on nor off.
    R.STATISTICS_CHECK_SETTING_OUT_OF_DOMAIN: (
        ValueError,
        lambda _: _bb84(statistics_check="sometimes"),
    ),
    # A configuration payload naming a retired run parameter (record schema
    # 0.29.0).
    R.RETIRED_PARAMETER: (
        ValueError,
        lambda _: RunConfig.from_payload(
            {
                **_bb84().to_payload(),
                "parameters": {
                    **_bb84().to_payload()["parameters"],
                    "certify_snaps": True,
                },
            }
        ),
    ),
    R.SOLVER_BUDGET_NOT_POSITIVE: (
        ValueError,
        lambda _: SolverSettings(max_iterations=0),
    ),
    R.SOLVER_GAP_TOLERANCE_NOT_POSITIVE: (
        ValueError,
        lambda _: AdvancedSolverSettings(gap_tolerance=0.0),
    ),
    R.SOLVER_ORACLE_NOT_ADMITTED: (
        ValueError,
        lambda _: AdvancedSolverSettings(oracle="no-such-oracle"),
    ),
    R.SOLVER_CERTIFIED_EVALUATION_NOT_ADMITTED: (
        ValueError,
        lambda _: AdvancedSolverSettings(certified_evaluation="sometimes"),
    ),
    R.SOLVER_METHOD_NOT_ADMITTED: (
        ValueError,
        lambda _: SolverSettings(method="no-such-method"),
    ),
    # The two tiers of the solver settings (record schema 0.43.0).
    R.SOLVER_METHOD_SET_TWICE: (
        ValueError,
        lambda _: SolverSettings(
            method="auto", advanced=AdvancedSolverSettings(method="factor")
        ),
    ),
    R.SOLVER_KEY_NOT_ADMITTED: (
        ValueError,
        lambda _: RunConfig.from_payload(
            {**_bb84().to_payload(), "solver": {"oracle": "spectral"}}
        ),
    ),
    # The opt-in outer alpha search (record schema 0.24.0).
    R.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN: (
        ValueError,
        lambda _: AlphaSearchSettings(lower=0.2, upper=0.1),
    ),
    R.ALPHA_AND_ALPHA_SEARCH_BOTH_SET: (
        ValueError,
        lambda _: _bb84(alpha=1.01, alpha_search=AlphaSearchSettings()),
    ),
    # A warm-start seed (runs.config.WarmStartSeed, runs.iterate_file).
    R.WARM_START_HASH_MALFORMED: (
        ValueError,
        lambda _: WarmStartSeed(file="seed.json", sha256="not-a-hash"),
    ),
    R.WARM_START_FILE_MISSING: (
        ValueError,
        lambda tmp: seed_of(tmp / "no-such-directory" / "final-iterate.json"),
    ),
    R.WARM_START_HASH_MISMATCH: (ValueError, _wrong_hash),
    R.WARM_START_NOT_AN_ITERATE: (ValueError, _not_an_iterate),
}

_CLASS_OF = {
    KeyError: RunInputKeyError,
    ValueError: RunInputValueError,
    TypeError: RunInputTypeError,
}


def test_every_code_has_a_real_input_path_and_every_path_a_code() -> None:
    """No code nothing raises, and no path below is about a code that is gone."""
    assert set(PATHS) == set(RunInputReason)


@pytest.mark.parametrize("reason", list(RunInputReason), ids=str)
def test_each_code_is_raised_by_its_input_path(
    reason: RunInputReason, tmp_path: Path
) -> None:
    """The code, the family, and the builtin a plain ``except`` still catches."""
    builtin, path = PATHS[reason]
    with pytest.raises(builtin) as caught:
        path(tmp_path)
    error = caught.value
    assert isinstance(error, RunInputError)
    assert isinstance(error, _CLASS_OF[builtin])
    assert error.reason is reason
    # The message is the human half: plain text, never the builtin's repr
    # (a KeyError would otherwise render it quoted).
    assert error.message
    assert str(error) == error.message


def test_a_code_outside_the_vocabulary_cannot_be_raised() -> None:
    with pytest.raises(ValueError, match="not_a_code"):
        RunInputValueError("message", reason="not_a_code")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  The vocabulary is closed: every raise site at an input check is coded
# ---------------------------------------------------------------------------

#: The input-check sites a caller reaches before a run: whole modules, or
#: named functions of a module that also holds other code. ``None`` means the
#: whole module.
INPUT_CHECK_SITES: dict[str, frozenset[str] | None] = {
    "src/certiqs_key/runs/inputs.py": None,
    "src/certiqs_key/runs/config.py": None,
    "src/certiqs_key/runs/surface.py": frozenset(
        {"check_keys", "_check_scalar", "_check_per_port"}
    ),
    "src/certiqs_key/runs/iterate_file.py": frozenset({"seed_of", "load_warm_start"}),
    # The packaged instances' configuration reader:
    # the document surface's, whose own refusals are the run tier's codes or
    # the document layer's (instances/declared/errors.py).
    "instances/declared/surface.py": frozenset(
        {"default_config", "_derive", "_configured", "_environment", "resolve"}
    ),
}

_BUILTINS = {"KeyError", "ValueError", "TypeError", "LookupError", "Exception"}


def _raises(tree: ast.AST) -> list[ast.Raise]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Raise)]


def _raised_name(node: ast.Raise) -> str | None:
    exc = node.exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    return exc.id if isinstance(exc, ast.Name) else None


@pytest.mark.parametrize("relative", sorted(INPUT_CHECK_SITES))
def test_no_input_check_raises_a_bare_builtin(relative: str) -> None:
    """A bare ``raise ValueError`` at an input check is a code nobody named."""
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    functions = INPUT_CHECK_SITES[relative]
    scopes: list[ast.AST] = (
        [tree]
        if functions is None
        else [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name in functions
        ]
    )
    if functions is not None:
        assert {node.name for node in scopes} == functions, relative  # type: ignore[attr-defined]
    bare = [
        f"{relative}:{node.lineno}"
        for scope in scopes
        for node in _raises(scope)
        if _raised_name(node) in _BUILTINS
    ]
    assert not bare


#: Every class of the family a raise site names. Another module's own
#: vocabulary (a ``SnapRefusedError`` reason, turned into an adapter refusal
#: outcome) is not this one.
_FAMILY = {
    "RunInputError",
    "RunInputKeyError",
    "RunInputValueError",
    "RunInputTypeError",
    "RunConfigError",
    "WarmStartFileError",
}


def test_every_reason_is_a_member_never_a_string_literal() -> None:
    """``reason="..."`` would reopen the vocabulary one call site at a time."""
    offenders = []
    for base in ("src/certiqs_key/runs", "instances"):
        for path in sorted((ROOT / base).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.id if isinstance(node.func, ast.Name) else ""
                if name not in _FAMILY:
                    continue
                for keyword in node.keywords:
                    if keyword.arg == "reason" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not offenders


def test_the_documented_table_lists_exactly_the_vocabulary() -> None:
    """The caller-facing table in ``instances/NOTES.md`` is this enum, no more."""
    text = (ROOT / "instances" / "NOTES.md").read_text(encoding="utf-8")
    section = text.split("## Input errors", 1)[1]
    documented = set(re.findall(r"^\| `([a-z0-9_]+)` \|", section, re.MULTILINE))
    assert documented == {str(member) for member in RunInputReason}


# ---------------------------------------------------------------------------
#  Completeness demands only what applies (the parameters' applies_when)
# ---------------------------------------------------------------------------


def _bbm92_without(model_key: str, source_model: str) -> RunConfig:
    from instances.bbm92.surface import default_config

    config = default_config()
    model = {k: v for k, v in config.model.items() if k != model_key}
    return dataclasses.replace(
        config,
        model=model,
        device={**config.device, "source_model": source_model},
    )


def _configuration(config: RunConfig) -> RunConfig:
    """Return bbm92's configuration as its reader reads it (key checks applied).

    The template's reader.
    """
    from tests.support.lowered_templates import lowered

    return lowered("bbm92", config)[0]


def test_an_inapplicable_parameter_is_not_demanded() -> None:
    """bbm92's mean_pairs has no effect under ideal_pair, so it may be absent."""
    config = _bbm92_without("mean_pairs", "ideal_pair")
    assert "mean_pairs" not in _configuration(config).model


def test_an_applicable_parameter_is_still_demanded() -> None:
    """Under the spdc model the same absence is refused as missing_parameter."""
    with pytest.raises(KeyError) as caught:
        _configuration(_bbm92_without("mean_pairs", "spdc"))
    assert isinstance(caught.value, RunInputError)
    assert caught.value.reason is R.MISSING_PARAMETER
    assert "mean_pairs" in str(caught.value)


def test_an_inapplicable_parameter_supplied_is_accepted_as_before() -> None:
    """Supplying visibility under spdc (where it has no effect) is not refused."""
    from instances.bbm92.surface import default_config

    config = default_config()
    spdc = dataclasses.replace(config, device={**config.device, "source_model": "spdc"})
    assert "visibility" in _configuration(spdc).model
