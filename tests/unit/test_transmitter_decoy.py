"""The decoy submodule: the model, the tagged declaration and what it emits.

``transmitter/decoy/def:wcp-model``, ``def:tagged-source``,
``prop:decoy-cert``, ``cor:emitted-decoy`` and the two remarks.

ONE TEST PER REFUSAL AND ONE PER PREDICATE, which is what the ``decoy/req:*``
requirements list: the weight obligation (against the enclosure the emission
forms) and its equality reading, the cutoffs, the flag family, the
construction of the signal dyads, a formed entry that is not declarable, and
(E1)/(E2)/(E3) through the core. The
predicates are the index set of (T3), the tail weight of ``eq:tailweight``, the
weight and dyad each letter carries in each sector (``prop:decoy-cert``), and
the obligation triple of (ii).

WHAT IS DELIBERATELY NOT TESTED HERE: what the protocol compiler does with the
emission. ``tests/unit/test_protocol_general_compile.py`` (the decoy-shaped
specification) exercises that, and
``tests/unit/test_transmitter_forms_at_the_compiler.py`` what the compiler's
gate (G2) does with an ensemble presentation and a block-form certificate.
"""

from __future__ import annotations

import math
from dataclasses import fields, replace
from fractions import Fraction as F

import numpy as np
import pytest
from decoy_support import (
    BB84_POLARISATIONS,
    declaration_input,
    signal_dyads,
    tagged_declaration,
    wcp_model,
)

from certiqs_key.foundations.blocks import BlockKind
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import equal, matrix, matrix_is_binary64
from certiqs_key.transmitter.decoy import (
    DECOY_ASSUMPTION_LEDGER,
    TAGGING_OBLIGATION,
    FlagFamily,
    SectorKind,
    TaggedSourceDeclaration,
    emit_decoy_declaration,
    exhibited_signal_dyad,
    poisson_enclosures,
    poisson_index,
)
from certiqs_key.transmitter.decoy.reasons import DecoyRefusal, DecoyRefusalReason
from certiqs_key.transmitter.links import (
    SOUNDNESS_REGISTRY,
    SourceLinkKind,
    WitnessKind,
)
from certiqs_key.transmitter.reasons import RefusalReason

pytestmark = pytest.mark.contract


def _refuse(**overrides: object) -> DecoyRefusal:
    result = emit_decoy_declaration(declaration_input(**overrides))
    assert result.declaration is None
    assert result.refusal is not None
    return result.refusal


# ---------------------------------------------------------------------------
#  The refusals of the decoy requirements (decoy/req:*)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        pytest.param(
            {"entropy_cutoff": 2, "source_cutoff": 1},
            DecoyRefusalReason.CUTOFFS_OUT_OF_ORDER,
            id="N_ent-above-N_src",
        ),
        pytest.param(
            {"entropy_cutoff": -1},
            DecoyRefusalReason.CUTOFFS_OUT_OF_ORDER,
            id="negative-N_ent",
        ),
        pytest.param(
            {"entropy_cutoff": 3, "source_cutoff": 3},
            DecoyRefusalReason.ENTROPY_CUTOFF_ABOVE_TWO,
            id="N_ent-above-two",
        ),
        pytest.param(
            {"flag_family": FlagFamily.SPLIT_BY_INTENSITY},
            DecoyRefusalReason.FLAG_FAMILY_SPLIT_BY_INTENSITY,
            id="split-flags",
        ),
        pytest.param(
            {"weight_obligation_presented_as_equality": True},
            DecoyRefusalReason.SECTOR_WEIGHT_AS_EQUALITY,
            id="equality-reading",
        ),
    ],
)
def test_each_refusal_of_part_vi_fires_on_its_own_condition(
    overrides: dict[str, object], reason: DecoyRefusalReason
) -> None:
    """Each negates a ``decoy/req:*`` requirement's condition, with its own reason."""
    assert _refuse(**overrides).reason is reason


@pytest.mark.parametrize(
    "cutoffs",
    [
        pytest.param({"entropy_cutoff": 1.5}, id="non-integer-N_ent"),
        pytest.param({"source_cutoff": 2.5}, id="non-integer-N_src"),
        pytest.param({"entropy_cutoff": True}, id="bool-N_ent"),
    ],
)
def test_a_cutoff_that_is_not_an_integer_is_refused_as_out_of_order(
    cutoffs: dict[str, object],
) -> None:
    """``decoy/req:cutoff-order``: the one refusal for a non-integer cutoff too.

    A non-integer cutoff gives the named refusal and not a ``TypeError`` from
    the emission. The cutoffs are replaced on a declaration
    built with integer ones, because the fixture itself iterates over them.
    """
    declaration = replace(declaration_input(), **cutoffs)
    result = emit_decoy_declaration(declaration)
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is DecoyRefusalReason.CUTOFFS_OUT_OF_ORDER


@pytest.mark.parametrize(
    "cutoffs",
    [
        pytest.param(
            {"entropy_cutoff": np.int64(1), "source_cutoff": np.int64(2)},
            id="numpy-int64",
        ),
    ],
)
def test_an_integral_cutoff_of_another_type_is_admitted(
    cutoffs: dict[str, object],
) -> None:
    """``decoy/req:cutoff-order`` refuses non-INTEGERS, not other integer types.

    A ``numbers.Integral`` that is not a ``bool`` -- a numpy integer included --
    is an integer cutoff, and the machine record carries it as a plain int.
    """
    declaration = replace(declaration_input(), **cutoffs)
    result = emit_decoy_declaration(declaration)
    assert result.refusal is None, result.refusal
    record = result.require().as_machine_record()
    assert type(record["entropy_cutoff"]) is int
    assert type(record["source_cutoff"]) is int
    assert (record["entropy_cutoff"], record["source_cutoff"]) == (1, 2)


def test_the_entropy_cutoff_refusal_is_a_scope_decision_and_says_so() -> None:
    """The refusal at ``N_ent >= 3`` is a scope decision and says so.

    ``decoy/req:entropy-cutoff``: "The refusal is A SCOPE DECISION and not a
    consequence of anything the claims state"; what is missing is a declared
    basis with exactly declarable dyad entries at three photons and above.
    """
    detail = _refuse(entropy_cutoff=3, source_cutoff=3).detail
    assert "SCOPE REFUSAL" in detail
    assert "three" in detail
    with pytest.raises(MalformedInputError, match="asserts nothing at three"):
        exhibited_signal_dyad(3, "H")


def test_a_weight_above_the_formed_enclosure_is_refused_naming_the_pair() -> None:
    """(T2) ``eq:weightineq``, decided against the enclosure's LOWER end.

    "The report names the first ``(n, mu)`` at which it fails."
    """
    base = declaration_input()
    weights = dict(base.sector_weights)
    weights[(1, "signal")] = F(1, 2)
    refusal = _refuse(sector_weights=weights)
    assert refusal.reason is DecoyRefusalReason.SECTOR_WEIGHT_ABOVE_POISSON
    assert "(1, 'signal')" in refusal.detail
    assert "LOWER" in refusal.detail


def test_a_weight_just_above_the_formed_lower_end_is_refused() -> None:
    """``req:sector-weight-bound``: the engine's own lower end decides, nothing else.

    The declaration carries no enclosure (it has no field for one), so a
    caller's enclosure, however computed, cannot enter. The binary64 number
    just above the lower end the emission forms at ``K_mu`` is refused with
    ``sector_weight_above_poisson``, and the one at or below it is admitted:
    the comparison is with that lower end and with no other number.
    """
    declared = {field.name for field in fields(TaggedSourceDeclaration)}
    assert "poisson_enclosures" not in declared
    assert "signal_dyads" not in declared

    base = declaration_input()
    mu = base.model.intensities["signal"]
    table = poisson_enclosures(mu, base.source_cutoff)
    assert table.index == poisson_index(mu)
    lower = table.enclosures[0].lower
    above = F(math.nextafter(float(lower), 1.0))
    while above <= lower:
        above = F(math.nextafter(float(above), 1.0))
    # BELOW on a coarse dyadic grid, so that every formed product stays exact.
    below = F(math.floor(lower * 2**20), 2**20)
    assert below <= lower < above

    weights = dict(base.sector_weights)
    weights[(0, "signal")] = above
    refusal = _refuse(sector_weights=weights)
    assert refusal.reason is DecoyRefusalReason.SECTOR_WEIGHT_ABOVE_POISSON
    assert "(0, 'signal')" in refusal.detail
    assert f"K_mu = {table.index}" in refusal.detail

    weights[(0, "signal")] = below
    assert emit_decoy_declaration(
        declaration_input(sector_weights=weights)
    ).refusal is None


def test_the_record_carries_the_summation_index_per_intensity() -> None:
    """``req:sector-weight-bound``: ``K_mu`` is recorded per intensity.

    It travels in the weight table of the emitted record, beside the declared
    weights of that intensity.
    """
    emitted = tagged_declaration()
    table = emitted.as_machine_record()["sector_weights"]
    model = emitted.declaration.model
    assert list(table) == list(model.intensities)
    for name, mu in model.intensities.items():
        assert table[name]["poisson_index"] == poisson_index(mu)
        assert table[name]["weights"] == [
            emitted.declaration.sector_weights[(n, name)]
            for n in range(emitted.declaration.source_cutoff + 1)
        ]


def test_a_negative_declared_weight_is_refused() -> None:
    """``0 <= ptilde`` is the other half of ``eq:weightineq``."""
    base = declaration_input()
    weights = dict(base.sector_weights)
    weights[(2, "decoy")] = F(-1, 256)
    assert _refuse(sector_weights=weights).reason is (
        DecoyRefusalReason.SECTOR_WEIGHT_ABOVE_POISSON
    )


def test_a_formed_product_that_is_not_binary64_is_refused_and_never_rounded() -> None:
    """``formed_entry_not_declarable``, THE CORE'S STRING, on a product.

    The lead-in of ``req:exact-decoy-blocks``: the remedy is the declarer's --
    "choosing the ``p_x`` and the ``ptilde(n|mu)`` with few enough significant
    bits makes every product exact" -- and the refusal names it.

    THE WITNESS NEEDS BOTH FACTORS TO CARRY BITS, which is what makes it a test
    of the PRODUCT and not of either declared number: ``p_x = 3/4`` carries two
    significand bits and ``ptilde = 1 - 2^-52`` carries fifty-three, so each is
    a binary64 number and ``3(2^52 - 1)/2^54`` needs fifty-four. The intensity
    ``2^-60`` puts ``P_mu(0)``, and the lower end the emission forms, near
    ``1 - 2^-60``, above the declared weight. The model is built here rather
    than taken from the fixture because the fixture's weights are deliberately
    coarse enough that every product IS exact.
    """
    from certiqs_key.transmitter.decoy import (
        RoundType,
        TaggedSourceDeclaration,
        WcpLetter,
        WcpModel,
    )

    letters = (
        WcpLetter(label="H-tiny", polarisation="H", intensity="tiny",
                  round_type=RoundType.GEN),
        WcpLetter(label="V-tiny", polarisation="V", intensity="tiny",
                  round_type=RoundType.GEN),
    )
    model = WcpModel(
        polarisations=("H", "V"),
        intensities={"tiny": F(1, 2**60)},
        alphabet=letters,
        weights={"H-tiny": F(3, 4), "V-tiny": F(1, 4)},
    )
    declaration = TaggedSourceDeclaration(
        model=model,
        entropy_cutoff=0,
        source_cutoff=0,
        sector_weights={(0, "tiny"): F(1) - F(1, 2**52)},
    )
    result = emit_decoy_declaration(declaration)
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.FORMED_ENTRY_NOT_DECLARABLE
    assert "coarser dyadic grid" in result.refusal.detail
    # NOT ROUNDED: the declared weight is untouched after the refusal.
    assert declaration.sector_weights[(0, "tiny")] == F(1) - F(1, 2**52)


def test_a_tail_weight_whose_accumulation_rounds_is_refused() -> None:
    """``eq:tailweight``, "the sum formed in increasing ``n`` and rounding nowhere".

    ``1/2 + 2^-54 = (2^53 + 1)/2^54`` needs fifty-four significand bits, so the
    accumulation of ``eq:tailweight`` is inexact although both summands are
    binary64 numbers -- which is the whole reason (T2) says the sum "rounds
    nowhere" rather than saying the summands are declarable.
    """
    base = declaration_input()
    weights = dict(base.sector_weights)
    weights[(0, "decoy")] = F(1, 2)
    weights[(1, "decoy")] = F(1, 2**54)
    refusal = _refuse(sector_weights=weights)
    assert refusal.reason is RefusalReason.FORMED_ENTRY_NOT_DECLARABLE
    assert "tail weight" in refusal.detail


# ---------------------------------------------------------------------------
#  The predicates: (T3)'s index set, the tail weight, the weights and the dyads
# ---------------------------------------------------------------------------


def test_the_index_set_is_read_off_the_weights_in_the_declared_order() -> None:
    """(T3) ``eq:tset``: quantum sectors, then polarisation flags, then tail flags.

    With ``N_ent = 1`` and ``N_src = 2`` the declaration carries the vacuum and
    the one-photon quantum sectors, one polarisation flag per polarisation at
    two photons SHARED ACROSS THE TWO INTENSITIES, and one tail flag per
    ``(a, mu)`` a letter carries.
    """
    declaration = declaration_input()
    sectors = declaration.sector_index_set()
    kinds = [sector.kind for sector in sectors]
    assert kinds[:2] == [SectorKind.QUANTUM, SectorKind.QUANTUM]
    flags = [s for s in sectors if s.kind is SectorKind.POLARISATION_FLAG]
    # ONE FLAG PER POLARISATION AND NOT ONE PER (POLARISATION, INTENSITY):
    # "that sharing is the content of the declaration".
    assert len(flags) == len(BB84_POLARISATIONS)
    assert all(flag.photon_number == 2 for flag in flags)
    tails = [s for s in sectors if s.kind is SectorKind.TAIL_FLAG]
    assert len(tails) == len(BB84_POLARISATIONS) * 2
    assert all(sector.dim == 1 for sector in sectors if sector.kind is not
               SectorKind.QUANTUM)


def test_a_sector_no_letter_weights_is_not_declared() -> None:
    """A sector no letter weights is not in the index set.

    (T3): "A SECTOR THAT NO LETTER OF X PUTS POSITIVE WEIGHT ON IS NOT
    DECLARED", and the list is re-formed when the weights change (v).
    """
    base = declaration_input()
    weights = dict(base.sector_weights)
    for intensity in ("signal", "decoy"):
        weights[(2, intensity)] = F(0)
    declaration = declaration_input(sector_weights=weights)
    sectors = declaration.sector_index_set()
    assert not [s for s in sectors if s.kind is SectorKind.POLARISATION_FLAG]
    # The tail flags GAINED weight, which is the direction (v) names.
    assert [s for s in sectors if s.kind is SectorKind.TAIL_FLAG]


def test_lowering_a_weight_gives_another_tagged_declaration() -> None:
    """(v): "the weights ``ptilde'`` are again a tagged source declaration".

    The rounded declaration "is a different declaration, not a perturbation of
    one": its tail weight is larger and its sector list is re-formed.
    """
    base = declaration_input()
    lowered = dict(base.sector_weights)
    lowered[(1, "signal")] = F(1, 8)
    rounded = declaration_input(sector_weights=lowered)
    assert rounded.tail_weight("signal").value > base.tail_weight("signal").value
    assert emit_decoy_declaration(rounded).refusal is None


def test_the_tail_weight_is_formed_exactly_and_is_one_minus_the_sum() -> None:
    """``eq:tailweight``, and ``wtilde_mu >= 0`` by (T2)."""
    declaration = declaration_input()
    for intensity in ("signal", "decoy"):
        tail = declaration.tail_weight(intensity)
        assert tail.rounds_nowhere
        assert tail.value >= 0
        total = sum(
            declaration.sector_weights[(n, intensity)]
            for n in range(declaration.source_cutoff + 1)
        )
        assert tail.value == F(1) - total


def test_the_weight_and_the_dyad_each_letter_carries_are_the_propositions() -> None:
    """``prop:decoy-cert``: ``w_{x,t}`` and ``|phi_{x,t}>`` case by case."""
    declaration = declaration_input()
    sectors = declaration.sector_index_set()
    model = declaration.model
    letter = next(x for x in model.alphabet if x.polarisation == "H")
    other = next(x for x in model.alphabet if x.polarisation == "V")
    flag = next(s for s in sectors if s.kind is SectorKind.POLARISATION_FLAG
                and s.polarisation == "H")
    # A polarisation flag carries ptilde for its own polarisation and 0 for
    # another's.
    assert declaration.weight_in(flag, letter) == declaration.sector_weights[
        (2, letter.intensity)
    ]
    assert declaration.weight_in(flag, other) == 0
    # ON EVERY FLAG SECTOR AND ON THE VACUUM the dyad is the number 1.
    assert equal(declaration.dyad_in(flag, letter), matrix(((1,),)))
    vacuum = next(s for s in sectors if s.kind is SectorKind.QUANTUM
                  and s.photon_number == 0)
    assert equal(declaration.dyad_in(vacuum, letter), matrix(((1,),)))


def test_the_exhibited_dyads_have_the_entries_the_proof_writes() -> None:
    """(iv)(b): "a declared basis exists in which every entry is 0 or +/- 1/2"."""
    for photon_number in (0, 1, 2):
        for polarisation in BB84_POLARISATIONS:
            dyad = exhibited_signal_dyad(photon_number, polarisation)
            assert matrix_is_binary64(dyad)
            for row in dyad:
                for entry in row:
                    assert entry.re in (F(0), F(1, 2), F(-1, 2), F(1))
                    assert entry.im == 0


def test_the_two_photon_dyads_are_rank_one_projectors_of_the_proofs_vectors() -> None:
    """The two-photon dyads carry the Gram matrix the proof matches.

    ``<2,H|2,V> = 0`` and ``<2,H|2,+> = 1/2``, read off the dyads as
    ``tr[P_a P_b]``.
    """
    from certiqs_key.foundations.exact import matmul, trace

    dyads = {a: exhibited_signal_dyad(2, a) for a in BB84_POLARISATIONS}
    assert trace(matmul(dyads["H"], dyads["V"])).re == 0
    assert trace(matmul(dyads["+"], dyads["-"])).re == 0
    assert trace(matmul(dyads["H"], dyads["+"])).re == F(1, 4)
    for dyad in dyads.values():
        assert trace(dyad).re == 1


# ---------------------------------------------------------------------------
#  The emission of cor:emitted-decoy
# ---------------------------------------------------------------------------


def test_the_emission_declares_the_tagged_ensemble_itself() -> None:
    """(i), (iv): the declared blocks ARE ``p_x w_{x,t} |phi><phi|``, formed exactly."""
    emitted = tagged_declaration()
    declaration = emitted.declaration
    sectors = declaration.sector_index_set()
    for letter in declaration.model.alphabet:
        blocks = emitted.presentation.weighted_blocks[letter.label]
        assert len(blocks) == len(sectors)
        for sector, block in zip(sectors, blocks, strict=True):
            assert matrix_is_binary64(block)
            expected_trace = (
                declaration.model.weights[letter.label]
                * declaration.weight_in(sector, letter)
            )
            from certiqs_key.foundations.exact import trace

            assert trace(block).re == expected_trace


def test_nothing_is_compressed_and_no_rank_is_read() -> None:
    """(T5) and ``prop:decoy-cert`` (iii): ``dim A_t = dim S_t``, whatever the rank.

    The one-photon sector's marginal has rank two in a two-dimensional space and
    the two-photon flags are one dimensional; ``A_t`` copies ``S_t`` in both
    cases, and there is no compression record to emit.
    """
    emitted = tagged_declaration()
    alice, virtual = emitted.alice_sector_map
    assert alice.dims == virtual.dims
    assert alice.labels == virtual.labels
    assert alice.block_kind is BlockKind.PROOF_SECTOR
    assert "compression" not in str(emitted.as_machine_record())


def test_the_segment_is_one_tagging_link_with_its_obligation() -> None:
    """(ii) and (T6): one link, witness a THEOREM CONSTRUCTOR, entries empty."""
    emitted = tagged_declaration()
    assert len(emitted.source_segment) == 1
    link = emitted.link
    assert link.kind is SourceLinkKind.TAGGING
    assert link.witness_kind is WitnessKind.THEOREM_CONSTRUCTOR
    assert link.channel_witness is None
    assert link.constraint_entries == ()
    assert link.licence is None
    assert link.obligation is TAGGING_OBLIGATION
    # The target is the FOCK SPACE: no dimension and no matrix, which is why
    # the witness cannot be supplied as data.
    assert link.target_descriptor.system_dim is None
    assert not link.target_descriptor.is_finite_dimensional


def test_the_obligation_triple_is_the_cores_registry_entry() -> None:
    """(ii): the triple IS this submodule's entry in the core's registry.

    A drift between the two files would make every emitted link refusable the
    day the segment opens, which is exactly the failure the registry row's
    ``why_this_list`` field names.
    """
    entry = next(e for e in SOUNDNESS_REGISTRY if e.kind is SourceLinkKind.TAGGING)
    assert TAGGING_OBLIGATION.triple == entry.triple
    assert TAGGING_OBLIGATION.assumptions == ("A-WCP",)


def test_the_ledger_carries_a_wcp_and_never_a_ens_or_a_nosrc() -> None:
    """The submodule's ``emission_rule``: A-WCP in the place of A-ENS."""
    assert DECOY_ASSUMPTION_LEDGER == (
        "wcp_source_model",
        "sequential_round_model",
        "source_replacement_license",
    )
    assert "source_ensemble" not in DECOY_ASSUMPTION_LEDGER
    assert "source_stage_empty" not in DECOY_ASSUMPTION_LEDGER


def test_no_yield_no_statistic_and_no_key_rate_is_emitted() -> None:
    """The submodule's ``not_outputs``, read off the emitted record's keys."""
    record = tagged_declaration().as_machine_record()
    for absent in ("yield", "frequency", "key_length", "key_rate", "receiver"):
        assert not any(absent in key for key in record)


# ---------------------------------------------------------------------------
#  def:wcp-model's own typing
# ---------------------------------------------------------------------------


def test_a_label_of_weight_zero_is_not_a_letter() -> None:
    """(W2): "the alphabet carries the labels the source actually prepares"."""
    model = wcp_model()
    with pytest.raises(MalformedInputError, match="WEIGHT ZERO IS NOT A LETTER"):
        replace(
            model,
            weights={**model.weights, model.alphabet[0].label: F(0)},
        )


def test_a_quantum_sector_is_the_whole_photon_number_space() -> None:
    """``cor:emitted-decoy`` (iv)(b): ``dim S_1 = 2`` and ``dim S_2 = 3``.

    Inside the construction ``S_n`` is the whole ``n``-photon space, so its
    dimension is ``n + 1`` and is no declared datum.
    """
    for entropy_cutoff in (1, 2):
        sectors = tagged_declaration(
            entropy_cutoff=entropy_cutoff, source_cutoff=2
        ).presentation.virtual_sectors
        for photon_number in range(entropy_cutoff + 1):
            position = sectors.labels.index(f"n{photon_number}")
            assert sectors.dims[position] == photon_number + 1


def test_an_intensity_of_zero_is_admissible() -> None:
    """(W2): "An intensity of zero is admissible and is the vacuum-only letter"."""
    model = wcp_model()
    replace(model, intensities={**model.intensities, "signal": F(0)})


def test_the_emitted_dyads_are_the_constructions() -> None:
    """``req:signal-dyads``: the emission forms the dyads by (iv)(b) itself.

    Every block of a quantum sector is ``p_x ptilde(n|mu_x)`` times the dyad
    the corollary's construction writes for the vector of ``D`` the letter's
    polarisation stands for, and the vacuum's is that weight times one.
    """
    for entropy_cutoff in (1, 2):
        emitted = tagged_declaration(entropy_cutoff=entropy_cutoff, source_cutoff=2)
        declaration = emitted.declaration
        expected = signal_dyads(entropy_cutoff)
        sectors = declaration.sector_index_set()
        for letter in declaration.model.alphabet:
            blocks = emitted.presentation.weighted_blocks[letter.label]
            for sector, block in zip(sectors, blocks, strict=True):
                if sector.kind is not SectorKind.QUANTUM:
                    continue
                assert sector.photon_number is not None
                dyad = expected[(sector.photon_number, letter.polarisation)]
                factor = declaration.model.weights[letter.label] * (
                    declaration.sector_weights[
                        (sector.photon_number, letter.intensity)
                    ]
                )
                assert equal(declaration.dyad_in(sector, letter), dyad)
                for row, expected_row in zip(block, dyad, strict=True):
                    for entry, expected_entry in zip(
                        row, expected_row, strict=True
                    ):
                        assert entry.re == factor * expected_entry.re
                        assert entry.im == 0


def test_a_formed_dyad_that_fails_the_guard_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact guard of ``req:signal-dyads`` on the formed dyads.

    The emission decides of each formed dyad that it is a rank-one projector
    and that ``tr[X_a X_b] = |<a|b>|^(2n)``, the right-hand side formed from
    the one-photon overlaps of ``D`` and not from the matrices. A construction
    that returned H's dyad for V, or a mixture, would fail it.

    THE SUBSTITUTION IS MADE WHERE THE BLOCKS GET THEIR DYADS
    (``tagged.exhibited_signal_dyad``, behind
    ``TaggedSourceDeclaration.dyad_in`` and ``signal_dyad``), so the test fails
    if the guard decided a second copy of the dyads rather than the matrices
    that enter the blocks (review F-1).
    """
    import certiqs_key.transmitter.decoy.tagged as tagged_module

    real = tagged_module.exhibited_signal_dyad

    def swapped(photon_number: int, part: str) -> object:
        return real(photon_number, "H" if part == "V" else part)

    monkeypatch.setattr(tagged_module, "exhibited_signal_dyad", swapped)
    refusal = _refuse()
    assert refusal.reason is DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION
    assert "tr[X_a X_b]" in refusal.detail

    def mixed(photon_number: int, part: str) -> object:
        if part == "H":
            return matrix(((F(1, 2), 0), (0, F(1, 2))))
        return real(photon_number, part)

    monkeypatch.setattr(tagged_module, "exhibited_signal_dyad", mixed)
    refusal = _refuse()
    assert refusal.reason is DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION
    assert "rank-one projector" in refusal.detail

    monkeypatch.setattr(tagged_module, "exhibited_signal_dyad", real)
    assert emit_decoy_declaration(declaration_input()).refusal is None


def test_the_record_decides_the_dyads_its_own_blocks_carry() -> None:
    """``DecoySourceDeclaration`` re-decides the guard on its presentation's blocks.

    A record built by hand with the emitted declaration but a presentation
    whose one-photon block of a V letter carries H's dyad (its weight
    unchanged) refuses to exist, although the tagged declaration itself is
    inside the construction (review F-1).
    """
    from certiqs_key.foundations.exact import scale
    from certiqs_key.transmitter.presentation import EnsemblePresentation

    good = tagged_declaration()
    declaration = good.declaration
    sectors = declaration.sector_index_set()
    position = next(
        index
        for index, sector in enumerate(sectors)
        if sector.kind is SectorKind.QUANTUM and sector.photon_number == 1
    )
    letter = next(x for x in declaration.model.alphabet if x.polarisation == "V")
    factor = declaration.model.weights[letter.label] * declaration.weight_in(
        sectors[position], letter
    )
    blocks = {
        label: list(row) for label, row in good.presentation.weighted_blocks.items()
    }
    blocks[letter.label][position] = scale(factor, exhibited_signal_dyad(1, "H"))
    forged = EnsemblePresentation(
        virtual_sectors=good.presentation.virtual_sectors,
        weighted_blocks={label: tuple(row) for label, row in blocks.items()},
    )
    with pytest.raises(MalformedInputError, match="is not the block"):
        replace(good, presentation=forged)


@pytest.mark.parametrize(
    "forgery", ["vacuum-halved", "flag-halved", "letter-missing", "zero-weight-filled"]
)
def test_the_record_decides_every_block_it_carries(forgery: str) -> None:
    """Every block of the record is ``eq:decoy-blocks``'s, exactly (review F-7).

    A hand-built record whose vacuum block or polarisation-flag block of one
    letter is halved, whose presentation lacks a letter, or whose block at a
    position of weight zero (another polarisation's flag) is not zero, raises
    ``MalformedInputError`` rather than being admitted or failing untyped.
    """
    from certiqs_key.foundations.exact import scale
    from certiqs_key.transmitter.presentation import EnsemblePresentation

    good = tagged_declaration()
    sectors = good.declaration.sector_index_set()
    letter = good.declaration.model.alphabet[0]
    blocks = {
        label: list(row) for label, row in good.presentation.weighted_blocks.items()
    }
    if forgery == "letter-missing":
        del blocks[letter.label]
    elif forgery == "zero-weight-filled":
        position = next(
            index
            for index, sector in enumerate(sectors)
            if sector.kind is SectorKind.POLARISATION_FLAG
            and sector.polarisation != letter.polarisation
        )
        blocks[letter.label][position] = matrix(((F(1, 64),),))
    else:
        kind = (
            SectorKind.QUANTUM
            if forgery == "vacuum-halved"
            else SectorKind.POLARISATION_FLAG
        )
        position = next(
            index
            for index, sector in enumerate(sectors)
            if sector.kind is kind
            and (sector.photon_number == 0 or kind is not SectorKind.QUANTUM)
            and (
                kind is SectorKind.QUANTUM
                or sector.polarisation == letter.polarisation
            )
        )
        blocks[letter.label][position] = scale(
            F(1, 2), blocks[letter.label][position]
        )
    forged = EnsemblePresentation(
        virtual_sectors=good.presentation.virtual_sectors,
        weighted_blocks={label: tuple(row) for label, row in blocks.items()},
    )
    with pytest.raises(MalformedInputError):
        replace(good, presentation=forged)


#: ``cor:emitted-decoy`` (iv)(b), WRITTEN BY HAND from the corollary's text and
#: not from any function of the package: in the basis ``{|1,H>, |1,V>}`` the
#: one-photon dyads are ``[[1,0],[0,0]]``, ``[[0,0],[0,1]]`` and
#: ``(1/2)[[1,+-1],[+-1,1]]``; at two photons ``|2,a><2,a| = (1/2) v_a v_a^T``
#: with ``v_H = (1,1,0)``, ``v_V = (1,-1,0)``, ``v_+ = (1,0,1)``,
#: ``v_- = (1,0,-1)``, multiplied out entry by entry.
_H = F(1, 2)
_COROLLARY_DYADS: dict[tuple[int, str], tuple[tuple[F, ...], ...]] = {
    (1, "H"): ((F(1), F(0)), (F(0), F(0))),
    (1, "V"): ((F(0), F(0)), (F(0), F(1))),
    (1, "+"): ((_H, _H), (_H, _H)),
    (1, "-"): ((_H, -_H), (-_H, _H)),
    (2, "H"): ((_H, _H, F(0)), (_H, _H, F(0)), (F(0), F(0), F(0))),
    (2, "V"): ((_H, -_H, F(0)), (-_H, _H, F(0)), (F(0), F(0), F(0))),
    (2, "+"): ((_H, F(0), _H), (F(0), F(0), F(0)), (_H, F(0), _H)),
    (2, "-"): ((_H, F(0), -_H), (F(0), F(0), F(0)), (-_H, F(0), _H)),
}


@pytest.mark.parametrize("key", sorted(_COROLLARY_DYADS), ids=str)
def test_the_formed_dyads_are_the_corollarys_entries(key: tuple[int, str]) -> None:
    """The dyads the emission forms equal the corollary's, entry by entry (F-3).

    The expected side is the hand-written table above; the formed side is
    what the emitted blocks carry, read through ``signal_dyad`` of a
    declaration at ``N_ent = 2`` whose labels are the parts.
    """
    photon_number, polarisation = key
    declaration = declaration_input(entropy_cutoff=2, source_cutoff=2)
    formed = declaration.signal_dyad(photon_number, polarisation)
    expected = _COROLLARY_DYADS[key]
    assert len(formed) == len(expected)
    for row, expected_row in zip(formed, expected, strict=True):
        assert len(row) == len(expected_row)
        for entry, value in zip(row, expected_row, strict=True):
            assert entry.re == value
            assert entry.im == 0


def test_the_construction_cannot_be_walked_past_by_building_the_records() -> None:
    """A hand-built emitted record outside the construction refuses to exist.

    The emission is a function and a function is bypassable; a caller that
    built the emitted record by hand around a declaration whose quantum sector
    lies outside the construction of (iv)(b) would carry an obligation
    asserting membership of ``prop:tagging``'s family. The record re-decides
    ``req:signal-dyads`` at construction.
    """
    good = tagged_declaration()
    model = replace(
        good.declaration.model,
        polarisation_parts={"H": "H", "V": "V", "+": "+"},
    )
    with pytest.raises(MalformedInputError, match="refuses"):
        replace(good, declaration=replace(good.declaration, model=model))


def _small_model(polarisations: tuple[str, ...]) -> object:
    from certiqs_key.transmitter.decoy import RoundType, WcpLetter, WcpModel

    letters = tuple(
        WcpLetter(
            label=f"{polarisation}-mu",
            polarisation=polarisation,
            intensity="mu",
            round_type=RoundType.GEN,
        )
        for polarisation in polarisations
    )
    # DYADIC LABEL WEIGHTS, so that every formed product is exact.
    shares = {1: (F(1),), 2: (F(1, 2), F(1, 2)), 3: (F(1, 2), F(1, 4), F(1, 4))}
    return WcpModel(
        polarisations=polarisations,
        intensities={"mu": F(1, 4)},
        alphabet=letters,
        weights={
            letter.label: share
            for letter, share in zip(letters, shares[len(letters)], strict=True)
        },
        polarisation_parts=dict(zip(polarisations, polarisations, strict=True)),
    )


def _small_declaration(
    polarisations: tuple[str, ...], photon_number: int
) -> object:
    return declaration_input(
        model=_small_model(polarisations),
        entropy_cutoff=photon_number,
        source_cutoff=photon_number,
        sector_weights={(n, "mu"): F(1, 64) for n in range(photon_number + 1)},
    )


@pytest.mark.parametrize(
    ("polarisations", "photon_number"),
    [
        pytest.param(("H", "V"), 2, id="two-polarisations-at-two-photons"),
        pytest.param(("H",), 1, id="one-polarisation-at-one-photon"),
    ],
)
def test_fewer_than_n_plus_one_polarisations_at_n_photons_are_refused(
    polarisations: tuple[str, ...], photon_number: int
) -> None:
    """``req:signal-dyads``: the construction needs ``|Pol| >= n + 1``.

    Below it ``S_n`` need not be the whole ``n``-photon space and
    ``cor:emitted-decoy`` (iv)(b) exhibits no basis, so the declaration is
    refused with ``quantum_sector_outside_construction`` and no dyad is formed.
    """
    result = emit_decoy_declaration(
        _small_declaration(polarisations, photon_number)  # type: ignore[arg-type]
    )
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is (
        DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION
    )
    assert "n + 1" in result.refusal.detail


@pytest.mark.parametrize(
    ("polarisations", "photon_number"),
    [
        pytest.param(("H", "V"), 1, id="two-polarisations-at-one-photon"),
        pytest.param(("H", "V", "+"), 2, id="three-polarisations-at-two-photons"),
    ],
)
def test_a_subset_of_d_with_enough_polarisations_is_admitted(
    polarisations: tuple[str, ...], photon_number: int
) -> None:
    """(iv)(b) holds for every polarisation set drawn from ``D`` with ``n + 1``."""
    result = emit_decoy_declaration(
        _small_declaration(polarisations, photon_number)  # type: ignore[arg-type]
    )
    assert result.refusal is None, result.refusal
    sectors = result.require().presentation.virtual_sectors
    position = sectors.labels.index(f"n{photon_number}")
    assert sectors.dims[position] == photon_number + 1


def test_a_polarisation_with_no_declared_part_carries_no_quantum_sector() -> None:
    """Every polarisation must stand for a vector of ``D`` above the vacuum.

    ``req:signal-dyads`` forms the dyads only where every polarisation of
    ``Pol`` is one of the four vectors of ``D``; otherwise the declaration is
    refused with ``quantum_sector_outside_construction``. The vacuum is
    untouched, its dyad being the number one for every polarisation.
    """
    model = wcp_model()
    without = replace(model, polarisation_parts={"H": "H", "V": "V", "+": "+"})
    refusal = _refuse(model=without)
    assert refusal.reason is DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION
    assert "['-']" in refusal.detail
    # AT THE VACUUM ALONE IT IS ADMISSIBLE: N_ent = 0 declares only n = 0.
    assert (
        emit_decoy_declaration(
            declaration_input(model=without, entropy_cutoff=0, source_cutoff=2)
        ).refusal
        is None
    )
    # N_ent >= 3 IS REFUSED FIRST, under its own reason.
    assert _refuse(
        model=without, entropy_cutoff=3, source_cutoff=3
    ).reason is DecoyRefusalReason.ENTROPY_CUTOFF_ABOVE_TWO


def test_two_labels_for_one_vector_are_refused_above_the_vacuum_only() -> None:
    """``req:signal-dyads``: distinct polarisations as distinct vectors (F-2).

    Distinctness is a condition of a quantum sector ``n >= 1``: with two
    labels standing for one vector of ``D`` such a declaration is refused with
    ``quantum_sector_outside_construction``, and a vacuum-only declaration
    (``N_ent = 0``) is admitted, the vacuum's dyad being the number one.
    """
    model = wcp_model()
    shared = replace(model, polarisation_parts={**model.polarisation_parts, "V": "H"})
    refusal = _refuse(model=shared)
    assert refusal.reason is DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION
    assert "same vector" in refusal.detail
    assert (
        emit_decoy_declaration(
            declaration_input(model=shared, entropy_cutoff=0, source_cutoff=2)
        ).refusal
        is None
    )


def test_the_tail_flags_run_in_the_declared_order_of_polarisation_then_intensity(
) -> None:
    """(T3): "the tail flags in the declared order of ``(a, mu)``".

    The order is not the ALPHABET's, which is a
    third declared order the definition does not name; read like the ``(n, a)``
    of the polarisation flags it is the model's declared polarisation order
    outer and its declared intensity order inner. The two differ exactly when
    the alphabet is intensity-major, so the witness declares the SAME model
    twice with the two alphabet orders and asks for one tail order.
    """
    model = wcp_model()
    polarisation_major = tuple(
        letter
        for polarisation in model.polarisations
        for letter in model.alphabet
        if letter.polarisation == polarisation
    )
    assert polarisation_major != model.alphabet  # the fixture is intensity-major
    other = replace(
        model,
        alphabet=polarisation_major,
        weights={letter.label: model.weights[letter.label] for letter in
                 polarisation_major},
    )
    tails_of = lambda declaration: tuple(  # noqa: E731
        sector.label
        for sector in declaration.sector_index_set()
        if sector.kind is SectorKind.TAIL_FLAG
    )
    expected = (
        "tail-H-signal",
        "tail-H-decoy",
        "tail-V-signal",
        "tail-V-decoy",
        "tail-+-signal",
        "tail-+-decoy",
        "tail---signal",
        "tail---decoy",
    )
    assert tails_of(declaration_input()) == expected
    assert tails_of(declaration_input(model=other)) == expected
