"""The honest-model library: the instances' exact channel models, used by name.

WHY A LIBRARY. The protocol document (``instances/declared/``) lets a user
name one of the instances' honest models instead of writing Python, so the
models live here, behind one interface
(:class:`~instances.common.honest.interface.LibraryModel`), and the instances
use them from here too: one model, two consumers, no copy that can drift.
Nothing is added to the proof path; an honest model is the simulator side of
spec/architecture.md 4.3.

:data:`MODELS` is the registry by library name. :func:`build` is the one entry
point a protocol document uses: it refuses an unknown name
(``library_model_unknown``), a binding that does not give exactly the model's
parameters (``library_model_binding_invalid``) and a structure the model does
not model (its preconditions, the same code), and only then builds the
providers. The Python instances, whose structure is fixed by their own code,
call a model's ``providers`` directly; ``tests/unit/test_honest_library.py``
holds every instance's context against its model's preconditions.

``tables`` holds the honest statistics given as data (a table, a raw joint
table, an envelope), which the document offers beside the models.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Final

from certiqs_key.runs.pipeline import HonestProvider, RawJointProvider
from instances.common.honest import (
    coherent_pulses,
    depolarized_bell_pair,
    ideal_pair,
    single_photon_loss_depolarizing,
    spdc_pair,
)
from instances.common.honest.interface import (
    HonestContext,
    LibraryModel,
    SourceFacts,
    StationFacts,
    station_from_device,
)
from instances.declared.errors import DocumentError, DocumentReason

__all__ = [
    "MODELS",
    "BuiltModel",
    "HonestContext",
    "LibraryModel",
    "SourceFacts",
    "StationFacts",
    "build",
    "station_from_device",
]

#: Every library model by its name.
MODELS: Final[Mapping[str, LibraryModel]] = {
    model.name: model
    for model in (
        depolarized_bell_pair.MODEL,
        single_photon_loss_depolarizing.MODEL,
        coherent_pulses.MODEL,
        ideal_pair.MODEL,
        spdc_pair.MODEL,
    )
}


@dataclass(frozen=True)
class BuiltModel:
    """A bound library model: its two providers and its honest-model note.

    ``note`` is the context's live note: pass this dict to the run unchanged,
    so that what a model adds to it at run time reaches the record.
    """

    honest: HonestProvider
    raw: RawJointProvider | None
    note: dict[str, Any]


def build(
    name: str, bind: Mapping[str, Fraction | str], context: HonestContext
) -> BuiltModel:
    """Look up, bind and check one library model, then build its providers.

    Raises:
        DocumentError: ``library_model_unknown`` for a name not in
            :data:`MODELS`; ``library_model_binding_invalid`` for a binding
            that misses or adds a parameter, or for a context that fails the
            model's preconditions (the first failure is named).
    """
    model = MODELS.get(name)
    if model is None:
        raise DocumentError(
            f"no honest model is called {name!r}; the library has {sorted(MODELS)}",
            reason=DocumentReason.LIBRARY_MODEL_UNKNOWN,
            path="/honest/library",
        )
    missing = [p for p in model.parameters if p not in bind]
    extra = sorted(set(bind) - set(model.parameters))
    if missing or extra:
        raise DocumentError(
            f"the honest model {name!r} binds exactly {list(model.parameters)}; "
            f"missing {missing}, not a parameter {extra}",
            reason=DocumentReason.LIBRARY_MODEL_BINDING_INVALID,
            path="/honest/bind",
        )
    model.preconditions(context)
    # THE NOTE IS THE LIVE ONE, made before the providers: a model that records
    # what it declared at run time (the SPDC model's Gram preparation) writes
    # into ``context.note``, and the caller hands this same dict to the run.
    note = model.note(bind, context)
    context.note = note
    honest, raw = model.providers(bind, context)
    return BuiltModel(honest=honest, raw=raw, note=note)
