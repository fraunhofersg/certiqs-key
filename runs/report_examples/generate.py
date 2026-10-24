"""Generate the committed key-rate report examples and their renderings.

WHY THIS EXISTS. The key-rate report is a projection of a run record. A
reviewer and every adapter need real records of every instance to read it on,
and a change to the report code needs a visible consequence: the snapshot test
(``tests/integration/test_report_examples.py``) re-renders every committed
record with the current code and compares it with the committed rendering. This
script is the one way those files change.

THESE ARE EXAMPLES, NOT ORACLES. A key length here is whatever the engine
computed at the commit the record names (``payload.provenance.engine``); it
pins nothing. A snapshot proves that the rendering is deterministic and that
a change to it was seen, not that it is right; correctness is held by the
hand-written expectations of the report's unit tests.

Usage::

    python -m runs.report_examples.generate [--instance ID ...]
                                            [--render-only | --check]

* no option: re-run every example (needs QICS; minutes), rewrite its records,
  then render them;
* ``--instance ID``: only the examples of that instance (repeatable);
* ``--render-only``: re-render the committed records without re-running, when
  only the report code or the claim-closure table changed;
* ``--check``: re-render and compare with the committed files, writing
  nothing; exit 1 naming every file that differs, is missing or is stale.

Each example folder is generated whole and is deleted before it is rewritten:
nothing in one is hand-edited.

THE DOCUMENT ROUTE. Two
examples run a CUSTOM protocol document rather than a packaged instance, so
that the committed reports show what a custom document's run adds: its own
"Declared in the protocol document" items (a receiver characterisation, a
declared POVM; bb84's and decoy_bb84's examples show their templates' own).
Each document is a
packaged template customised the way its header says (a new identity, no
reserved strings) and then edited, here in :func:`_y_basis` and
:func:`_port_grams`; the record carries the document's canonical tree, so
the document a report was computed on is in its record.

TWO ENTANGLEMENT-BASED DOCUMENTS cover role classes no packaged instance's default
has: Bob holding the key (:func:`_bbm92_holder_b`) and the only public
choice declared at the second station (:func:`_bbm92_choice_at_bob`). The
role guards read them with the other examples
(``tests/unit/test_role_guards.py``, ``tests/integration/
test_role_guards_fresh.py``).
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any, Final, Literal

from certiqs_key.runs.config import AlphaSearchSettings, RunConfig, SolverSettings
from certiqs_key.runs.report import (
    build_report,
    build_sweep_report,
    default_contract_link,
    default_excerpt_link,
    pages_site_serves,
    render_excerpts_html,
    render_excerpts_markdown,
    render_html,
    render_markdown,
    render_sweep_html,
    render_sweep_markdown,
)
from certiqs_key.runs.report.__main__ import read_lambda_ec
from certiqs_key.runs.report._render import report_pointers
from certiqs_key.runs.report.model import Outcome, SweepPoint
from certiqs_key.runs.sweep import grid

__all__ = [
    "CONTRACT_BASE",
    "EXAMPLES",
    "EXAMPLES_ROOT",
    "GZIP_ABOVE",
    "SOLVER",
    "Example",
    "committed_files",
    "main",
    "read_record",
    "record_paths",
    "rendered",
]

#: The folder every example lives in, one subfolder per example.
EXAMPLES_ROOT: Final[Path] = Path(__file__).resolve().parent

#: From ``runs/report_examples/<example>/`` to the repository root, so a
#: contract link opens the committed PDF from a checkout.
#: A sweep's point reports sit one folder deeper and take one more ``../``.
CONTRACT_BASE: Final[str] = "../../../"

#: A record larger than this is written ``.json.gz``, within a 1 MB budget
#: per committed file.
GZIP_ABOVE: Final[int] = 512 * 1024

#: The solver budget of every example: a handful of Frank-Wolfe iterations,
#: enough for a record of every stage, nowhere near convergence. The method
#: is ``fw`` by name, not by default: a snapshot must repeat exactly, and the
#: default ``auto`` spends wall-clock time, not iterations.
SOLVER: Final[SolverSettings] = SolverSettings(method="fw", max_iterations=5)

#: The budget of the entanglement-based examples: ten iterations. At five
#: the two documents' first-order bound stays negative (a Frank-Wolfe gap
#: near 1.8 after five steps from their starting point, so a key length of
#: 0); at ten it is positive (gap below 3e-3), at about nine seconds a run.
#: For the ``bbm92`` template, on the receiver's rigorous weight, the fifth
#: iterate's gap is 1.47 and its key 0, at the edge of convergence rather
#: than at any defect of the weight; at six steps and more every weight
#: gives a positive key.
EB_DOCUMENT_SOLVER: Final[SolverSettings] = SolverSettings(
    method="fw", max_iterations=10
)

#: The budget of the prepare-and-measure examples whose first-order bound
#: is still negative at five steps: twenty iterations. Measured on the
#: receiver's rigorous weight: ``decoy_bb84``
#: gives 0 at five, ten and fifteen steps (h_lb -0.19 at fifteen) and
#: 4,110,454 at twenty (h_lb 0.041, about 13 s), every run certified.
PM_LONG_SOLVER: Final[SolverSettings] = SolverSettings(
    method="fw", max_iterations=20
)

#: The opt-in outer alpha search of the ``alpha-search-bb84`` example (record
#: schema 0.24.0): a grid of three and one refinement, so four runs.
ALPHA_SEARCH: Final[AlphaSearchSettings] = AlphaSearchSettings(
    lower=1e-4, upper=0.1, coarse_points=3, refine_steps=1
)

#: Written as every record's ``created_by``.
CREATED_BY: Final[str] = "runs.report_examples.generate"

#: A security budget whose sum ``eps_pa + eps_ev + 2 eps_auth`` is at least 1,
#: so meat-core refuses the run at ``solve`` (``security_statement_vacuous``).
VACUOUS_EPS_AUTH: Final[float] = 0.5

#: The repository root, where the packaged templates are.
REPOSITORY: Final[Path] = EXAMPLES_ROOT.parents[1]


@dataclass(frozen=True)
class Example:
    """One committed example: a folder of records and their renderings."""

    #: The folder under :data:`EXAMPLES_ROOT`.
    name: str
    #: The instance package (``instances.<instance>``) every record is of.
    instance: str
    #: ``run``: one ``record.json[.gz]`` and ``report.{md,html}``. ``sweep``:
    #: ``run-NNNN.json[.gz]``, ``sweep.{md,html}`` and ``points/NNNN.{md,html}``.
    kind: Literal["run", "sweep"]
    #: The configurations, from the instance's surface module.
    configs: Callable[[ModuleType], tuple[RunConfig, ...]]
    #: The outcome each record must have; the generator refuses to write
    #: an example whose run came out otherwise, and a ``key-length`` outcome
    #: whose key length is 0 (:func:`_refusal_to_write`).
    outcomes: tuple[Outcome, ...]
    #: For a protocol document: builds its surface, which then stands for
    #: ``instances.<instance>`` (``instance`` is the document's id).
    document: Callable[[], Any] | None = None


def _default(surface: ModuleType) -> tuple[RunConfig, ...]:
    """Return the default configuration with the examples' solver budget."""
    return (surface.default_config(solver=SOLVER),)


def _eb_document(surface: ModuleType) -> tuple[RunConfig, ...]:
    """Return the default configuration with :data:`EB_DOCUMENT_SOLVER`.

    The entanglement-based examples' budget: the two bbm92 documents and the
    bbm92 template.
    """
    return (surface.default_config(solver=EB_DOCUMENT_SOLVER),)


def _pm_long(surface: ModuleType) -> tuple[RunConfig, ...]:
    """Return the default configuration with :data:`PM_LONG_SOLVER`."""
    return (surface.default_config(solver=PM_LONG_SOLVER),)


def _refused(surface: ModuleType) -> tuple[RunConfig, ...]:
    """Return the default configuration with a vacuous security budget."""
    return (surface.default_config(solver=SOLVER, eps_auth=VACUOUS_EPS_AUTH),)


def _searched(surface: ModuleType) -> tuple[RunConfig, ...]:
    """Return the default configuration with the outer alpha search opted into."""
    return (surface.default_config(solver=SOLVER, alpha_search=ALPHA_SEARCH),)


def _qber_sweep(surface: ModuleType) -> tuple[RunConfig, ...]:
    """Two qber points, and a third whose budget is vacuous (a refused point)."""
    base: RunConfig = surface.default_config(solver=SOLVER)
    refused = base.with_(
        model={**base.model, "qber": Fraction(3, 50)}, eps_auth=VACUOUS_EPS_AUTH
    )
    return (*grid(base, model={"qber": [Fraction(1, 50), Fraction(1, 25)]}), refused)


# --------------------------------------------------------------------------
# The protocol documents
# --------------------------------------------------------------------------

HALF: Final[str] = "1/2"
QUARTER: Final[str] = "1/4"
#: The Y-basis projectors, ``[re, im]`` entries: (|0> +- i|1>)(<0| -+ i<1|)/2.
P_Y0: Final[dict[str, Any]] = {"matrix": [[HALF, [0, "-1/2"]], [[0, HALF], HALF]]}
P_Y1: Final[dict[str, Any]] = {"matrix": [[HALF, [0, HALF]], [[0, "-1/2"], HALF]]}


def _customised(instance: str, identity: dict[str, str]) -> dict[str, Any]:
    """Return a packaged template's tree made custom, as its header says.

    A new identity (no ``readme``, no ``record_label``) and no station's
    ``declared_by``: the strings only the packaged template may write.
    """
    from instances.declared.reader import parse_text

    path = REPOSITORY / "instances" / instance / "protocol.yaml"
    tree: dict[str, Any] = parse_text(path.read_text(encoding="utf-8"), syntax="yaml")
    tree["identity"] = identity
    for station in tree["stations"]:
        station.pop("declared_by", None)
    return tree


def _y_basis() -> Any:
    """BB84 with the Y basis in place of X: a custom Band-A document.

    The bb84 template, with Alice's X states and Bob's X measurement replaced
    by the Y basis, whose states are genuinely complex; the announcements and
    the acceptance rules follow. Bob's measurement is declared directly, so
    the report lists it as declared by you (A-SPEC, A-IDEAL).
    """
    from instances.declared import load

    tree = _customised(
        "bb84",
        {
            "id": "qubit_bb84_y",
            "title": "Qubit BB84 in the Z and Y bases",
            "summary": "The bb84 template with the Y basis in place of X: a custom "
            "protocol document, run as a report example.",
        },
    )
    tree["alphabets"]["signal"]["product"]["dims"]["basis"] = ["Z", "Y"]
    ann = tree["alphabets"]["ann"]["union"][1]
    ann["product"]["label"] = "(Y,{bit})"
    ann["attrs"] = {"basis": "Y"}
    source = tree["source"]
    states = source["states"]
    source["weights"] = {
        "(Z,0)": {"expr": "alice_z / 2"},
        "(Z,1)": {"expr": "alice_z / 2"},
        "(Y,0)": {"expr": "alice_x / 2"},
        "(Y,1)": {"expr": "alice_x / 2"},
    }
    source["states"] = {
        "(Z,0)": states["(Z,0)"],
        "(Z,1)": states["(Z,1)"],
        "(Y,0)": P_Y0,
        "(Y,1)": P_Y1,
    }
    measurement = tree["stations"][0]["measurement"]["choice_family"]
    for family in (source["alice"]["choice_family"], measurement):
        family["choices"] = ["Z", "Y"]
        family["weights"] = {"Z": family["weights"]["Z"], "Y": family["weights"]["X"]}
        family["conditional_alphabets"] = {"Z": [0, 1], "Y": [0, 1]}
    measurement["conditional_elements"] = {
        "Z": measurement["conditional_elements"]["Z"],
        "Y": {"0": P_Y0, "1": P_Y1},
    }
    public = tree["public"]
    public["announcements"]["alice"]["map"][1]["value"] = "(Y,{x.bit})"
    public["announcements"]["bob"]["map"][1]["value"] = "(Y,{v.outcome})"
    for rule in public["acceptance"]["map"]:
        for key in ("A.basis", "B.basis"):
            if rule.get("when", {}).get(key) == "X":
                rule["when"][key] = "Y"
    return load(tree)


def _port_grams() -> Any:
    """Optical BB84 with Bob's receiver declared by its four port Grams.

    The optical_bb84 template, with the element graph replaced by the ideal
    receiver's port Grams (route i): numbers the engine takes as the device's
    rather than derives from catalogue optics, so the report lists them as
    declared by you (A-TRUST).
    """
    from instances.declared import load

    tree = _customised(
        "optical_bb84",
        {
            "id": "optical_bb84_port_grams",
            "title": "Optical BB84 with a receiver declared by its port Grams",
            "summary": "The optical_bb84 template with Bob's receiver declared by "
            "its four port Grams: a custom protocol document, run as a report "
            "example.",
        },
    )
    bob = tree["stations"][0]["measurement"]
    bob["route"] = "port_grams"
    bob["elements"] = []
    bob["edges"] = []
    bob["port_grams"] = {
        "H": {"matrix": [[HALF, 0], [0, 0]]},
        "V": {"matrix": [[0, 0], [0, HALF]]},
        "D": {"matrix": [[QUARTER, QUARTER], [QUARTER, QUARTER]]},
        "A": {"matrix": [[QUARTER, "-1/4"], ["-1/4", QUARTER]]},
    }
    return load(tree)


def _bbm92_holder_b() -> Any:
    """BBM92 with Bob holding the key: a custom entanglement-based document.

    The bbm92 template with ``key.holder: B``: the key bit is read
    off Bob's station readout, Alice keeps the test coin and announces first.
    The report's key-holder wording, A-KEYREG and the laboratory rows are
    then read with B as the holder.
    """
    from instances.declared import load

    tree = _customised(
        "bbm92",
        {
            "id": "bbm92_holder_b",
            "title": "BBM92 with Bob holding the key",
            "summary": "The bbm92 template with the key read off Bob's station: a "
            "custom entanglement-based protocol document, run as a report example.",
        },
    )
    tree["public"]["key"]["holder"] = "B"
    return load(tree)


def _bbm92_choice_at_bob() -> Any:
    """BBM92 with the test coin at Bob's station only: a custom EB document.

    The bbm92 template with its ``choice_weighting`` moved from Alice's
    station to Bob's, so the run's only public choice is declared at the
    SECOND measured factor (guard G6 on a real run: A-COIN is emitted from
    the second factor). The coin's holder announces
    first, so the two transcript messages swap senders: Bob's message carries
    gen/test and his class or letter, Alice's answers with hers. Alice still
    holds the key.
    """
    from instances.declared import load

    tree = _customised(
        "bbm92",
        {
            "id": "bbm92_choice_at_bob",
            "title": "BBM92 with Bob's test coin",
            "summary": "The bbm92 template with the test coin drawn at Bob's "
            "station: a custom entanglement-based protocol document, run as a "
            "report example.",
        },
    )
    alice, bob = tree["stations"]
    bob["choice_weighting"] = alice.pop("choice_weighting")
    first, second = tree["public"]["transcript"]["messages"]
    first["sender"], second["sender"] = "B", "A"
    for row in tree["parameters"]["table"]:
        if row["name"] == "test_fraction":
            row["meaning"] = (
                "Probability that Bob's public coin makes a round a test round, "
                "in which both parties announce their full outcome"
            )
    return load(tree)


#: Every example, in the order they are generated. One per instance at its
#: default configuration, one refused record, one sweep with a refused
#: point, one run whose alpha the outer alpha search
#: chose (record schema 0.24.0), two custom protocol documents, and
#: two custom entanglement-based documents (key
#: holder B; the only public choice at the second station).
EXAMPLES: Final[tuple[Example, ...]] = (
    Example("bb84", "bb84", "run", _default, ("key-length",)),
    Example("bbm92", "bbm92", "run", _eb_document, ("key-length",)),
    Example("decoy_bb84", "decoy_bb84", "run", _pm_long, ("key-length",)),
    Example("optical_bb84", "optical_bb84", "run", _default, ("key-length",)),
    Example("refused", "bb84", "run", _refused, ("refused",)),
    Example("alpha-search-bb84", "bb84", "run", _searched, ("key-length",)),
    Example(
        "sweep-bb84", "bb84", "sweep", _qber_sweep,
        ("key-length", "key-length", "refused"),
    ),
    Example(
        "document-qubit_bb84_y", "qubit_bb84_y", "run", _default, ("key-length",),
        document=_y_basis,
    ),
    Example(
        "document-optical_bb84_port_grams", "optical_bb84_port_grams", "run",
        _default, ("key-length",), document=_port_grams,
    ),
    Example(
        "document-bbm92_holder_b", "bbm92_holder_b", "run", _eb_document,
        ("key-length",), document=_bbm92_holder_b,
    ),
    Example(
        "document-bbm92_choice_at_bob", "bbm92_choice_at_bob", "run", _eb_document,
        ("key-length",), document=_bbm92_choice_at_bob,
    ),
)


# --------------------------------------------------------------------------
# Reading and rendering the committed records
# --------------------------------------------------------------------------


def _is_record_file(path: Path) -> bool:
    return path.is_file() and (
        path.name.endswith(".json") or path.name.endswith(".json.gz")
    )


def record_paths(example: Example) -> list[Path]:
    """Return the example's committed record files, in point order (by name)."""
    folder = EXAMPLES_ROOT / example.name
    stem = "record" if example.kind == "run" else "run-"
    if not folder.is_dir():
        return []
    return sorted(
        (
            path for path in folder.iterdir()
            if _is_record_file(path) and path.name.startswith(stem)
        ),
        key=lambda path: path.name,
    )


def read_record(path: Path) -> dict[str, Any]:
    """Read a ``.json`` or ``.json.gz`` record."""
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            data = json.load(handle)
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} holds no JSON object")
    return data


def _render_run(
    record: dict[str, Any], path: Path, base: str, stem: str, excerpts: str
) -> dict[str, str]:
    """Return a run's report and its record excerpts, as the CLI writes them.

    ``base`` prefixes the contract and the repository links (both relative to
    the file); ``stem`` names the report file and ``excerpts`` its excerpts,
    each without the extension. The HTML is the page the Pages site serves,
    so it links a repository path only where the site serves it
    (``--pages-site``); the Markdown, read in the repository, links every one.
    """
    report = build_report(record)
    link = default_contract_link(base)
    estimate = read_lambda_ec(path)
    files: dict[str, str] = {}
    for extension, render, write in (
        ("md", render_markdown, render_excerpts_markdown),
        ("html", render_html, render_excerpts_html),
    ):
        files[f"{stem}.{extension}"] = render(
            report, contract_link=link,
            excerpt_link=default_excerpt_link(f"{excerpts}.{extension}"),
            repo_base=base, lambda_ec=estimate,
            repo_served=pages_site_serves if extension == "html" else None,
        )
        files[f"{excerpts}.{extension}"] = write(
            record, report, report_href=f"{stem}.{extension}"
        )
    return files


def rendered(example: Example) -> dict[str, bytes]:
    """Return every rendering of the example's committed records, by file name.

    The files ``python -m certiqs_key.runs.report`` writes with
    ``--contract-base ../../../ --repo-base ../../../`` and ``--out`` a file
    (a sweep: ``--out <folder>``, which adds the point reports under
    ``points/``), the HTML with ``--pages-site`` too: each report with its
    record excerpts beside it (``record.<ext>``; a point's
    ``points/<NNNN>.record.<ext>``).
    """
    paths = record_paths(example)
    records = [read_record(path) for path in paths]
    if example.kind == "run":
        (record,) = records
        (path,) = paths
        texts = _render_run(record, path, CONTRACT_BASE, "report", "record")
        return {name: text.encode("utf-8") for name, text in texts.items()}
    sweep = build_sweep_report(records)
    link = default_contract_link(CONTRACT_BASE)
    files: dict[str, bytes] = {}
    renderers = (("md", render_sweep_markdown), ("html", render_sweep_html))
    shown = sweep["common"]["setup_point"]
    pointers = (
        frozenset() if shown is None
        else frozenset(report_pointers(build_report(records[shown])))
    )
    for extension, render in renderers:

        def point_link(point: SweepPoint, extension: str = extension) -> str:
            return f"points/{point['index']:04d}.{extension}"

        files[f"sweep.{extension}"] = render(
            sweep, contract_link=link, point_link=point_link,
            repo_base=CONTRACT_BASE,
            excerpt_link=None if shown is None else default_excerpt_link(
                f"points/{shown:04d}.record.{extension}"
            ),
            excerpt_pointers=pointers,
            repo_served=pages_site_serves if extension == "html" else None,
        ).encode("utf-8")
    for point, record, path in zip(sweep["points"], records, paths, strict=True):
        stem = f"{point['index']:04d}"
        for name, text in _render_run(
            record, path, "../" + CONTRACT_BASE, stem, f"{stem}.record"
        ).items():
            files[f"points/{name}"] = text.encode("utf-8")
    return files


def committed_files(example: Example) -> set[str]:
    """Return every file under the example's folder, as POSIX relative paths."""
    folder = EXAMPLES_ROOT / example.name
    if not folder.is_dir():
        return set()
    return {
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file()
    }


def _write_rendered(example: Example) -> None:
    """Write every rendering and delete any file that is neither one nor a record."""
    folder = EXAMPLES_ROOT / example.name
    files = rendered(example)
    keep = set(files) | {path.name for path in record_paths(example)}
    for name in committed_files(example) - keep:
        (folder / name).unlink()
    for name, content in files.items():
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _check(example: Example) -> list[str]:
    """Return the example's files that differ from a fresh rendering."""
    folder = EXAMPLES_ROOT / example.name
    expected = rendered(example)
    records = {path.name for path in record_paths(example)}
    problems = [
        f"{example.name}/{name}: differs" if (folder / name).is_file() else
        f"{example.name}/{name}: missing"
        for name, content in sorted(expected.items())
        if not (folder / name).is_file() or (folder / name).read_bytes() != content
    ]
    problems += [
        f"{example.name}/{name}: stale (not generated)"
        for name in sorted(committed_files(example) - set(expected) - records)
    ]
    if not records:
        problems.append(f"{example.name}: no record")
    return problems


# --------------------------------------------------------------------------
# Re-running the examples
# --------------------------------------------------------------------------


def _refusal_to_write(example: Example, results: Sequence[Any]) -> str | None:
    """Return why the runs' results may not be written as this example, if so.

    Each record must have the example's outcome, and a ``key-length`` outcome
    a positive key: the outcome reads only whether a key length is reported,
    so a run whose bound clamped to a key of 0 would pass as one.
    """
    outcomes = tuple(result["outcome"] for result in results)
    if outcomes != example.outcomes:
        return f"the runs came out {outcomes}, not {example.outcomes}"
    zero = [
        index
        for index, result in enumerate(results)
        if result["outcome"] == "key-length" and not result["key_length"]
    ]
    if zero:
        return (
            f"run(s) {zero} report a key length of 0, which a key-length "
            "example's outcome does not stand for"
        )
    return None


def _run(example: Example, scratch: Path) -> None:
    """Re-run one example and replace its folder: records, then renderings."""
    from instances import surface_of

    from certiqs_key.runs.record import write_record
    from certiqs_key.runs.surface import InstanceIdentity
    from certiqs_key.runs.sweep import sweep
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = (
        surface_of(example.instance)
        if example.document is None
        else example.document()
    )
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    runner = surface.runner(
        QicsSectorChoiOracle(), scratch / example.name, created_by=CREATED_BY
    )
    swept = sweep(
        example.configs(surface), runner, created_by=CREATED_BY, instance=identity
    )
    refusal = _refusal_to_write(
        example,
        [build_report(point.record.as_dict())["sections"]["result"] for point in swept],
    )
    if refusal is not None:
        raise SystemExit(
            f"{example.name}: {refusal}; the committed example is left as it was"
        )
    folder = EXAMPLES_ROOT / example.name
    if folder.exists():
        shutil.rmtree(folder)
    for point in swept:
        stem = "record" if example.kind == "run" else f"run-{point.index:04d}"
        path = folder / f"{stem}.json"
        write_record(path, point.record)
        if path.stat().st_size > GZIP_ABOVE:
            _compress(path)
    _write_rendered(example)


def _compress(path: Path) -> None:
    """Replace ``<name>.json`` by ``<name>.json.gz``, the same bytes compressed.

    The gzip header carries no file name and a zero time, so the same record
    always compresses to the same bytes.
    """
    target = path.with_name(path.name + ".gz")
    with target.open("wb") as raw, gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0
    ) as handle:
        handle.write(path.read_bytes())
    path.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    """Re-run, re-render or check the examples; return the exit code."""
    parser = argparse.ArgumentParser(
        prog="python -m runs.report_examples.generate",
        description="Generate the committed key-rate report examples.",
    )
    parser.add_argument(
        "--instance", action="append",
        choices=sorted({example.instance for example in EXAMPLES}),
        help="only the examples of this instance (repeatable)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--render-only", action="store_true",
                      help="re-render the committed records without re-running")
    mode.add_argument("--check", action="store_true",
                      help="compare a fresh rendering with the committed files")
    args = parser.parse_args(argv)
    chosen = [
        example for example in EXAMPLES
        if args.instance is None or example.instance in args.instance
    ]
    if args.check:
        problems = [problem for example in chosen for problem in _check(example)]
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            print("regenerate with: python -m runs.report_examples.generate "
                  "--render-only (and read the diff)", file=sys.stderr)
            return 1
        print(f"ok: {len(chosen)} example(s) render as committed")
        return 0
    if args.render_only:
        for example in chosen:
            _write_rendered(example)
            print(f"rendered {example.name}")
        return 0
    with tempfile.TemporaryDirectory(prefix="certiqs-report-examples-") as scratch:
        for example in chosen:
            _run(example, Path(scratch))
            print(f"generated {example.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
