"""The core reaches probe conditioning through one seam and names none of its claims.

Motivation: the receiver's probe-conditioning submodule is a removable leaf
(its interface's ``removability`` block; ``harness/export_manifest.yaml``,
group ``probe-conditioning``), and the public tree is exported without it.
Deleting it must leave every other module importable and a receiver with
source modes refused by name. Three properties make that so, and this file
holds each:

* THE IMPORT HALF. No module of the package, of ``instances/`` or of
  ``runs/`` imports the submodule's code, :mod:`certiqs_key.receiver.probe`;
  the one seam, :func:`certiqs_key.receiver.settings.setting_construction`,
  loads it by name, and only ``receiver/settings.py`` spells that name. An
  import anywhere else would turn the cut into an ``ImportError``. The static
  scan sees an import statement; a fresh interpreter that constructs a
  probe-free receiver shows that no path loads the submodule at run time
  either.
* THE VOCABULARY HALF. No tier outside the submodule names one of its claim
  or equation labels, in a literal or in prose, and neither does the core
  receiver's interface: a docstring or an interface row pointing at a claim
  that the cut removes is a pointer to nothing. The weight route read
  through the conditioned receiver, ``reductions/wpfss/cor:route-conditioned``,
  goes with the submodule and is named nowhere outside it either; the run
  tier recognises both results by their closure in the claim-closure table.
* THE REFUSAL. Where the submodule is absent, a receiver with source modes is
  refused with ``probe_conditioning_submodule_absent`` at validation, and a
  probe-free receiver is constructed as before.

This file survives the cut: its scans read the code that stays, the label
list is its own, and the check that the list is the submodule's skips where
the submodule's claim files are gone. ``tests/harness/test_removability.py``
cuts the group from a copy of the tree and checks the rest.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from receiver_povm_support import probe_receiver_request

from certiqs_key.receiver import settings as settings_module
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.reasons import RefusalReason
from certiqs_key.receiver.settings import (
    CONDITIONING_MODULE,
    UNCONDITIONED,
    setting_construction,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "certiqs_key"
SUBMODULE_CODE = PACKAGE / "receiver" / "probe.py"
SEAM = PACKAGE / "receiver" / "settings.py"
CORE_INTERFACE = ROOT / "spec" / "modules" / "receiver" / "interface.yaml"
SUBMODULE_CLAIMS = (
    ROOT / "spec" / "modules" / "receiver" / "probe-conditioning" / "claims"
)

#: Every claim and equation label the probe-conditioning submodule's claim
#: files carry, and the one claim outside it that the cut removes with it.
SUBMODULE_LABELS = (
    "cor:emitted-conditioned",
    "cor:rigorous-conditioned",
    "eq:Prep",
    "eq:cohbreak",
    "eq:cohfock",
    "eq:condcomponents",
    "eq:conditioned-data",
    "eq:condmap",
    "eq:condmc",
    "eq:counterX",
    "eq:emitted-conditioned",
    "eq:entire",
    "eq:exact-conditioned-click",
    "eq:exact-effgram",
    "eq:schur",
    "eq:schurform",
    "eq:schurmono",
    "eq:variational",
    "lem:coherentdet",
    "lem:schurmono",
    "prop:conditioned-family",
    "prop:exact-conditioned",
    "rem:coherent-breaks",
    "rem:collapse-fails",
    "rem:condpair",
    "rem:tsm",
    "rem:twoinstances",
    "rem:windowdecidable",
    "req:conditional-family-only",
    "thm:channel-block-diagonal",
    "thm:conditional-povm",
    "thm:gaussian-schur",
)
#: The wpfss claim the cut removes with the submodule.
ROUTE_CONDITIONED = "cor:route-conditioned"


def _shipped_files() -> list[Path]:
    """Return every Python file of the package, ``instances/`` and ``runs/``."""
    return sorted(
        path
        for top in (PACKAGE, ROOT / "instances", ROOT / "runs")
        for path in top.rglob("*.py")
        if path != SUBMODULE_CODE
    )


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _imports_the_submodule(tree: ast.AST) -> bool:
    """Return whether a module imports :data:`CONDITIONING_MODULE` statically."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == CONDITIONING_MODULE for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == CONDITIONING_MODULE:
                return True
            if node.module == "certiqs_key.receiver" and any(
                alias.name == "probe" for alias in node.names
            ):
                return True
    return False


@pytest.mark.contract
def test_no_shipped_module_imports_the_submodule() -> None:
    offenders = [
        _relative(path)
        for path in _shipped_files()
        if _imports_the_submodule(ast.parse(path.read_text(encoding="utf-8-sig")))
    ]
    assert offenders == []


@pytest.mark.contract
def test_only_the_seam_spells_the_submodule_s_module_name() -> None:
    offenders = [
        _relative(path)
        for path in _shipped_files()
        if path != SEAM and CONDITIONING_MODULE in path.read_text(encoding="utf-8-sig")
        and any(
            CONDITIONING_MODULE in node.value
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig")))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and "\n" not in node.value
        )
    ]
    assert offenders == []


@pytest.mark.contract
@pytest.mark.parametrize("label", (*SUBMODULE_LABELS, ROUTE_CONDITIONED))
def test_no_shipped_tier_names_a_claim_the_cut_removes(label: str) -> None:
    """The shared tiers, the core and the run tier cite only what survives.

    A label is matched as a whole: ``eq:schur`` does not match inside
    ``eq:schurform``.
    """
    pattern = re.compile(re.escape(label) + r"(?![\w-])")
    offenders = [
        _relative(path)
        for path in _shipped_files()
        if pattern.search(path.read_text(encoding="utf-8-sig"))
    ]
    assert offenders == [], (label, offenders)


@pytest.mark.contract
def test_the_label_list_is_the_submodule_s_own() -> None:
    """The list above is the submodule's labels, so the net misses none.

    SKIPPED WHERE THE SUBMODULE IS GONE, which is the state the removability
    check runs in: its claim files are exactly what the cut removes.
    """
    if not SUBMODULE_CLAIMS.is_dir():
        pytest.skip("the probe-conditioning submodule is not in this tree")
    declared = re.compile(r"\\label\{([^}]*)\}")
    found = {
        label
        for path in SUBMODULE_CLAIMS.glob("*.tex")
        for label in declared.findall(path.read_text(encoding="utf-8-sig"))
    }
    assert found == set(SUBMODULE_LABELS)


@pytest.mark.contract
def test_without_the_submodule_a_receiver_with_source_modes_is_refused_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The seam's refusal, as a tree without the submodule meets it.

    A request with source modes and a lit setting is refused at validation
    with ``probe_conditioning_submodule_absent`` and no artifact; the seam
    itself raises rather than import what is not there. Where the submodule
    is absent this is the tree's own state and the patch changes nothing.
    """
    monkeypatch.setattr(settings_module, "conditioning_present", lambda: False)
    emission = construct_receiver(probe_receiver_request())
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.PROBE_CONDITIONING_SUBMODULE_ABSENT
    assert "probe-conditioning submodule" in emission.refusal.detail
    with pytest.raises(HypothesisError, match="probe_conditioning_submodule_absent"):
        setting_construction(1)
    assert setting_construction(0) is UNCONDITIONED


@pytest.mark.contract
def test_a_probe_free_receiver_never_reaches_the_submodule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``Inp_S`` empty is the core's construction, with or without the submodule."""
    monkeypatch.setattr(settings_module, "conditioning_present", lambda: False)
    from instances.common.optics import ReceiverParameters, receiver_request

    emission = construct_receiver(receiver_request(ReceiverParameters(photon_cutoff=1)))
    assert emission.refusal is None
    assert emission.artifact is not None


#: A probe-free construction in a fresh interpreter, which reports whether the
#: submodule's code was loaded on the way.
PROBE_FREE_SNIPPET = """
import sys
from certiqs_key.receiver.construct import construct_receiver
from instances.common.optics import ReceiverParameters, receiver_request

emission = construct_receiver(receiver_request(ReceiverParameters(photon_cutoff=1)))
assert emission.artifact is not None, emission.refusal
print("certiqs_key.receiver.probe" in sys.modules)
"""


@pytest.mark.contract
def test_a_probe_free_construction_never_imports_the_submodule() -> None:
    """The import half at run time: ``Inp_S`` empty never loads ``probe.py``.

    A fresh interpreter, so that no earlier test's import is counted; the
    tree's own ``src/`` and root first on the path, so that the tree under
    test is the one imported.
    """
    path = os.pathsep.join(
        [str(ROOT / "src"), str(ROOT), os.environ.get("PYTHONPATH", "")]
    )
    proc = subprocess.run(
        [sys.executable, "-c", PROBE_FREE_SNIPPET],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
        env={**os.environ, "PYTHONPATH": path},
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    assert proc.stdout.strip() == "False"


@pytest.mark.contract
@pytest.mark.parametrize("label", (*SUBMODULE_LABELS, ROUTE_CONDITIONED))
def test_the_core_interface_names_no_claim_the_cut_removes(label: str) -> None:
    """The core receiver's interface rows are stated over the setting family.

    What the submodule adds to a row where a receiver has source modes is in
    the submodule's own interface (``core_rows``), which goes with it.
    """
    pattern = re.compile(r"(?<![\w:-])" + re.escape(label) + r"(?![\w-])")
    assert not pattern.search(CORE_INTERFACE.read_text(encoding="utf-8")), label
