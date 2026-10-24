"""The hard errors of this instance -- and the rule that a REFUSAL is not one.

The same split :mod:`certiqs_key.runs.errors` draws, derived from its base so that
``except RunError`` still catches everything a run can raise
(``instances.common.honest.depolarized_bell_pair.HonestModelError`` is the
sibling precedent).

A REFUSAL by this instance is not here. The rows adapter declines by returning a
:class:`~certiqs_key.runs.pipeline.AdapterRefusal`, which
:func:`~certiqs_key.runs.pipeline.run_slice` carries out as a
:class:`~certiqs_key.runs.pipeline.SliceRefusal` like any module's -- because a
declaration this instance cannot make exactly is an answer about the device, and
a caller is entitled to see which block it was.
"""

from __future__ import annotations

from certiqs_key.runs.errors import RunError

__all__ = [
    "OpticalBB84Error",
    "OpticalDeviceError",
    "OpticalModelError",
    "OpticalReceiverError",
]


class OpticalBB84Error(RunError):
    """Base class for every hard error this instance raises."""


class OpticalModelError(OpticalBB84Error):
    """The optical channel model was asked for something it does not model.

    A ``float`` where an exact rational is required, a transmittance outside
    ``[0, 1]``, a declaration whose physical system is not the truncated Fock
    space this model lives on. None of these is a refusal by anything: no
    contract is about such an argument.
    """


class OpticalDeviceError(OpticalBB84Error):
    """This instance was asked for a DECLARATION it does not write.

    A route name that is not one of
    :data:`~instances.common.passive_device.ROUTES`,
    or a carried entry whose constants cannot be recovered from the baseline
    emission it is supposed to be about. Not a refusal by ``reductions``:
    that module refuses the strings it is handed, and this is about a string it
    would never be handed.
    """


class OpticalReceiverError(OpticalBB84Error):
    """The declared optics cannot be assembled into a receiver at all.

    A parameter outside its domain, a mode that no port maps, an angle given as
    something other than an exact rational multiple of the declared unit. The
    receiver's own refusals are NOT this: ``receiver`` declines with a
    machine-readable reason and that reaches the caller as an outcome.
    """
