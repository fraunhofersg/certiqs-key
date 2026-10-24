"""The stages of a run, as one vocabulary.

WHY THE ENUM HAS A MODULE OF ITS OWN
====================================
:mod:`certiqs_key.runs.pipeline` runs the stages and
:mod:`certiqs_key.runs.flow` records which of them happened, so both need the
names and neither may import the other. The vocabulary is therefore below both,
which is also the honest place for it: the stage list is what the run tier OWNS
(spec/architecture.md 3.3, "the ORDER -- the stages of section 6, and the rule
that a refusal by any of them is carried as data rather than raised"), and an
owned thing is not a detail of the function that happens to drive it.

THE ENUM COVERS THE WHOLE PATH AND NOT ONLY THE REFUSALS
========================================================
A vocabulary of the stages that can conformingly decline would name a stage
only for a refusal. The composition-flow view needs every stage of the path,
refusable or not, and a SECOND vocabulary beside this one would be a parallel
flow schema. So the five refusable stages keep their names and their strings -- they are
recorded in refusals and compared in tests -- and the rest of the path joins them.

**Which of them can refuse is a fact about the modules, not about this enum.**
Three of the four modules on the path can decline in their own vocabulary
(``protocol-compiler``, ``statistics``, ``receiver`` twice and ``reductions``);
``meat-core`` does not refuse but may emit no key length, which is a RESULT and
is carried as one; and the run tier's own stages raise rather than refuse,
because a bundle this tier failed to write is its defect and not a declination.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["SliceStage"]


class SliceStage(StrEnum):
    """One stage of the path, named after the owning module's step.

    Named after the OWNING MODULE's stage rather than after a symptom, so that
    a caller acting on a refusal acts on the check that refused.
    """

    #: The device prologue. On the path only where a device was declared; the
    #: direct finite route declares its POVM and its identity link instead.
    RECEIVER_CONSTRUCTION = "receiver_construction"
    #: Both ``receiver``'s own adapter and the caller's rows adapter refuse
    #: here. They share a stage because they are the same act -- handing the
    #: receiver's numbers to the squasher -- and the reason string says which.
    RECEIVER_DOCKING = "receiver_docking"
    REDUCTION = "reduction"
    #: The rest of the path, on every route.
    COMPILATION = "compilation"
    #: The instance's honest channel model, on the emitted declaration. It is
    #: not proof-critical (spec/architecture.md 3.4) and the provider does not
    #: refuse: a provider that cannot model a declaration raises, and nothing
    #: is substituted. The run tier refuses here once, before the provider is
    #: called, under its own ``factored_loss_not_applied`` (a station compiled
    #: at a factored loss below one and a provider that does not declare it
    #: applies that loss; receiver/detector-imperfections/
    #: req:loss-before-evaluation).
    HONEST_MODEL = "honest_model"
    ACCEPTANCE_CONSTRUCTION = "acceptance_construction"
    #: The compiled declaration read into ``meat-core``'s own type, with the
    #: acceptance set, the rounds and the key-length parameters this run
    #: composed (the consumer reads the supplier).
    DOCKING = "docking"
    BUNDLE_WRITE = "bundle_write"
    #: READ BACK, not reused: what is solved is what is on the disk.
    BUNDLE_READ = "bundle_read"
    #: Bundle validation, the generated maps and the Frank-Wolfe loop are ONE
    #: stage here because they are one call: ``meat-core`` validates before it
    #: solves anything (spec/architecture.md 3.6) and the run tier never sees
    #: the seam between them. What each of them did is on the result.
    SOLVE = "solve"
