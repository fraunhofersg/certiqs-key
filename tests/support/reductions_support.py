"""Helpers the reductions suites share.

WHAT IS HERE AND WHY. The core's normalizer is written over a CLASS
DECOMPOSITION of the joint alphabet (``def:joint-family``), because
``def:emitnorm`` acts per class and the core may not know that a class is a
probe setting. The tests are written against a signature that names ``Y`` and ``T``
directly. :func:`emission_normalizer`
is the adapter: it builds the classes from the letters, the settings and the
declared ``q_t`` and calls the core's own ``normalize``. NO ARITHMETIC HAPPENS
HERE -- the helper builds one record and forwards.

Keeping the adapter in the test tree rather than in the package is deliberate:
the package's own callers hand the classes over, and a second entry point in
the source would be a second reading of ``def:joint-family``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction

from registry_reductions import INHERITED_RECEIVER_KEYS_1_0_0, PR_R1

from certiqs_key.foundations.exact import Matrix, matrix
from certiqs_key.reductions.artifact import ReductionOutcome
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    HighPhotonBound,
    InheritedAssumption,
    JointOutcome,
    Label,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionCall,
    ReductionRequest,
    canonical_coarse_graining,
    product_form_dark_counts,
)
from certiqs_key.reductions.normalizer import JointClass, Normalization, normalize
from certiqs_key.reductions.reasons import (
    LinkKind,
    LinkStage,
    SourceMode,
)
from certiqs_key.reductions.wpfss import reduce_flat

__all__ = [
    "FIXTURE_KAPPA",
    "FIXTURE_RECEIVER_VERSION",
    "RECEIVER_LEDGER_KEYS",
    "RETIRED_RECEIVER_KEYS",
    "classes_of",
    "emission_normalizer",
    "flat_call",
    "reduce_flat_call",
]


#: The receiver keys of the frozen ``INHERITED_RECEIVER_KEYS_1_0_0`` that are
#: not emitted: A-ACYC is condition (E2) of ``receiver/def:graph``,
#: A-PROBE-DIAG is ``receiver/def:probe`` with
#: ``req:probe-diagonal-admission``, and A-FLOAT is
#: ``receiver/def:evaluation-model``. None is an assumption, so none has a row.
#: The frozen registry quotes the 1.0.0 contract and is not edited.
RETIRED_RECEIVER_KEYS: tuple[str, ...] = (
    "acyclic_element_graph",
    "probe_fock_diagonal",
    "floating_point_evaluation",
)

#: The receiver's ledger keys as a receiver artifact carries them, every row on
#: every artifact, in the receiver's order (``receiver/interface.yaml``
#: ``outputs.assumption_ledger.rows``): the frozen thirteen less the three
#: not emitted, written out by hand.
RECEIVER_LEDGER_KEYS: tuple[str, ...] = (
    "receiver_trusted_exact",
    "passive_optics",
    "undeclared_inputs_vacuum",
    "no_undeclared_paths",
    "threshold_memoryless_detectors",
    "mode_insensitive_ports",
    "exact_parameters",
    "device_not_adversarial",
    "round_homogeneity",
    "exact_window_eigenvalue_slack",
)
assert tuple(
    key for key in INHERITED_RECEIVER_KEYS_1_0_0 if key not in RETIRED_RECEIVER_KEYS
) == RECEIVER_LEDGER_KEYS


def classes_of(
    letters: Sequence[Label],
    settings: Sequence[Label],
    probe_weights: Mapping[Label, Fraction],
) -> tuple[JointClass, ...]:
    """Return the class decomposition of ``V = Y x T`` the tests declare."""
    return tuple(
        JointClass(
            label=setting,
            weight=probe_weights[setting],
            members=tuple((letter, setting) for letter in letters),
            names=tuple(letters),
        )
        for setting in settings
    )


def emission_normalizer(
    constructed: Mapping[JointOutcome, tuple[Matrix, ...]],
    *,
    letters: Sequence[Label],
    settings: Sequence[Label],
    probe_weights: Mapping[Label, Fraction],
    block_dimensions: Sequence[int],
    kappa: int,
) -> Normalization:
    """Run ``def:emitnorm`` from letters, settings and probe weights."""
    return normalize(
        constructed,
        classes=classes_of(letters, settings, probe_weights),
        sector_dimensions=block_dimensions,
        kappa=kappa,
    )


def reduce_flat_call(
    artifact_rows: ReceiverArtifactRows,
    declaration: ProtocolDeclaration,
    request: ReductionRequest,
) -> ReductionOutcome:
    """Run the FLAT reduction from the interface's three groups.

    The core's entry point takes them as one record and an INSTANCE BUILDER
    beside them. This helper is the adapter, so that the change of shape is
    visible in one place.

    IT SELECTS THE FLAT PATH, which is what a declaration with no branching
    model means: no DEGENERATE branching model with one mode and a
    one-dimensional register, whose ampliation every emitted object would
    carry.
    """
    return reduce_flat(ReductionCall(artifact_rows, declaration, request))


#: The supplier version the fixture below declares and accepts: the
#: receiver's accepted one, which STATES the per-setting weights; the wpfss
#: slot row refuses an artifact of a version that does not
#: (req:supplier-version). Fixture data, not an oracle value.
FIXTURE_RECEIVER_VERSION: str = "receiver@0.9.0"

#: The declared lattice exponent of the fixture. The same value the golden
#: emission suite declares, so that a factor built here and an artefact emitted
#: there are on one lattice.
FIXTURE_KAPPA: int = 12


def flat_call(
    *,
    party: Label | None = None,
    route: str = "encoded",
    letters: Sequence[Label] = ("y_empty", "y_1", "y_2", "y_mc"),
    settings: Sequence[Label] = ("t_off", "t_on"),
    source_mode: SourceMode = SourceMode.UNTRUSTED,
    **overrides: object,
) -> ReductionCall:
    """Return one flat-instance CALL, optionally scoped to a declared party.

    THE MINIMAL VALID DECLARATION FOR THE FLAT INSTANCE, built from the frozen
    band-5 receiver data the golden suite uses: a two-port device at cutoff 0,
    one preserved block, a coarse-graining onto four letters and two probe
    settings. It exists so that a suite about SEVERAL MEASURING PARTIES can
    declare a pair of factors without restating sixty lines of receiver rows
    per factor, and so that the two factors differ in exactly what the test is
    about -- the declared party label.

    ``party`` is the ``sector_declaration`` row's optional ``party_label``:
    ``None`` is the DEFAULT and is Bob's, which is what every instance of this
    repository declares.
    """
    coarse = canonical_coarse_graining(
        2,
        empty_letter=letters[0],
        single_letters={1: letters[1], 2: letters[2]},
        multiclick_letter=letters[3],
    )
    joint = tuple(
        (letter, setting) for setting in settings for letter in coarse.letters
    )
    declared_blocks = dict(PR_R1.declared_blocks)
    rows = ReceiverArtifactRows(
        mathematical_spec_version=FIXTURE_RECEIVER_VERSION,
        detection_alphabet=coarse.letters,
        photon_blocks={
            (letter, setting): (matrix([[declared_blocks[frozen]]]),)
            for letter, frozen in zip(
                coarse.letters, declared_blocks, strict=True
            )
            for setting in settings
        },
        high_photon_bounds=(
            HighPhotonBound.uniform(
                coarse.fibre(letters[3]),
                dict(PR_R1.slot_weights)["y_mc"],
                tuple(settings),
            ),
        ),
        bound_quantifier_domain=BoundQuantifierDomain(
            cutoff=0, settings=tuple(settings)
        ),
        dark_count_channel=product_form_dark_counts(
            2, {1: Fraction(3, 16), 2: Fraction(1, 4)}
        ),
        outcome_coarse_graining=coarse,
        bound_evaluation="floating_point",
        channel_grading=ChannelGrading(block_dimensions=(1,)),
        validation_results_present=True,
        declared_device_family=(),
        occupation_basis_order=(),
        inherited_assumption_ledger=tuple(
            InheritedAssumption(machine_key=key) for key in RECEIVER_LEDGER_KEYS
        ),
    )
    declaration = ProtocolDeclaration(
        probe_declaration=ProbeDeclaration(
            settings=tuple(settings), weights=dict(PR_R1.probe_weights)
        ),
        detection_alphabet=coarse.letters,
        photon_cutoff=0,
        source_mode=source_mode,
        joint_alphabet=joint,
        party_label=party,
    )
    request_fields: dict[str, object] = {
        "link_declarations": (
            LinkDeclaration(
                stage=LinkStage.RECEIVER,
                kind=LinkKind.FSS if route == "licensed" else LinkKind.WPFSS,
            ),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
        "route": route,
        "accepted_receiver_versions": (FIXTURE_RECEIVER_VERSION,),
        "requested_assurance": "estimate",
        "lattice_exponent": FIXTURE_KAPPA,
    }
    request_fields.update(overrides)
    return ReductionCall(
        rows, declaration, ReductionRequest(**request_fields)  # type: ignore[arg-type]
    )
