"""The compiler's and the transmitter's assumption bindings.

Values are bound per assumption: beside each row of
its ledger an emitter records the declared values the row's assumption's
clauses are about. The protocol compiler's ledger and the transmitter's are
tuples of bare machine keys, which frozen expectations pin, so the values
travel beside them as ``assumption_bindings`` (one entry per row, in the
ledger's order; :mod:`certiqs_key.domain.bindings` for the shape).

WHAT IS HELD HERE. The NAMES each row binds on every route, hand-written from
the claim each row states (``spec/modules/protocol-compiler/claims/ass-*.tex``,
``spec/modules/transmitter/claims/ass-*.tex``, ``transmitter/decoy/claims/
ass-wcp.tex``) and the route's declared facts; the VALUES, against the
declaration they are read from; the absence of A-LINK on Band A (``thm:band-a`` (v)
proves every clause of the identity link, and the theorem does not assume A-LINK); the
refusal, which binds nothing; and the run tier's join of the bindings onto the emitted
rows. No number of any result is read.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest
from instances.bb84.specification import (
    ConjugationConvention,
    bb84_specification,
    conjugation_example_specification,
)
from protocol_blocks import source_part
from route_fixtures import ROUTES, preparation, route_result

from certiqs_key.domain.bindings import is_immutable, ledger_bindings_record
from certiqs_key.foundations.exact import matrix, scale
from certiqs_key.protocol_compiler import compile_specification
from certiqs_key.protocol_compiler.compile import public_choice_declared
from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    INHERITED_KEYS,
)
from certiqs_key.protocol_compiler.spec import PublicChoices
from certiqs_key.runs.assumptions import emitted_rows
from certiqs_key.transmitter import (
    SourceReplacementCertificate,
    SourceSpecification,
    emit_artifact,
)
from certiqs_key.transmitter.reasons import SourceMode

pytestmark = pytest.mark.contract

#: Short id -> machine key, for every row the compiler's ledger may carry.
KEY: dict[str, str] = {
    **{str(identifier): key for identifier, key in ASSUMPTION_MACHINE_KEYS.items()},
    **INHERITED_KEYS,
}

#: THE NAMES EACH ROW BINDS, PER ROUTE, hand-written. The clause each name
#: comes from is ``compile._assumption_bindings``'s docstring and the
#: interface's ``assumption_ledger.binds``; what varies between routes is
#: which rows the ledger carries and the conditional names:
#:
#: * A-SPEC's ``alice_povm`` only where no source-replacement certificate is
#:   demanded (``ass:spec`` (i)): the untrusted two-station route;
#: * A-COIN's ``public_choices`` where a ``public_choices`` record is declared
#:   (Band A, the flat routes, a probe station), ``choice_weighting`` where a
#:   setting-dependent weighting is (two-station, a probe station);
#: * A-ATK's ``attack_set_license`` where one is supplied (licensed route);
#: * A-SEQ binds nothing; A-RECV is no row of the compiler's ledger on any
#:   route (its interface's ``assumption_ledger.a_recv_not_emitted_note``).
_SPEC = ("specification", "receiver_family")
_TRANSMITTER = {
    "A-ENS": ("source_ensemble",),
    "A-SEQ": (),
    "A-SRC": ("source_mode", "alice_marginal", "alice_povm"),
}
# There is no A-PRESENT on any route; A-LINK is omitted on the three one-station
# flat-instance routes, whose run passes chain_provenance (req:link-row-provenance
# (ii)), and kept on a branching route (no claim shows its read-off to be a
# compression).
_FLAT: dict[str, tuple[str, ...]] = {
    "A-SPEC": _SPEC,
    "A-RHOM": ("specification", "source_mode"),
    "A-COIN": ("public_choices", "specification"),
    **_TRANSMITTER,
}
EXPECTED_NAMES: dict[str, dict[str, tuple[str, ...]]] = {
    "band-a": {
        "A-SPEC": _SPEC,
        "A-RHOM": ("specification", "source_mode"),
        "A-COIN": ("public_choices", "specification"),
        # No A-LINK: thm:band-a (v) proves every clause of the identity link.
            "A-IDEAL": ("declared_povm", "transmitted_dim"),
        **_TRANSMITTER,
    },
    "wpfss-encoded": _FLAT,
    "wpfss-licensed": {
        **_FLAT,
        "A-ATK": (
            "constraint_entries",
            "source_mode",
            "reduction_chain",
            "attack_set_license",
        ),
    },
    "wpfss-no-window": _FLAT,
    "decoy": {
        "A-SPEC": _SPEC,
        "A-RHOM": ("specification", "source_mode"),
        "A-LINK": ("reduction_chain",),
        "A-WCP": (
            "signal_alphabet",
            "signal_weights",
            "intensities",
            "polarisations",
            "entropy_cutoff",
            "source_cutoff",
        ),
        "A-SEQ": (),
        "A-SRC": ("source_mode", "alice_marginal", "alice_povm"),
    },
    # One letter, so no A-ALICE-MEAS and no
    # alice_povm in A-SPEC; untrusted, so no A-ENS; both stations' links
    # discharged by the run's chain_provenance, so no A-LINK.
    "untrusted-two-station": {
        "A-SPEC": _SPEC,
        "A-RHOM": ("specification", "source_mode"),
        "A-COIN": ("choice_weighting", "specification"),
        "A-SEQ": (),
    },
}


def _bindings(route: str) -> dict[str, dict[str, object]]:
    """Return the route's compiled bindings as ``{short id: {name: value}}``."""
    compilation = preparation(route)[0].compilation
    short = {key: short_id for short_id, key in KEY.items()}
    return {
        short[key]: dict(bindings) for key, bindings in compilation.assumption_bindings
    }


@pytest.mark.parametrize("route", ROUTES)
def test_one_entry_per_ledger_row_in_its_order_and_immutable(route: str) -> None:
    """The bindings are the ledger's rows, in its order, each value immutable.

    The machine record writes the same entries as ``{key: {name: value}}``,
    in the same order (the ``assumption_bindings`` output row).
    """
    compilation = preparation(route)[0].compilation
    keys = tuple(key for key, _ in compilation.assumption_bindings)
    assert keys == compilation.assumption_ledger
    for key, bindings in compilation.assumption_bindings:
        assert is_immutable(bindings), (route, key)
        names = [name for name, _ in bindings]
        assert len(names) == len(set(names)), (route, key)
    record = compilation.as_machine_record()["assumption_bindings"]
    assert list(record) == list(compilation.assumption_ledger)
    assert record == ledger_bindings_record(compilation.assumption_bindings)


@pytest.mark.parametrize("route", ROUTES)
def test_each_row_binds_exactly_the_names_its_clauses_name(route: str) -> None:
    """Every row binds exactly the hand-written names, no more and no fewer."""
    bindings = _bindings(route)
    assert set(bindings) == set(EXPECTED_NAMES[route]), route
    for short_id, names in EXPECTED_NAMES[route].items():
        assert tuple(bindings[short_id]) == names, (route, short_id)


#: The routes whose run passes ``chain_provenance`` and whose compiler omits
#: A-LINK under req:link-row-provenance (ii), by hand.
_LINK_ROW_ON_PROVENANCE = (
    "wpfss-encoded",
    "wpfss-licensed",
    "wpfss-no-window",
    # Both stations' links discharged (per factor).
    "untrusted-two-station",
)


def test_a_link_is_not_emitted_on_band_a_s_identity_link() -> None:
    """Band A emits no A-LINK row and binds nothing for it.

    ``thm:band-a`` (v) proves that the identity link satisfies every clause
    of A-LINK and the theorem does not assume it; ``ass:link``'s lead-in
    says that on the Band-A identity link nothing is left to attest. The row
    is also omitted on an in-run single exact instance link
    (req:link-row-provenance (ii)). Off
    both the row is emitted and binds the chain.
    """
    assert "A-LINK" not in _bindings("band-a")
    for route in ROUTES:
        if route == "band-a":
            continue
        if route in _LINK_ROW_ON_PROVENANCE:
            assert "A-LINK" not in _bindings(route), route
        else:
            assert "reduction_chain" in dict(_bindings(route)["A-LINK"]), route


def test_the_band_a_values_are_the_declared_ones() -> None:
    """Each value is the declaration's own, read back off the specification."""
    specification = preparation("band-a")[0].specification
    bindings = _bindings("band-a")
    source = specification.source
    public = specification.public

    shape = dict(bindings["A-SPEC"]["specification"])  # type: ignore[arg-type]
    assert shape["alice_dim"] == source.alice_dim
    assert shape["signal_alphabet"] == tuple(source.alphabet)
    assert shape["transmitted_dim"] == source.transmitted_dim
    assert shape["key_holder"] == str(public.holder)
    assert shape["key_alphabet"] == tuple(public.key_alphabet)
    assert shape["acceptance_alphabet"] == tuple(public.acceptance_alphabet)
    assert bindings["A-RHOM"]["specification"] == bindings["A-SPEC"]["specification"]
    assert bindings["A-RHOM"]["source_mode"] == "trusted"

    # A-COIN (i): each declared record's T_pub and q_t, exact.
    records = bindings["A-COIN"]["public_choices"]
    declared = [source.alice_povm, specification.receiver.physical_povm]
    assert all(isinstance(record, PublicChoices) for record in declared)
    assert records == tuple(
        (
            ("party", str(record.party)),
            ("choices", tuple(record.choices)),
            (
                "weights",
                tuple(
                    (choice, str(record.weights[choice]))
                    for choice in record.choices
                ),
            ),
        )
        for record in declared
        if isinstance(record, PublicChoices)
    )

    # A-IDEAL (iii): the transmitted system.
    assert bindings["A-IDEAL"]["transmitted_dim"] == source.transmitted_dim

    # The transmitter's rows are the artefact's own, copied.
    artifact = dict(source.artifact.assumption_bindings)
    for short_id in ("A-ENS", "A-SEQ", "A-SRC"):
        assert tuple(bindings[short_id].items()) == artifact[KEY[short_id]]
    ensemble = dict(bindings["A-ENS"]["source_ensemble"])  # type: ignore[arg-type]
    assert ensemble["weights"] == tuple(
        (label, str(source.artifact.virtual_ensemble_weights[label]))
        for label in source.alphabet
    )


def test_alice_s_measurement_is_bound_only_where_no_certificate_is_demanded() -> None:
    """``ass:spec`` (i) and ``ass:alice-meas`` (i): untrusted, or ``d_A = 1``.

    Band A is trusted at ``d_A = 2``, where a certificate is demanded: neither
    row binds ``alice_povm``. The two-station route is untrusted: A-SPEC binds
    it and A-ALICE-MEAS binds it with the mode.
    """
    assert "alice_povm" not in _bindings("band-a")["A-SPEC"]
    # And only where X has at least two letters.
    # The two-station route is untrusted at one letter: neither row binds it.
    untrusted = _bindings("untrusted-two-station")
    source = preparation("untrusted-two-station")[0].specification.source
    assert len(source.alphabet) == 1
    assert "A-ALICE-MEAS" not in untrusted
    assert "alice_povm" not in untrusted["A-SPEC"]
    # At two letters, untrusted: both bind {M_x} (BB84 with the source untrusted).
    band_a = preparation("band-a")[0].specification
    two_letters = replace(
        band_a,
        source=source_part(
            alphabet=band_a.source.alphabet,
            alice_dim=band_a.source.alice_dim,
            alice_povm=band_a.source.alice_povm,
            transmitted_dim=band_a.source.transmitted_dim,
            signal_weights=band_a.source.signal_weights,
            signal_states=band_a.source.signal_states,
        ),
    )
    compiled = compile_specification(two_letters)
    assert compiled.refusal is None
    short = {key: short_id for short_id, key in KEY.items()}
    bound = {
        short[key]: dict(pairs) for key, pairs in compiled.assumption_bindings
    }
    assert bound["A-ALICE-MEAS"]["source_mode"] == "untrusted"
    assert bound["A-SPEC"]["alice_povm"] == bound["A-ALICE-MEAS"]["alice_povm"]
    assert dict(bound["A-ALICE-MEAS"]["alice_povm"])["alphabet"] == tuple(  # type: ignore[arg-type]
        two_letters.source.alphabet
    )


def test_a_atk_binds_the_licensed_list_its_mode_its_chain_and_its_licence() -> None:
    """``ass:atk`` (i) the list's tags and mode; (ii) the chain and its licence."""
    prepared = preparation("wpfss-licensed")[0]
    bindings = _bindings("wpfss-licensed")["A-ATK"]
    emitted = prepared.compilation.declaration.constraint_list
    assert emitted
    assert dict(bindings["constraint_entries"]) == {  # type: ignore[arg-type]
        "count": len(emitted),
        "rhs_tags": tuple(str(entry.tag) for entry in emitted),
    }
    assert bindings["source_mode"] == str(prepared.specification.source.source_mode)
    licence = prepared.specification.constraints.attack_set_license
    assert licence is not None
    assert bindings["attack_set_license"] == (("supplier", licence.supplier),)
    # The same chain shape A-LINK binds where its row is emitted: on this route
    # the run's chain_provenance omits that row (req:link-row-provenance
    # (ii)), so the chain is compared with a compilation that passes none.
    without = compile_specification(prepared.specification)
    link_row = dict(without.assumption_bindings)[KEY["A-LINK"]]
    assert bindings["reduction_chain"] == dict(link_row)["reduction_chain"]


def test_the_setting_dependent_weighting_binds_its_declared_matrix() -> None:
    """``ass:coin`` (ii): ``P(f | t)`` as declared, exact, ``"t|f"`` per cell."""
    specification = preparation("untrusted-two-station")[0].specification
    (weighted,) = (
        part for part in specification.receiver_parts if part.choice_weighting
    )
    weighting = weighted.choice_weighting
    assert weighting is not None
    (record,) = _bindings("untrusted-two-station")["A-COIN"]["choice_weighting"]  # type: ignore[misc]
    record = dict(record)
    # It names the factor that declares it, and no party (a factor's
    # party label may differ by sector).
    assert record["factor"] == "alice_station"
    assert "party" not in record
    assert record["choice_alphabet"] == tuple(weighting.choice_alphabet)
    assert record["setting_alphabet"] == tuple(weighting.setting_alphabet)
    assert dict(record["matrix"]) == {
        f"{setting}|{choice}": str(weighting.weight(setting, choice))
        for setting in weighting.setting_alphabet
        for choice in weighting.choice_alphabet
    }


@pytest.mark.parametrize("route", ROUTES)
def test_a_coin_is_emitted_under_the_exported_predicate(route: str) -> None:
    """``public_choice_declared`` is the predicate the A-COIN row is emitted under."""
    prepared = preparation(route)[0]
    assert public_choice_declared(prepared.specification) == (
        KEY["A-COIN"] in prepared.compilation.assumption_ledger
    )


def test_the_decoy_source_model_row_binds_the_model() -> None:
    """``ass:wcp``: the letters, weights, intensities, polarisations and cutoffs.

    The decoy artefact carries A-WCP's values as its ``source_model_bindings``,
    which its ``assumption_bindings`` reads; the compiler copies them. The
    premise fixes the declaration "with the cutoffs, the weights and the
    polarisations it declares", so ``N_ent`` and ``N_src`` are bound too.
    """
    prepared, config = preparation("decoy")
    artifact = prepared.specification.source.artifact
    wcp = dict(dict(artifact.assumption_bindings)[KEY["A-WCP"]])
    assert set(wcp) == {
        "signal_alphabet",
        "signal_weights",
        "intensities",
        "polarisations",
        "entropy_cutoff",
        "source_cutoff",
    }
    declared = {**dict(config.model), **dict(config.device)}
    for name in ("entropy_cutoff", "source_cutoff"):
        assert type(wcp[name]) is int
        if name in declared:
            assert wcp[name] == declared[name], name
    letters = dict(wcp["signal_alphabet"])  # type: ignore[arg-type]
    assert tuple(letters) == tuple(artifact.signal_alphabet)
    assert dict(wcp["signal_weights"]) == {  # type: ignore[arg-type]
        label: str(artifact.virtual_ensemble_weights[label])
        for label in artifact.signal_alphabet
    }
    for value in dict(wcp["intensities"]).values():  # type: ignore[arg-type]
        assert F(value) >= 0
    assert _bindings("decoy")["A-WCP"] == wcp


def test_the_decoy_declaration_binds_what_its_artefact_binds() -> None:
    """The declaration's own record and the artefact it admits agree, row by row."""
    from decoy_support import tagged_declaration

    declaration = tagged_declaration()
    artifact = declaration.as_transmitter_artifact()
    assert declaration.assumption_bindings == artifact.assumption_bindings
    wcp = dict(dict(declaration.assumption_bindings)["wcp_source_model"])
    assert dict(wcp["intensities"]) == {"signal": "1/2", "decoy": "1/8"}  # type: ignore[arg-type]
    record = declaration.as_machine_record()["assumption_bindings"]
    assert record == ledger_bindings_record(declaration.assumption_bindings)  # type: ignore[comparison-overlap]


#: The transmitter test's trusted pure-form source: two letters, d_A = 2.
_HALF = F(1, 2)
_Z0 = matrix(((1, 0), (0, 0)))
_Z1 = matrix(((0, 0), (0, 1)))
_PHI_PLUS = scale(
    _HALF, matrix(((1, 0, 0, 1), (0, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 1)))
)


def _source(mode: SourceMode) -> SourceSpecification:
    return SourceSpecification(
        signal_alphabet=("x0", "x1"),
        alice_dim=2,
        alice_povm={"x0": _Z0, "x1": _Z1},
        transmitted_dim=2,
        signal_weights={"x0": _HALF, "x1": _HALF},
        signal_states={"x0": _Z0, "x1": _Z1},
        source_mode_request=mode,
        certificate=(
            None
            if mode is SourceMode.UNTRUSTED
            else SourceReplacementCertificate(
                alice_marginal=scale(_HALF, matrix(((1, 0), (0, 1)))),
                psi=_PHI_PLUS,
                virtual_dim=2,
                virtual_weights={"x0": _HALF, "x1": _HALF},
                virtual_states={"x0": _Z0, "x1": _Z1},
            )
        ),
    )


def test_the_transmitter_binds_its_rows_from_its_own_fields() -> None:
    """``ass:ens`` (i), (ii); ``ass:seq`` nothing; ``ass:src`` its premise and (ii)."""
    trusted = emit_artifact(_source(SourceMode.TRUSTED)).require()
    rows = dict(trusted.assumption_bindings)
    assert tuple(rows) == trusted.assumption_ledger
    assert rows["source_ensemble"] == (
        (
            "source_ensemble",
            (
                ("signal_alphabet", ("x0", "x1")),
                ("weights", (("x0", "1/2"), ("x1", "1/2"))),
                ("transmitted_dim", 2),
            ),
        ),
    )
    assert rows["sequential_round_model"] == ()
    assert rows["source_replacement_license"] == (
        ("source_mode", "trusted"),
        ("alice_marginal", (("dimension", 2), ("sector_dims", (2,)))),
        (
            "alice_povm",
            (("form", "povm"), ("alphabet", ("x0", "x1")), ("dimension", 2)),
        ),
    )
    assert trusted.as_machine_record()["assumption_bindings"] == ledger_bindings_record(
        trusted.assumption_bindings
    )
    # Untrusted: no A-SRC row, and no A-ENS row (A-ENS is in trusted-source mode only),
    # so nothing bound for either.
    untrusted = emit_artifact(_source(SourceMode.UNTRUSTED)).require()
    assert tuple(dict(untrusted.assumption_bindings)) == ("sequential_round_model",)


def test_an_artefact_an_instance_builds_directly_binds_the_same_way() -> None:
    """The Band-A instance builds its artefact by hand; its rows are still bound."""
    artifact = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)).source.artifact
    rows = dict(artifact.assumption_bindings)
    assert tuple(rows) == artifact.assumption_ledger
    assert [name for name, _ in rows["source_replacement_license"]] == [
        "source_mode",
        "alice_marginal",
        "alice_povm",
    ]


def test_a_refusal_binds_nothing() -> None:
    """A refusal emits no declaration, so no ledger and no bindings."""
    result = compile_specification(
        conjugation_example_specification(ConjugationConvention.OMITTED)
    )
    assert result.refuses
    assert result.assumption_bindings == ()
    assert result.as_machine_record()["assumption_bindings"] == {}


@pytest.mark.parametrize("route", ROUTES)
def test_the_run_tier_joins_the_bindings_onto_the_emitted_rows(route: str) -> None:
    """``runs.assumptions.emitted_rows`` joins each emitter's bindings onto its rows.

    A compiler row carries the compiler's, a transmitter row the artefact's.
    """
    result = route_result(route)
    compiler = dict(result.compilation.assumption_bindings)
    transmitter = dict(result.specification.source.artifact.assumption_bindings)
    rows = emitted_rows(result)  # type: ignore[arg-type]
    for row in rows:
        if row.emitted_by == "protocol-compiler":
            assert row.bindings == compiler[row.machine_key], row.machine_key
        elif row.emitted_by == "transmitter":
            assert row.bindings == transmitter[row.machine_key], row.machine_key
