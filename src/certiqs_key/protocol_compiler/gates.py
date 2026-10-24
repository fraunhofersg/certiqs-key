"""PC9 -- the emission gates, and Table ``tab:gateoutcome`` as ONE TOTAL FUNCTION.

protocol-compiler 0.3.0 Definition ``def:eligible`` ((G1), (G2), (G3)(a)-(b)),
Definition ``def:homog``, Theorem ``thm:gates`` (i)-(iii), Table
``tab:gateoutcome``, Remark ``rem:degenerate``, Proposition
``prop:conservative`` and Remark ``rem:notfallback``.

THE OUTCOME IS NOT AN IMPLEMENTER'S CHOICE
==========================================
``thm:gates`` (ii) is the sentence this module exists to obey: if any gate fails,
"which of the TWO PERMITTED OUTCOMES it produces -- refusal, or emission of a
declaration that is not key-length-eligible -- is fixed by the gate outcome
table (``def:gate-outcome-table``, which holds Table ``tab:gateoutcome``) and
is NOT AN IMPLEMENTER'S CHOICE; ... It never drops a constraint entry silently,
never substitutes a default, never changes the source mode it was handed, and
never synthesizes a licence."

TWO OUTCOMES, AND NO FALLBACK. Emission in the weaker source mode WITH THE
FALLBACK RECORDED is not an outcome. There is no ``source_mode_request`` input: the
emitted mode is read off the transmitter artefact's marginal slot, and the transmitter
REFUSES a trusted-mode request at ``d_A >= 2`` carrying no certificate before any
artefact exists (``trusted_mode_without_certificate``). So no artefact this
module receives satisfies the premise of rows 2 and 4, which read "unreachable
through the transmitter artefact; refused there". ``prop:conservative`` KEEPS
ITS MATHEMATICS and is not a rule of emission. Accordingly, in
code: :class:`GateReport` has no ``fallback`` field, the two case ids
``G-T-D2-NOCERT-M0-FALLBACK`` and ``G-T-D2-NOCERT-M1-REFUSE`` are not
reachable, :class:`GateInputs` has no ``request`` axis, and the ``d_A = 1``
marginal slot is filled and recorded by the transmitter.

:func:`resolve_gates` is therefore written as a TOTAL FUNCTION over the case
space -- every combination of the seven decided facts maps to exactly one
outcome, and there is no fall-through, no default branch and no place where a
combination could reach the end unhandled. The frozen enumeration in
``tests/oracles/registry_protocol_compiler.py`` is its specification, and the
unit suite proves the mapping total against the same seven axes.

Two consequences of "not an implementer's choice" are easy to get wrong in the
conservative direction, and both are forbidden:

* a DOUBLE (G3) failure is still an EMISSION with ``key_length_eligible =
  false``, never an escalation to a refusal (case
  ``G-T-D2-CERT-M1-UNLIC-NOLICENCE``, rows 5 AND 6).

ROW 3 IS SCOPED TO EVERY ``d_A``, AND THAT IS WHY A FAILING CERTIFICATE AT
``d_A = 1`` IS REFUSED
======================================================================
Rows 2 and 4 carry the scope "at ``d_A >= 2``" and are unreachable in any case;
row 3 is scoped "trusted mode AT ANY ``d_A``, certificate PRESENT but one of
the five conditions fails". At ``d_A = 1`` the gate demands no certificate
(``transmitter/req:licence-scope``), "but one supplied there and failing is the same
defect in the same data", so this is the row ``def:compile``'s certificate
clause points at: "a certificate that does not verify is A DEFECT IN THE
SUPPLIED DATA, NOT A WEAKER CLAIM". :data:`GateCaseId.T_D1_CERTFAIL` carries
that route.

THE THIRD TOKEN IS REQUIRED, AND IT IS NOT A SOFTER "PASSED"
============================================================
Remark ``rem:degenerate``: gate (G3)(a) is vacuously true in untrusted-source
mode at any ``d_A`` (the entry type is already scalar by D(vi)); in
trusted-source mode it is a type check at every ``d_A``, ``d_A = 1`` included,
where it rejects nothing a producer cannot trivially avoid. Where it is
vacuous the compiler emits PASSED VACUOUSLY rather than PASSED in
``gate_report`` and does not report the vacuous pass as evidence of anything
(``req:vacuous-gate-report``), because a gate that reads as two independent
checks and is in fact one is exactly the kind of thing a later reader assumes
is still load-bearing.

:class:`GateEntry` therefore has NO boolean ``passed`` field. A caller that
wants to know whether a gate obstructs eligibility asks
:attr:`GateEntry.permits_eligibility`, whose docstring says what it is for; a
caller that wants to know what to REPORT reads ``verdict``, which keeps the
three tokens apart. There is no accessor that collapses ``passed vacuously``
into ``True`` and calls the result evidence.

WHAT IS DECIDED HERE AND WHAT IS ONLY TESTED FOR PRESENCE
=========================================================
Theorem ``thm:gates`` (i): (G1) by ``thm:validator-soundness``; (G2)'s five
conditions, (SR1)-(SR2) among them, as exact identities by
``thm:certificate-sufficiency`` (i); (G3)(a) "by READING THE TYPE OF THE DATUM
each entry's right-hand-side slot holds, which is its tag, and by nothing else";
(G3)(b) by a presence test. AND NOT: "(G2)'s clause (SR3) and (G3)(b)'s record
are attestations and are NOT DECIDABLE; they are tested for presence only", and
Requirement ``req:attestation-presence``: "for presence only, NEVER FOR TRUTH".
Nothing in this module inspects the content of either.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from certiqs_key.domain.constraints import ConstraintEntry, RhsTag
from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix
from certiqs_key.protocol_compiler.reasons import (
    GateVerdict,
    Refusal,
    RefusalReason,
    SourceMode,
)
from certiqs_key.protocol_compiler.transcript import (
    EMPTY_TRANSCRIPT,
    PredicateTranscript,
)
from certiqs_key.transmitter.reasons import CertificateForm

__all__ = [
    "GATE_IDS",
    "LICENSED_TAGS",
    "RETIRED_GATE_CASE_IDS",
    "CertificateState",
    "EmissionOutcome",
    "GateCaseId",
    "GateEntry",
    "GateId",
    "GateInputs",
    "GateReport",
    "GateResolution",
    "licensed_for_the_emitted_mode",
    "resolve_gates",
]


class GateId(StrEnum):
    """The gates of Definition ``def:eligible``, with (G3) split into its halves.

    Theorem ``thm:gates`` (i) splits (G3) itself: (a) "is decided by reading the
    type of the datum each entry's right-hand-side slot holds" and (b) "is a
    presence test", and Remark ``rem:degenerate`` is a statement
    about (a) alone. A report that carried one entry for (G3) could not say
    that its mechanical half was vacuous while its attestation half failed --
    which is the most misleading combination in the whole case space and the
    one the third token exists to keep visible.
    """

    G1 = "G1"
    G2 = "G2"
    G3A = "G3a"
    G3B = "G3b"


#: The four report entries, in Definition ``def:eligible``'s order.
GATE_IDS: Final[tuple[GateId, ...]] = tuple(GateId)


class CertificateState(StrEnum):
    """What the request carries in the ``source_replacement_certificate`` slot.

    ``PRESENT_FAILING`` means present and failing a condition of (G2) for its
    declared form (``thm:gates`` (ii')): one of the five pure-form conditions,
    among them (SR1) and (SR2), which Theorem ``thm:certificate-sufficiency``
    (i) makes finitely checkable; (E1)-(E3) or the slot identity of an
    ensemble presentation; or, for a block-form certificate, the form itself,
    (G2) admitting none. (SR3) is NOT one of them and never enters this
    classification.
    """

    ABSENT = "absent"
    PRESENT_PASSING = "present_passing"
    PRESENT_FAILING = "present_failing"


class EmissionOutcome(StrEnum):
    """The two kinds of outcome a compilation can have.

    ``thm:gates`` (ii)'s TWO permitted outcomes are these two, with the
    distinction inside an emission -- ``key_length_eligible`` true or false --
    carried by :class:`GateResolution` as a field of its own rather than as a
    third kind, so that no field has to be reconstructed from the outcome name.
    There is no third outcome (see the module docstring).
    """

    REFUSAL = "refusal"
    EMISSION = "emission"


class GateCaseId(StrEnum):
    """The region of the case space a resolution landed in.

    These are the identifiers of the frozen enumeration, carried so that a
    resolution can say WHICH rule produced it -- which is what makes a
    disagreement with the registry a located finding rather than a puzzle.
    """

    VALIDATOR_FAIL = "G-VALIDATOR-FAIL"
    U_M0 = "G-U-M0"
    U_M1_LIC = "G-U-M1-LIC"
    U_M1_NOLIC = "G-U-M1-NOLIC"
    T_D1_CERTFAIL = "G-T-D1-CERTFAIL"
    T_D1_M0 = "G-T-D1-M0"
    T_D1_M1_LIC = "G-T-D1-M1-LIC"
    T_D1_M1_NOLIC = "G-T-D1-M1-NOLIC"
    T_D2_CERT_M0 = "G-T-D2-CERT-M0"
    T_D2_CERT_M1_LIC_LICENCE = "G-T-D2-CERT-M1-LIC-LICENCE"
    T_D2_CERT_M1_LIC_NOLICENCE = "G-T-D2-CERT-M1-LIC-NOLICENCE"
    T_D2_CERT_M1_UNLIC_LICENCE = "G-T-D2-CERT-M1-UNLIC-LICENCE"
    T_D2_CERT_M1_UNLIC_NOLICENCE = "G-T-D2-CERT-M1-UNLIC-NOLICENCE"
    T_D2_CERTFAIL = "G-T-D2-CERTFAIL"


#: THE TWO CASE IDS OF ROWS 2 AND 4, kept as NAMES so that a reader can find
#: out why they are not cases of :class:`GateCaseId`. Both stand on a trusted-mode
#: REQUEST at ``d_A >= 2`` whose certificate was absent, which the transmitter refuses
#: before an artefact exists; neither is reachable through
#: :class:`~certiqs_key.transmitter.artifact.TransmitterArtifact`.
RETIRED_GATE_CASE_IDS: Final[tuple[str, ...]] = (
    "G-T-D2-NOCERT-M0-FALLBACK",
    "G-T-D2-NOCERT-M1-REFUSE",
)


@dataclass(frozen=True)
class GateEntry:
    """One gate's line of the report: engagement, verdict, and degeneration.

    ``engaged`` is ``None`` where the contract determines NO engagement -- on a
    refusal there is no emitted declaration for Definition ``def:eligible``'s
    conditions to be about, and the contract states no report content there.
    ``verdict`` is ``None`` wherever the contract fixes no token: for an
    unengaged gate it states the ENGAGEMENT (Theorem ``thm:band-a`` (iii) uses the
    phrase "not engaged") and no token, and picking one would be inventing
    vocabulary where the outputs table fixes exactly three values. NO FOURTH TOKEN IS
    EVER WRITTEN.
    """

    gate: GateId
    engaged: bool | None
    verdict: GateVerdict | None
    #: Present exactly when ``verdict`` is ``passed vacuously``: the record
    #: Remark ``rem:degenerate`` requires "where it applies", naming WHICH of
    #: its two cases degenerated.
    degeneration: str | None = None

    def __post_init__(self) -> None:
        """Keep the degeneration record and the third token in step."""
        vacuous = self.verdict is GateVerdict.PASSED_VACUOUSLY
        if vacuous and self.degeneration is None:
            raise MalformedInputError(
                "a `passed vacuously` verdict carries the degeneration record "
                "of Remark rem:degenerate (the ``gate_report`` output row)"
            )
        if not vacuous and self.degeneration is not None:
            raise MalformedInputError(
                "a degeneration record belongs only to a `passed vacuously` "
                "verdict; Remark rem:degenerate applies nowhere else"
            )
        if self.engaged is None and self.verdict is not None:
            raise MalformedInputError(
                "a gate with no subject carries no verdict: Definition "
                "def:eligible is stated on an EMITTED declaration"
            )

    @property
    def permits_eligibility(self) -> bool:
        """Whether this gate leaves ``key_length_eligible`` available.

        DELIBERATELY NOT NAMED ``passed``, and deliberately not a rendering of
        the verdict. Remark ``rem:degenerate`` forbids reporting a vacuous pass
        "as evidence of anything", so this predicate is for deciding the FLAG
        and for nothing else; what a reader is shown is
        :attr:`verdict`, which keeps the three tokens apart. An unengaged gate
        permits eligibility because a conditional with a false antecedent holds
        (Definition ``def:eligible``).
        """
        if self.engaged is not True:
            return True
        return self.verdict in (GateVerdict.PASSED, GateVerdict.PASSED_VACUOUSLY)


@dataclass(frozen=True)
class GateReport:
    """The ``gate_report`` output key: ONE ENTRY PER GATE, AND NOTHING ELSE.

    THERE IS NO ``fallback`` FIELD. The record ``prop:conservative`` requires
    at row 2 of the gate outcome table has no subject: that row is unreachable
    through the transmitter artefact, so such a field would be a slot nothing
    can ever fill.

    OPEN CHOICE ``OC-gate-report``, DECIDED HERE. ``interface.yaml`` records
    that the claims fix the three-valued vocabulary, that there is a verdict
    PER GATE with (G3) split into (a) and (b), and that a degeneration record
    accompanies a vacuous pass -- and that it fixes NO CONTAINER: "whether the
    report is a mapping keyed by gate name, a list of records, or a nested
    structure; the spelling of the three values as machine tokens; and the shape
    of the degeneration record itself".

    THE CONTAINER CHOSEN IS AN ORDERED TUPLE OF SELF-NAMING ENTRIES, in
    Definition ``def:eligible``'s order. Three reasons, and the first is the
    operative one: an entry that names its own gate cannot be misread by
    position, which a bare 4-tuple could; the ordered form preserves the order
    the claims state the gates in, which a mapping would leave to insertion
    order; and ``engaged = None`` stays distinguishable from ``verdict = None``,
    which a flattened "status string per gate" would collapse. The degeneration
    record is a sentence naming which case of ``rem:degenerate`` applied.

    THE PER-PREDICATE HALF OF THE ROW IS CARRIED BY :attr:`transcript`, AND
    WHAT IT DOES NOT CARRY IS DISCLOSED RATHER THAN LEFT TO BE DISCOVERED.
    The ``gate_report`` output row asks for more than a verdict per gate. It
    asks, "per exact predicate of Definition ``def:exact`` that the compiler
    decided, and per further decision of the kind the enumeration beneath this
    table delimits, THE OUTCOME, KEYED BY (source, element, block)", with "a
    FAILED predicate ... recorded with the block, outcome, signal or entry
    index at which it first failed, and (S) additionally with the index of the
    first inexact addition". That record is
    :class:`~certiqs_key.protocol_compiler.transcript.PredicateTranscript`; it
    is assembled by
    :func:`~certiqs_key.protocol_compiler.compile.compile_specification` from
    the deciders -- validation, chain, weights, feasibility through check V7,
    and the certificate's verification through gate (G2) -- and emitted by
    :meth:`as_machine_record` under ``predicates``. The open choice
    ``OC-gate-report`` leaves the CONTAINER open and not the CONTENT, so the
    container -- an ordered tuple in the order the decisions were taken, keyed
    as the row keys it -- is this module's choice and the content is the row's.

    TWO RESIDUES REMAIN, and they are the interface's
    ``implementation_status`` to state rather than this docstring's to hide.
    Both are questions for the HUMAN and not an implementer's to settle:

    * the exact admissibility of each conditional family ``{N_{u|t}}_u``,
      which the enumeration's last item calls "DECIDED and not assumed", is
      decided BY NOTHING IN THIS PACKAGE: neither
      :func:`~certiqs_key.protocol_compiler.weights.weighted_family`, which
      decides the weights, nor check V3, which decides the four conditions of
      Definition ``def:exact`` on the EMITTED family and not on the
      conditional ones. Recording it means ADDING the decision, which would
      change what the module refuses;
    * (C3)'s per-block legs are keyed by nothing, the enumeration not naming
      them while the row's first clause reaches them
      (:func:`~certiqs_key.protocol_compiler.chain._check_c3`).

    WHY NEITHER IS A DEFECT OF EMISSION, stated so that a reader can
    check it rather than take it: THE ROW IS A REPORT AND NOT A SECURITY
    DECISION. Every predicate the enumeration names but the first is DECIDED,
    exactly and before emission -- V1--V8 in
    :mod:`certiqs_key.protocol_compiler.validation`, (SR1)/(SR2) in
    :mod:`certiqs_key.transmitter.certificate`, (C1)--(C5) and (S1)--(S4) in
    :mod:`certiqs_key.protocol_compiler.chain`, the two emission decisions in
    :mod:`certiqs_key.protocol_compiler.weights` -- and the VERDICT each one
    feeds is emitted in full, as the gate outcome and, on a failure, as
    ``refusal`` naming the failed check and the index at which it failed. No
    number is admitted that should be refused and none is refused that should
    be admitted.

    The gap is disclosed, not excepted: the interface row is where a consumer
    reads what is recorded and what is not.
    """

    entries: tuple[GateEntry, ...]
    #: The per-predicate transcript of the compilation this report belongs to.
    #: DEFAULTED TO AN EMPTY ONE, which is this shape's advantage over a
    #: recorder threaded down: a report built without a transcript says
    #: "nothing was recorded" out loud, and a test can demand otherwise, where
    #: an optional recorder nobody passed would leave a record silently empty
    #: and indistinguishable from one whose decisions all held.
    transcript: PredicateTranscript = EMPTY_TRANSCRIPT

    def entry(self, gate: GateId) -> GateEntry:
        """Return one gate's line."""
        for candidate in self.entries:
            if candidate.gate is gate:
                return candidate
        raise KeyError(f"no entry for gate {gate}")

    def as_machine_record(self) -> dict[str, object]:
        """Return the report as a machine record. NO ``fallback`` KEY.

        TWO KEYS, AND THE SECOND IS THE ROW'S SECOND HALF. ``predicates``
        stands BESIDE ``gates`` and not inside it: the row states the two
        halves as two; a transcript entry is keyed by
        ``(source, element, block)`` and not by a gate; and most of the sources
        the row names -- V1--V8, (C1)--(S4), the compilation map -- are not
        gates at all, so nesting the transcript under a gate's entry would have
        had to pick a gate for a decision no gate took.
        """
        return {
            "gates": [
                {
                    "gate": str(entry.gate),
                    "engaged": entry.engaged,
                    "verdict": None if entry.verdict is None else str(entry.verdict),
                    "degeneration": entry.degeneration,
                }
                for entry in self.entries
            ],
            "predicates": self.transcript.as_record(),
        }


@dataclass(frozen=True)
class GateInputs:
    """The seven decided facts the gate outcome table is a function of.

    Each is DECIDED before this record is built -- the validator by
    :func:`certiqs_key.protocol_compiler.validation.validate`, the certificate
    by :func:`certiqs_key.transmitter.certificate.verify_certificate` RE-RUN
    HERE on the emitted data (``def:eligible`` (G2); the
    ``decide_never_infer`` convention), the licensing by
    :func:`licensed_for_the_emitted_mode`, the rest by inspection -- so that
    the mapping to an outcome is a pure function of seven values and can be
    proved total over their product.

    THE FIRST AXIS IS THE EMITTED MODE AND NOT A REQUEST. ``emitted_mode`` is
    read off the transmitter artefact's marginal slot and is not this module's
    to choose; there is no notion of a mode this module serves or declines to
    serve.
    """

    validator_passed: bool
    #: The mode the ARTEFACT emits, read off its marginal slot.
    emitted_mode: SourceMode
    alice_dim: int
    certificate: CertificateState
    has_constraint_entries: bool
    list_licensed: bool
    license_present: bool
    #: WHICH OF THE THREE DECLARED FORMS the artefact's certificate is in, read
    #: off the artefact and never a second datum (``transmitter/def:srcert``;
    #: ``def:spec`` (a')). ``pure`` is the accepted format's form and is the
    #: default, so an input record of today's shape is the record it was, field
    #: for field, and every case of the frozen enumeration is unmoved.
    certificate_form: CertificateForm = CertificateForm.PURE
    #: WHICH OF (DX4)'s TWO SLOTS the emitted declaration filled. ``povm`` is the
    #: accepted format's slot and the default. (G2) reads it for ONE decision: a
    #: presentation is admitted ONLY BESIDE AN ENSEMBLE-FORM DECLARATION,
    #: "nothing tying the declared {M_x} to it", which is "the transmitter's own
    #: rule for a POVM-form consumer and is what this module already does".
    alice_form: AliceForm = AliceForm.POVM

    def __post_init__(self) -> None:
        """Refuse the three combinations no transmitter artefact can present.

        THE THIRD IS WHAT MAKES ROWS 2 AND 4 UNREACHABLE IN
        CODE RATHER THAN ONLY IN PROSE. A trusted artefact at ``d_A >= 2``
        carries the licence record -- the transmitter refuses one without a
        certificate, with ``trusted_mode_without_certificate`` -- so an input
        record claiming otherwise is not a presentation of an artefact this
        module types, and no clause of ``def:eligible`` can be read against it.
        It is a hard error rather than a refusal for exactly the reason the
        other two are: refusing it would have to invent a reason string, and
        the string that names this situation belongs to the transmitter.
        """
        if self.alice_dim < 1:
            raise MalformedInputError(
                "d_A >= 1 (transmitter/def:source-spec; the "
                "``transmitter_artifact`` input row)"
            )
        if (
            self.emitted_mode is SourceMode.UNTRUSTED
            and self.certificate is not CertificateState.ABSENT
        ):
            raise MalformedInputError(
                "a source-replacement certificate is TRUSTED MODE ONLY "
                "(def:spec (a); transmitter/def:source-spec); an untrusted "
                "artefact carrying one is not a state of affairs this module "
                "admits"
            )
        if (
            self.emitted_mode is SourceMode.TRUSTED
            and self.alice_dim >= 2
            and self.certificate is CertificateState.ABSENT
        ):
            raise MalformedInputError(
                "a trusted artefact at d_A >= 2 carries the licence record: "
                "the transmitter refuses a trusted-mode request without a "
                "certificate with `trusted_mode_without_certificate`, which is "
                "why rows 2 and 4 of the gate outcome table are UNREACHABLE "
                "through the transmitter artefact (req:gate-outcomes)"
            )
        if not self.has_constraint_entries and not self.list_licensed:
            raise MalformedInputError(
                "the EMPTY LIST lies in the licensed class VACUOUSLY, its "
                "condition, on every entry, being an empty conjunction "
                "(def:homog)"
            )


@dataclass(frozen=True)
class GateResolution:
    """What the gates decided: the outcome, the flag, and the report."""

    case: GateCaseId
    outcome: EmissionOutcome
    #: The source mode of the EMITTED declaration, or ``None`` on a refusal.
    #: It is the artefact's own, passed through: this module CHANGES NO SOURCE
    #: MODE (thm:gates (ii)).
    emitted_mode: SourceMode | None
    key_length_eligible: bool | None
    report: GateReport
    emits_source_replacement_license: bool
    refusal: Refusal | None
    derives_from: str

    @property
    def refuses(self) -> bool:
        """Whether the compilation refuses, emitting NO declaration."""
        return self.outcome is EmissionOutcome.REFUSAL


# ---------------------------------------------------------------------------
#  THE ONE DECISION THE GATES ARE A FUNCTION OF
#
#  There is one. What goes into the marginal slot, including the
#  ``tau_A = [1]`` fill at ``d_A = 1``, is the transmitter's. The
#  emitted marginal is the ARTEFACT'S, passed through unchanged, fill included
#  and recorded as filled (``def:compile``; ``transmitter/req:marginal-fill``).
#  THIS MODULE FILLS NO SLOT, and ``rem:notfallback``'s ``tau_A = 1_A / d_A`` is
#  substituted at no dimension by either module.
# ---------------------------------------------------------------------------


def licensed_for_the_emitted_mode(
    marginal: Matrix | None,
    entries: tuple[ConstraintEntry, ...],
) -> bool:
    """Whether ``CList`` lies in the licensed class -- A TYPE CHECK ON THE TAG.

    Definition ``def:eligible`` (G3)(a): "``CList`` lies in the licensed class
    of the emitted source mode (Definition def:homog) -- A TYPE CHECK ON EACH
    ENTRY'S RIGHT-HAND-SIDE TAG, COMPARING NO NUMBERS." Definition
    ``def:homog``: "LICENSING IS THEREFORE A TYPE CHECK ON THE TAG, AND IT
    COMPARES NO NUMBERS."

    THE GATE IS A TYPE check
    on the right-hand side's declared tag, COMPARING NO NUMBERS AND DECIDING
    EXACTLY, and not a numerical test of an operator against ``c_k tau_A``.
    No pivot ratio is formed here and none may be introduced: the
    ``tau_A`` a supplier's attestation was made against is the same ``tau_A``
    the consumer constructs ``c_k tau_A`` from, so there is nothing to measure.

    THE LICENSED FORM IS ``homogeneous`` IN BOTH MODES. In trusted-source mode
    it is the scalar form, "and the right-hand side it denotes is then
    CONSTRUCTED as ``Theta_k := c_k tau_A``"; in untrusted-source mode "ONLY
    THE SCALAR FORM EXISTS". A ``general`` entry is "ADMISSIBLE INPUT ... BUT
    IT IS NOT LICENSED, so a list containing one CARRIES NO KEY-LENGTH CLAIM,
    WHICH IS THE FAIL-CLOSED DIRECTION."

    THE EMPTY LIST IS LICENSED VACUOUSLY, its condition being an empty
    conjunction -- which is why ``m = 0`` never reaches a licensing question.

    NO REQUEST ARGUMENT IS NEEDED. The one case that would need it is a
    TRUSTED request whose certificate is absent, which has "no ``tau_A`` for
    the consumer to construct ``c_k tau_A`` against", so no list with
    ``m >= 1`` could lie in the licensed class. That case is rows 2 and 4,
    which the transmitter refuses before an artefact exists, so THE EMITTED
    SLOT DECIDES THE MODE ON ITS OWN and this function reads it and nothing else.
    ``marginal`` is kept as an argument although both branches agree on it today: the
    licensed class is defined PER MODE (``def:homog``: "in untrusted-source
    mode ONLY THE SCALAR FORM EXISTS"), and a function that took only the
    entries would be asserting that the two classes coincide rather than
    recording that on the declared TAG they do.
    """
    if not entries:
        return True
    return all(entry.tag in LICENSED_TAGS for entry in entries)


#: THE LICENSED CLASS OF ``def:homog``, AS TAGS. ``homogeneous`` in either mode,
#: and ``party_local`` -- "the licensed class of Definition
#: def:homog contains, IN EITHER SOURCE MODE, the entries declared
#: ``party_local``; the decision remains A TYPE CHECK ON EACH ENTRY'S TAG and
#: compares no numbers" (``def:eligible`` (G3)(a)). It is the ONE widening of
#: an unsafe-direction gate, so it is a named constant rather than an inline
#: disjunction: what is licensed is data a reader finds in one place, and ``general`` is
#: not in it.
#:
#: WHAT THE WIDENING RESTS ON IS NOT DECIDED HERE. A ``party_local`` entry
#: "shrinks the feasible set further than its untagged reading does, and it is
#: sound only where every attack reaches ``Q_f`` through a channel acting on that
#: factor alone which carries the spectral certificate" -- a SUPPLIER's
#: certificate, stated by ``reductions``, attested by the ``attack_set_license``
#: record that (G3)(b) tests for, and decided by nothing in this module.
LICENSED_TAGS: Final[frozenset[RhsTag]] = frozenset(
    {RhsTag.HOMOGENEOUS, RhsTag.PARTY_LOCAL}
)


# ---------------------------------------------------------------------------
#  Table tab:gateoutcome, as one total function
# ---------------------------------------------------------------------------

_UNTRUSTED_DEGENERATION: Final[str] = (
    "Remark rem:degenerate, second case: in UNTRUSTED-source mode at any d_A "
    "the entry type is already scalar by D(vi), so (G3)(a) degenerates from a "
    "mathematical condition into a type check a well-formed declaration passes "
    "BY CONSTRUCTION. The gate rests entirely on (G3)(b), which no program can "
    "verify; this pass is NOT evidence of anything."
)

#: THERE IS NO d_A = 1 VACUOUS PASS. Remark ``rem:degenerate``: "In trusted-source mode
#: at d_A = 1 the gate is not vacuous": an entry tagged `general` declares a
#: matrix and fails a type check at every dimension, so it is unlicensed and
#: the declaration is emitted, not key-length-eligible, "and the consuming
#: engine reads its gate the same way" (``meat-core/rem:cgate``). The two
#: modules read a `general`-tagged 1x1 entry alike. `passed vacuously`
#: therefore survives IN UNTRUSTED-SOURCE MODE
#: ONLY, at any d_A, and an implementation must not carry the d_A = 1 pass
#: over.
_DIMENSION_ONE_VACUITY_WITHDRAWN: Final[str] = (
    "0.3.0: (G3)(a) is a TYPE CHECK AT EVERY d_A and is not vacuous at "
    "d_A = 1; see Remark rem:degenerate."
)

#: One line of the report before it is bound to a gate: engagement, verdict,
#: degeneration record.
type _Line = tuple[bool | None, GateVerdict | None, str | None]

_NOT_ENGAGED: _Line = (False, None, None)
_NO_SUBJECT: _Line = (None, None, None)
_G1_PASSED: _Line = (True, GateVerdict.PASSED, None)
_G1_FAILED: _Line = (True, GateVerdict.FAILED, None)
_PASSED: _Line = (True, GateVerdict.PASSED, None)
_FAILED: _Line = (True, GateVerdict.FAILED, None)


def _entry(gate: GateId, line: _Line) -> GateEntry:
    engaged, verdict, degeneration = line
    return GateEntry(
        gate=gate, engaged=engaged, verdict=verdict, degeneration=degeneration
    )


def _report(
    g1: _Line,
    g2: _Line,
    g3a: _Line,
    g3b: _Line,
    transcript: PredicateTranscript,
) -> GateReport:
    return GateReport(
        entries=(
            _entry(GateId.G1, g1),
            _entry(GateId.G2, g2),
            _entry(GateId.G3A, g3a),
            _entry(GateId.G3B, g3b),
        ),
        transcript=transcript,
    )


def resolve_gates(
    inputs: GateInputs,
    failed_check: str | None = None,
    *,
    transcript: PredicateTranscript | None = None,
) -> GateResolution:
    """Return the outcome the gate outcome table ``def:gate-outcome-table`` fixes.

    TOTAL over the seven axes: every admissible combination reaches exactly one
    ``return``, and the THREE inadmissible ones are refused by
    :meth:`GateInputs.__post_init__` as input-typing violations rather than
    given an outcome. ``failed_check`` names the check a (G1) refusal reports,
    which the caller has in hand from the validation result.

    NO BRANCH HERE SERVES A REQUEST OR TAKES A FALLBACK. The
    emitted mode is ``inputs.emitted_mode``, passed through to the resolution
    unchanged: ``thm:gates`` (ii), "it never ... changes the source mode".

    ``transcript`` IS KEYWORD-ONLY, DEFAULTED, AND NOT PART OF
    :class:`GateInputs`. That class is "the seven decided facts the gate
    outcome table is a function of", and the transcript is not one of them: the
    outcome table does not read it, no branch below branches on it, and putting
    it there would both make that docstring false and change what the frozen
    gate enumeration is a function of. It travels THROUGH this function onto
    the report it carries, and nothing here inspects it. Where a caller passes
    none -- which every test of the case space does -- the report carries an
    EMPTY transcript and says so.
    """
    recorded = EMPTY_TRANSCRIPT if transcript is None else transcript

    # --- (G1) dominates every other axis: Table tab:gateoutcome, row 1. -----
    if not inputs.validator_passed:
        named = failed_check or "the failed check among V1-V8"
        return GateResolution(
            case=GateCaseId.VALIDATOR_FAIL,
            outcome=EmissionOutcome.REFUSAL,
            emitted_mode=None,
            key_length_eligible=None,
            report=_report(
                _G1_FAILED, _NO_SUBJECT, _NO_SUBJECT, _NO_SUBJECT, recorded
            ),
            emits_source_replacement_license=False,
            refusal=Refusal(
                reason=RefusalReason.GATE_G1_FAILED,
                detail=(
                    f"gate (G1) failed at {named}: there is no declaration to "
                    "emit -- the candidate is not well-formed, or, at V7, has "
                    "not been shown to be. NOTHING DOWNSTREAM MAY CONSUME IT, "
                    "AT ANY TIER"
                ),
            ),
            derives_from="the gate outcome table, row 1",
        )

    emitted_trusted = inputs.emitted_mode is SourceMode.TRUSTED
    dimension_one = inputs.alice_dim == 1

    # --- (G2) BY FORM OF THE CERTIFICATE, BEFORE THE STATE AXIS IS READ. ----
    # def:eligible: "A presentation accompanying a POVM-FORM DECLARATION IS
    # REFUSED, nothing tying the declared {M_x} to it, WHICH IS THE
    # TRANSMITTER'S OWN RULE FOR A POVM-FORM CONSUMER and is what this module
    # already does." It is decided here and not through the three-valued state
    # axis because it is a decision about WHICH SLOTS ARE FILLED on two
    # artefacts and not about a number on one: the presentation may verify
    # perfectly and still have nothing in the declaration to be about. It lands
    # on ROW 3, where thm:gates (ii') puts a certificate present in any of the
    # three forms and failing a condition of that form, AND NO ROW IS ADDED.
    if (
        inputs.certificate_form is CertificateForm.ENSEMBLE_PRESENTATION
        and inputs.alice_form is not AliceForm.ENSEMBLE
    ):
        return GateResolution(
            case=(
                GateCaseId.T_D1_CERTFAIL
                if dimension_one
                else GateCaseId.T_D2_CERTFAIL
            ),
            outcome=EmissionOutcome.REFUSAL,
            emitted_mode=None,
            key_length_eligible=None,
            report=_report(
                _G1_PASSED,
                _NOT_ENGAGED if dimension_one else _FAILED,
                _NO_SUBJECT,
                _NO_SUBJECT,
                recorded,
            ),
            emits_source_replacement_license=False,
            refusal=Refusal(
                reason=RefusalReason.ENSEMBLE_PRESENTATION_WITHOUT_ENSEMBLE_FORM,
                detail=(
                    "the transmitter artefact presents its certificate as an "
                    "ENSEMBLE PRESENTATION beside a declaration whose Alice slot "
                    f"is {inputs.alice_form.value!r}. A presentation is admitted "
                    "ONLY BESIDE AN ENSEMBLE-FORM DECLARATION (def:eligible): "
                    "there is no declared Psi and no declared POVM to re-decide, "
                    "and nothing ties the POVM the declaration carries to the "
                    "blocks the presentation declares. This is the transmitter's "
                    "own rule for a POVM-form consumer (transmitter/def:srcert), "
                    "so it refuses nothing the transmitter admits"
                ),
            ),
            derives_from=(
                "def:eligible, (G2) by form of the certificate; the gate outcome "
                "table, row 3"
            ),
        )

    # --- (G2) BY FORM: A BLOCK-FORM CERTIFICATE IS REFUSED, WHATEVER ITS BLOCKS.
    # def:eligible: "A certificate declared in block form is refused at this
    # gate by its declared form, whatever its blocks, by row 3 of the gate
    # outcome table"; thm:gates (ii'), Step 5: the record is present and the
    # condition of (G2) it fails is the form itself, "so the outcome is a
    # refusal naming the form". It is decided before the state axis is read,
    # as the presentation rule above is, so that the refusal names the form
    # and not a numerical condition the form was never asked to meet; the
    # caller reports such a certificate as PRESENT_FAILING, which is what it
    # is. Row 3 is scoped to every d_A, so the case follows the dimension.
    #
    # IT FIRES ONLY WHERE A RECORD IS PRESENT (the state is not ABSENT), the
    # premise Step 5 argues from. A block form with no record -- d_A = 1, where
    # the transmitter emits no licence in any form (transmitter/
    # req:licence-scope) -- reads the state axis as ABSENT exactly as a pure
    # form does, so the two forms agree wherever no record exists. The same
    # reading covers BLOCK with ABSENT in untrusted mode, which no transmitter
    # artefact presents (an untrusted artefact declares no certificate in any
    # form and reads as PURE; transmitter/artifact.py refuses an untrusted
    # block form as untyped input): on a direct call it reaches the untrusted
    # rows as the pure form would, and is not refused by a form that no record
    # carries.
    if (
        inputs.certificate_form is CertificateForm.BLOCK
        and inputs.certificate is not CertificateState.ABSENT
    ):
        return GateResolution(
            case=(
                GateCaseId.T_D1_CERTFAIL
                if dimension_one
                else GateCaseId.T_D2_CERTFAIL
            ),
            outcome=EmissionOutcome.REFUSAL,
            emitted_mode=None,
            key_length_eligible=None,
            report=_report(
                _G1_PASSED,
                _NOT_ENGAGED if dimension_one else _FAILED,
                _NO_SUBJECT,
                _NO_SUBJECT,
                recorded,
            ),
            emits_source_replacement_license=False,
            refusal=Refusal(
                reason=RefusalReason.GATE_G2_FAILED,
                detail=(
                    "the transmitter artefact's source-replacement certificate "
                    "is declared in BLOCK FORM, and gate (G2) admits no "
                    "certificate declared in block form: it is refused by its "
                    "declared form, whatever its blocks (def:eligible, (G2) by "
                    "form of the certificate; thm:gates (ii'); the gate outcome "
                    "table, row 3). A block form declares positive semidefinite "
                    "blocks not known to be rank one, and admitting it would "
                    "widen (G2) in the unsafe direction "
                    "(rem:gate-by-certificate-form). Declare the certificate in "
                    "pure form or as an ensemble presentation"
                ),
            ),
            derives_from=(
                "def:eligible, (G2) by form of the certificate; the gate outcome "
                "table, row 3"
            ),
        )

    # --- The two refusals that come from a FAILING certificate. -------------
    if inputs.certificate is CertificateState.PRESENT_FAILING:
        certificate_refusal = Refusal(
            reason=RefusalReason.GATE_G2_FAILED,
            detail=(
                "the supplied source-replacement certificate fails one of the "
                "FIVE decided conditions of def:eligible (G2) -- Psi Hermitian, "
                "Psi^2 = Psi, tr Psi = 1 with its trace rounding nowhere, (SR1) "
                "and (SR2) -- or, for a certificate declared in another form, a "
                "condition of that form. THE CASE IT CATCHES IS ALL OF THEM; "
                "WHICH condition failed travels with the "
                "refusal the caller substitutes from the verification record "
                "(compile_specification, row 3), whose reason names it. A "
                "certificate that does not verify is A DEFECT IN THE SUPPLIED "
                "DATA, NOT A WEAKER CLAIM; silently demoting it to untrusted "
                "mode would hide a mis-specified source"
            ),
        )
        if dimension_one:
            # A FAILING CERTIFICATE AT d_A = 1 IS ROW 3. Rows 2 and 4 are
            # scoped to d_A >= 2; row 3 is scoped "trusted mode requested AT
            # ANY d_A, certificate PRESENT but one of the five conditions ...
            # fails", and def:compile says so of the certificate clause: "A
            # certificate that is present and fails any of the five conditions
            # of gate (G2) is refused AT EVERY d_A, row 3". The interface's
            # certificate_conditions rule gives the reason: at d_A = 1 the
            # gate demands no certificate (transmitter/req:licence-scope), but
            # one supplied there and failing is the same defect in the same
            # data. The recorded attribution agrees with the contract.
            return GateResolution(
                case=GateCaseId.T_D1_CERTFAIL,
                outcome=EmissionOutcome.REFUSAL,
                emitted_mode=None,
                key_length_eligible=None,
                report=_report(
                    _G1_PASSED, _NOT_ENGAGED, _NO_SUBJECT, _NO_SUBJECT, recorded
                ),
                emits_source_replacement_license=False,
                refusal=certificate_refusal,
                derives_from=(
                    "def:compile, the d_A = 1 certificate clause, which "
                    "refuses 'EXACTLY AS AT d_A >= 2 (row 3)' -- and row 3 "
                    "IS the row it points at, its scope being EVERY d_A"
                ),
            )
        return GateResolution(
            case=GateCaseId.T_D2_CERTFAIL,
            outcome=EmissionOutcome.REFUSAL,
            emitted_mode=None,
            key_length_eligible=None,
            report=_report(
                _G1_PASSED, _FAILED, _NO_SUBJECT, _NO_SUBJECT, recorded
            ),
            emits_source_replacement_license=False,
            refusal=certificate_refusal,
            derives_from="the gate outcome table, row 3",
        )

    certificate_present = inputs.certificate is CertificateState.PRESENT_PASSING

    # --- ROWS 2 AND 4 WOULD SIT HERE AND THERE IS NO BRANCH FOR THEM. ------
    # They served a trusted-mode REQUEST at d_A >= 2 whose certificate was
    # absent -- row 2 with the fallback, row 4 with a refusal. The transmitter
    # refuses such a request before an artefact exists, so no input this
    # function can be given satisfies their premise, and GateInputs refuses
    # the combination as an input-typing violation (req:gate-outcomes). An
    # implementation that reinstated a branch here would be reinstating the behaviour,
    # not covering a case.

    # --- Everything below EMITS. ------------------------------------------
    # (G2) is engaged exactly on a TRUSTED EMISSION at d_A >= 2: its premise
    # carries that scope, and transmitter/req:licence-scope forbids demanding
    # the attestation at d_A = 1 -- there "neither the engine nor a consumer of
    # its artefact demands the certificate or the attestation".
    #
    # AND WHERE IT IS ENGAGED IT PASSES, WHICH IS NOT A SHORTCUT. Two branches above
    # removed the other case: PRESENT_FAILING returned a refusal, and ABSENT at d_A >= 2
    # was refused by GateInputs.__post_init__ as an input-typing violation, rows 2 and 4
    # being unreachable through the transmitter artefact. So `certificate_present`
    # holds here by elimination, and
    # `_PASSED if certificate_present else _FAILED` would carry a _FAILED arm that
    # no input could reach -- and suggest a (G2) failure could still be
    # EMITTED rather than refused, which the gate outcome table does not allow.
    # The assertion is what keeps the elimination honest if a branch above
    # moves.
    g2: _Line
    if emitted_trusted and not dimension_one:
        assert certificate_present, (
            "a trusted emission at d_A >= 2 reaches this point only with a "
            "PASSING certificate: the failing case refused above and the "
            "absent case is refused by GateInputs (req:gate-outcomes)"
        )
        g2 = _PASSED
    else:
        g2 = _NOT_ENGAGED

    emits_license = emitted_trusted and not dimension_one

    if not inputs.has_constraint_entries:
        # (G3) is NOT ENGAGED: its premise is m >= 1.
        case = (
            GateCaseId.T_D2_CERT_M0
            if emitted_trusted and not dimension_one
            else GateCaseId.T_D1_M0
            if emitted_trusted
            else GateCaseId.U_M0
        )
        return GateResolution(
            case=case,
            outcome=EmissionOutcome.EMISSION,
            emitted_mode=inputs.emitted_mode,
            # KLE is decided by the gates AS THEY APPLY TO THE EMITTED
            # DECLARATION, and with m = 0 no (G3) premise is met.
            key_length_eligible=True,
            report=_report(_G1_PASSED, g2, _NOT_ENGAGED, _NOT_ENGAGED, recorded),
            emits_source_replacement_license=emits_license,
            refusal=None,
            derives_from="def:eligible (G1)-(G3)",
        )

    # --- (G3) IS engaged: m >= 1. -----------------------------------------
    # `passed vacuously` IS EMITTED IN UNTRUSTED-SOURCE MODE ONLY, at any d_A,
    # and NOT at d_A = 1 in trusted mode. Remark rem:degenerate withdraws the
    # d_A = 1 vacuity at 0.3.0: "an entry tagged `general` DECLARES A MATRIX
    # AND FAILS A TYPE CHECK AT EVERY DIMENSION", and this module takes the
    # stricter of the two readings -- fail-closed, costing a rate and never
    # claiming one. See _DIMENSION_ONE_VACUITY_WITHDRAWN.
    g3a: _Line
    if not emitted_trusted:
        g3a = (True, GateVerdict.PASSED_VACUOUSLY, _UNTRUSTED_DEGENERATION)
    else:
        g3a = _PASSED if inputs.list_licensed else _FAILED
    g3b: _Line = _PASSED if inputs.license_present else _FAILED
    report = _report(_G1_PASSED, g2, g3a, g3b, recorded)
    eligible = all(
        report.entry(gate).permits_eligibility for gate in (GateId.G3A, GateId.G3B)
    )

    if not emitted_trusted:
        case = GateCaseId.U_M1_LIC if inputs.license_present else GateCaseId.U_M1_NOLIC
    elif dimension_one:
        case = (
            GateCaseId.T_D1_M1_LIC
            if inputs.license_present
            else GateCaseId.T_D1_M1_NOLIC
        )
    elif inputs.list_licensed:
        case = (
            GateCaseId.T_D2_CERT_M1_LIC_LICENCE
            if inputs.license_present
            else GateCaseId.T_D2_CERT_M1_LIC_NOLICENCE
        )
    else:
        case = (
            GateCaseId.T_D2_CERT_M1_UNLIC_LICENCE
            if inputs.license_present
            else GateCaseId.T_D2_CERT_M1_UNLIC_NOLICENCE
        )
    return GateResolution(
        case=case,
        outcome=EmissionOutcome.EMISSION,
        emitted_mode=inputs.emitted_mode,
        key_length_eligible=eligible,
        report=report,
        emits_source_replacement_license=emits_license,
        refusal=None,
        derives_from=(
            "the gate outcome table, rows 5 and 6; def:eligible (G3); "
            "rem:degenerate"
        ),
    )
