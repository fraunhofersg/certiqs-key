"""The run facade with a protocol document in place of an instance.

A caller's document -- an object, or a ``.json``/``.yaml``/``.yml`` file of at
most 1 MiB -- is read as a CUSTOM document, refused in the facade's one shape
(``stage: "document"``, the document layer's ``reason``, the JSON ``path``),
keyed into a job by its digest, stored in ``request.json`` as its canonical
tree, and rebuilt by the worker with the reader ``prepare`` used. These tests
hold each of those, and that nothing a caller reaches reads a document as
packaged (the reader's trusted entry must never be reachable from MCP
input).

No test here solves: the worker is not spawned (``_spawn`` is replaced), and
the worker's own loading step, :func:`runs.facade.worker.load_request`, is
called directly on the ``request.json`` a start wrote.
"""

from __future__ import annotations

import copy
import json
import re
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from runs.facade import core, jobs, worker
from tests.support.declared_documents import BB84_DOCUMENT, bb84_tree, y_basis

ROOT = Path(__file__).resolve().parents[2]
REFUSAL_KEYS = {"refused", "stage", "reason", "path", "detail"}


@pytest.fixture
def jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(jobs.JOBS_ENV, str(tmp_path / "jobs"))
    monkeypatch.setenv(jobs.MAX_JOBS_ENV, "50")
    return tmp_path / "jobs"


class _NoWorker:
    """Stands for a worker process that was never started."""

    def poll(self) -> int:
        return 0


@pytest.fixture
def no_worker(jobs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Start jobs without a worker, on a clean engine, so reuse is decided."""
    identity = core.engine_identity()
    monkeypatch.setattr(
        core,
        "engine_identity",
        lambda: {**identity, "commit": "c" * 40, "dirty": False},
    )
    monkeypatch.setattr(jobs, "_spawn", lambda directory: _NoWorker())
    return jobs_dir


def custom_tree(name: str = "my_bb84") -> dict[str, Any]:
    """Return the bb84 template as a custom document, as an agent edits it."""
    tree = bb84_tree()
    del tree["identity"]["readme"], tree["identity"]["record_label"]
    tree["identity"]["id"] = name
    return tree


def y_tree() -> dict[str, Any]:
    tree = custom_tree("my_y_bb84")
    y_basis(tree)
    return tree


def _untimed(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _untimed(v) for k, v in value.items() if k != "wall_time_s"}
    if isinstance(value, list):
        return [_untimed(v) for v in value]
    return value


# ---------------------------------------------------------------------------
#  The refusal envelope
# ---------------------------------------------------------------------------


def _unknown_key(tree: dict[str, Any]) -> None:
    tree["stations"][0]["measurement"]["colour"] = "blue"


def _packaged_id(tree: dict[str, Any]) -> None:
    tree["identity"]["id"] = "bb84"


def _instances_label(tree: dict[str, Any]) -> None:
    tree["stations"][0]["declared_by"] = "instances.bb84.declare"


def _bad_reference(tree: dict[str, Any]) -> None:
    tree["source"]["weights"]["(Z,0)"] = {"expr": "alice_q / 2"}


@pytest.mark.parametrize(
    ("edit", "reason", "path"),
    [
        (_unknown_key, "document_schema_violation", "/stations/0/measurement"),
        (_packaged_id, "reserved_identity", "/identity/id"),
        (_instances_label, "reserved_identity", "/stations/0/declared_by"),
        (_bad_reference, "unknown_parameter_reference", "/source/weights/(Z,0)"),
    ],
    ids=["schema", "packaged-id", "instances-label", "reference"],
)
def test_a_document_refusal_has_the_one_shape_with_a_path(
    edit: Any, reason: str, path: str, jobs_dir: Path
) -> None:
    tree = custom_tree()
    edit(tree)
    config = core.describe_instance("bb84")["default_config"]
    for refused in (
        core.describe_instance(document=tree),
        core.prepare("", config, document=tree),
        jobs.start_run("", config, document=tree),
    ):
        assert set(refused) >= REFUSAL_KEYS, refused
        assert refused["refused"] is True
        assert refused["stage"] == core.DOCUMENT_STAGE
        assert refused["reason"] == reason
        assert refused["path"].startswith(path), refused
    assert not jobs_dir.exists() or not any(jobs_dir.iterdir())


def test_the_packaged_template_itself_is_a_reserved_identity() -> None:
    """The bb84 template, passed back unedited, is refused: it is not packaged."""
    refused = core.describe_instance(document=bb84_tree())
    assert refused["reason"] == "reserved_identity"
    refused = core.describe_instance(document_file=str(BB84_DOCUMENT))
    assert refused["reason"] == "reserved_identity"


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("bad.yaml", "identity: [unclosed\n"),
        ("bad.json", '{"format": '),
        ("document.txt", "format: certiqs-key/protocol-document\n"),
        ("large.yaml", "#" * (core.MAX_DOCUMENT_FILE_BYTES + 1)),
        ("missing.yaml", None),
        ("folder.yaml", "directory"),
    ],
    ids=["yaml", "json", "extension", "too-large", "missing", "directory"],
)
def test_a_document_file_that_is_not_a_document_is_unreadable(
    tmp_path: Path, name: str, content: str | None
) -> None:
    path = tmp_path / name
    if content == "directory":
        path.mkdir()
    elif content is not None:
        path.write_text(content, encoding="utf-8")
    refused = core.describe_instance(document_file=str(path))
    assert set(refused) >= REFUSAL_KEYS, refused
    assert (refused["stage"], refused["reason"]) == ("document", "document_unreadable")


def test_a_document_is_one_object_given_once(tmp_path: Path) -> None:
    path = tmp_path / "mine.json"
    path.write_text(json.dumps(custom_tree()), encoding="utf-8")
    both = core.describe_instance(document=custom_tree(), document_file=str(path))
    assert both["reason"] == "document_unreadable"
    listed = core.describe_instance(document=[custom_tree()])
    assert listed["reason"] == "document_unreadable"
    text = core.describe_instance(document=path.read_text(encoding="utf-8"))
    assert text["reason"] == "document_unreadable"


def test_the_instance_argument_must_name_the_document() -> None:
    config = core.describe_instance("bb84")["default_config"]
    refused = core.prepare("bb84", config, document=custom_tree())
    assert refused["reason"] == "document_schema_violation"
    assert refused["path"] == "/identity/id"
    prepared = core.prepare("my_bb84", config, document=custom_tree())
    assert prepared["kind"] == "preparation"


# ---------------------------------------------------------------------------
#  Describing and preparing a document
# ---------------------------------------------------------------------------


def test_describing_a_document_validates_it_as_the_instance_it_copies(
    tmp_path: Path,
) -> None:
    """The customised bb84 template describes as the bb84 instance does."""
    python = core.describe_instance("bb84")
    path = tmp_path / "mine.json"
    path.write_text(json.dumps(custom_tree()), encoding="utf-8")
    for described in (
        core.describe_instance(document=custom_tree()),
        core.describe_instance("my_bb84", document_file=str(path)),
    ):
        assert described["document"]["id"] == "my_bb84"
        assert described["document"]["packaged"] is False
        assert len(described["document"]["digest"]) == 64
        assert described["conversions"] == []
        assert described["default_config"] == python["default_config"]
        assert described["instance"]["parameters"] == python["instance"]["parameters"]
        assert described["presets"] == python["presets"]


def test_a_prepared_document_names_itself_and_what_it_declared() -> None:
    tree = y_tree()
    described = core.describe_instance(document=tree)
    envelope = core.prepare("", described["default_config"], document=tree)
    assert envelope["document"] == described["document"]
    record = envelope["preparation"]
    assert record["protocol_document"]["digest"] == described["document"]["digest"]
    summary = core.preparation_summary(envelope)
    assert summary["document"]["digest"] == described["document"]["digest"]
    assert "protocol_document" in summary["parts"]
    assert [item["kind"] for item in summary["user_declared"]] == ["receiver_povm"]
    assert core.preparation_file_stem(envelope).startswith("declared_my_y_bb84-")
    assert len(json.dumps(summary)) < 60_000


def test_a_shipped_template_s_summary_lists_what_it_declares() -> None:
    """A packaged instance's own declarations are the user's to vouch for too.

    The user still takes responsibility for these if using the key rates.
    """
    envelope = core.prepare("bb84", core.describe_instance("bb84")["default_config"])
    summary = core.preparation_summary(envelope)
    assert summary["document"] is None
    assert [item["kind"] for item in summary["user_declared"]] == ["receiver_povm"]
    assert summary["user_declared"][0]["assumptions"] == ["A-SPEC", "A-IDEAL"]
    assert core.preparation_file_stem(envelope).startswith("bb84-")


# ---------------------------------------------------------------------------
#  Jobs: the key, the namespace, request.json and the worker's reload
# ---------------------------------------------------------------------------


def test_a_document_job_is_keyed_by_its_digest(no_worker: Path) -> None:
    tree = y_tree()
    config = core.describe_instance(document=tree)["default_config"]
    first = jobs.start_run("", config, document=tree)
    assert first["reused"] is False
    assert re.fullmatch(r"declared_my_y_bb84-[0-9a-f]{12}-1", first["job"])
    digest = core.describe_instance(document=tree)["document"]["digest"]
    assert first["document"] == {"id": "my_y_bb84", "digest": digest}
    assert jobs.job_directory(first["job"]).is_dir()
    again = jobs.start_run("my_y_bb84", config, document=copy.deepcopy(tree))
    assert (again["job"], again["reused"]) == (first["job"], True)
    assert again["document"]["digest"] == digest
    # An annotation is not read, but it is part of the document: a new digest,
    # a new job.
    annotated = {**copy.deepcopy(tree), "annotations": {"source": "a lab note"}}
    other = jobs.start_run("", config, document=annotated)
    assert other["reused"] is False and other["job"] != first["job"]
    assert other["document"]["digest"] != digest
    # The packaged instance with the same configuration is another namespace.
    packaged = jobs.start_run("bb84", core.describe_instance("bb84")["default_config"])
    assert packaged["job"].startswith("bb84-") and packaged["document"] is None
    listed = {entry["job"]: entry for entry in jobs.list_jobs()}
    assert listed[first["job"]]["document"]["digest"] == digest


def _written_with_decimals(directory: Path) -> Path:
    """Write the bb84 template as YAML text with an unquoted decimal default."""
    text = BB84_DOCUMENT.read_text(encoding="utf-8")
    text = text.replace("  readme: instances/bb84/README.md\n", "")
    text = text.replace("  record_label: bb84\n", "")
    text = text.replace("  id: bb84\n", "  id: my_decimal_bb84\n")
    text = text.replace("    default: 0\n", "    default: 0.02\n", 1)
    assert "default: 0.02" in text
    path = directory / "mine.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _with_a_float() -> dict[str, Any]:
    tree = custom_tree("my_float_bb84")
    tree["parameters"]["table"][0]["default"] = 0.02
    return tree


@pytest.mark.parametrize("form", ["yaml-decimal", "object-float"])
def test_prepare_and_the_worker_read_one_document_alike(
    no_worker: Path, tmp_path: Path, form: str
) -> None:
    """One canonical tree, read alike on both sides."""
    from certiqs_key.runs import preparation_record

    if form == "yaml-decimal":
        source: dict[str, Any] = {
            "document_file": str(_written_with_decimals(tmp_path))
        }
    else:
        source = {"document": _with_a_float()}
    described = core.describe_instance(**source)
    # A decimal in text is read exactly; a binary64 float is its own exact
    # value, with the replacement recorded.
    exact = "1/50" if form == "yaml-decimal" else str(Fraction(0.02))
    assert Fraction(described["default_config"]["model"]["qber"]) == Fraction(exact)
    if form == "object-float":
        assert [c["path"] for c in described["conversions"]] == [
            "/parameters/table/0/default"
        ]
        assert (
            described["default_config"]["input_preparation"][:1]
            == (described["conversions"])
        )
    config = described["default_config"]
    envelope = core.prepare("", config, **source)
    started = jobs.start_run("", config, **source)
    request = json.loads(
        (jobs.job_directory(started["job"]) / "request.json").read_text("utf-8")
    )
    assert request["document_digest"] == described["document"]["digest"]
    assert request["document_conversions"] == described["conversions"]
    assert request["config"] == envelope["config"]
    loaded = worker.load_request(request)
    assert not isinstance(loaded, dict), loaded
    s, reread = loaded
    prepared = core.run_preparation(s, reread)
    assert s.digest == described["document"]["digest"]
    assert reread.to_payload() == envelope["config"]
    assert reread.digest() == envelope["config_digest"] == request["config_digest"]
    assert list(reread.input_preparation) == envelope["config"].get(
        "input_preparation", []
    )
    assert _untimed(json.loads(json.dumps(preparation_record(prepared)))) == _untimed(
        envelope["preparation"]
    )


def test_a_stored_document_is_reloaded_as_custom_and_digest_checked(
    no_worker: Path,
) -> None:
    """A forged ``request.json`` cannot have a tree read as packaged."""
    tree = y_tree()
    config = core.describe_instance(document=tree)["default_config"]
    started = jobs.start_run("", config, document=tree)
    path = jobs.job_directory(started["job"]) / "request.json"
    request = json.loads(path.read_text(encoding="utf-8"))
    forged = {**request, "document": bb84_tree()}
    refused = worker.load_request(forged)
    assert isinstance(refused, dict)
    assert (refused["stage"], refused["reason"]) == ("document", "reserved_identity")
    edited = copy.deepcopy(request)
    edited["document"]["identity"]["title"] = "changed after the start"
    refused = worker.load_request(edited)
    assert isinstance(refused, dict) and refused["reason"] == "document_unreadable"
    assert "digest" in refused["detail"]


def test_nothing_a_caller_reaches_reads_a_document_as_packaged() -> None:
    """The trusted and packaged readers stay out of runs/.

    Every caller of the facade and the MCP server is outside the repository's
    trust, so ``runs/`` names none of the readers that skip the identity
    reservation; the one place a packaged document is read is its own
    instance's package.
    """
    forbidden = re.compile(r"_read_trusted|read_packaged|load_packaged|packaged=True")
    offenders = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in sorted((ROOT / "runs").rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if forbidden.search(line)
    ]
    assert offenders == []


# ---------------------------------------------------------------------------
#  Templates and the format's references
# ---------------------------------------------------------------------------


#: The instances whose templates write no reserved string beyond ``identity``:
#: the customise hint alone makes a custom document of them.
_IDENTITY_ONLY = {"bb84", "bbm92"}


def _reserved_places(refused: dict[str, Any]) -> list[str]:
    """Return every place a reserved-identity refusal names: its path, then the rest."""
    _, _, rest = refused["detail"].partition("; also reserved: ")
    listed = rest.partition(". ")[0]
    return [refused["path"], *(place for place in listed.split(", ") if place)]


def _clear(tree: dict[str, Any], place: str) -> None:
    """Follow a template's header at one reserved place: write your own, or delete."""
    *parents, key = place.strip("/").split("/")
    node: Any = tree
    for part in parents:
        node = node[int(part)] if isinstance(node, list) else node[part]
    if key == "attested_by":
        node[key] = "my lab"
    else:
        del node[key]


def test_every_listed_template_is_a_packaged_document_that_customises() -> None:
    """Each template, customised as the hint and its header say, is a custom document.

    The facade's hint (a new identity, no readme or record_label) is all bb84
    and bbm92 need; optical_bb84 and decoy_bb84 also write ``instances.``
    labels in their stations and source, which one refusal names all at once
    and each template's header lists.
    """
    listed = [entry for entry in core.list_instances() if "template" in entry]
    assert {entry["id"] for entry in listed} == {
        "bb84",
        "optical_bb84",
        "decoy_bb84",
        "bbm92",
    }
    for entry in listed:
        assert (ROOT / entry["template"]).is_file()
        template = core.template(entry["id"])
        assert template["yaml"] == (ROOT / entry["template"]).read_text("utf-8")
        header = template["yaml"].partition("\nformat:")[0]
        assert "TO START A CUSTOM PROTOCOL FROM IT" in header
        tree = template["document"]
        assert tree["identity"]["id"] == entry["id"]
        refused = core.describe_instance(document=tree)
        assert refused["reason"] == "reserved_identity"
        assert "/identity/readme" in _reserved_places(refused)
        tree["identity"] = {
            "id": f"my_{entry['id']}",
            "title": "mine",
            "summary": "a copy of the template",
        }
        described = core.describe_instance(document=tree)
        if entry["id"] not in _IDENTITY_ONLY:
            assert described["reason"] == "reserved_identity", described
            places = _reserved_places(described)
            for place in places:
                # The header names each field the hint does not.
                assert place.rsplit("/", 1)[-1] in header.partition("TO START")[2]
                _clear(tree, place)
            described = core.describe_instance(document=tree)
        assert described["document"]["packaged"] is False, described
    with pytest.raises(KeyError):
        core.template("nope")
    with pytest.raises(KeyError):
        core.template("../bb84")


def test_the_document_references_are_served() -> None:
    schema = core.schema("protocol-document")
    assert schema["title"] or schema["$defs"]
    guide = core.document_guide()
    assert guide["markdown"].startswith("# Protocol documents")
    codes = core.document_refusal_codes()
    assert {"reserved_identity", "unsupported_topology"} <= set(codes)


def test_a_status_written_before_documents_still_reads(jobs_dir: Path) -> None:
    """An instance job's ``request.json`` has no document: its reply names none."""
    directory = jobs_dir / "bb84-000000000000-1"
    directory.mkdir(parents=True)
    core.write_json_atomic(
        directory / "request.json", {"instance": "bb84", "created": time.time()}
    )
    assert jobs.job_status(directory.name)["document"] is None


# ---------------------------------------------------------------------------
#  Reader isolation and request hygiene, one test or more each
# ---------------------------------------------------------------------------


def _signal_product(tree: dict[str, Any], n: int) -> None:
    product = tree["alphabets"]["signal"]["product"]
    for name in ("e1", "e2", "e3"):
        product["dims"][name] = [str(i) for i in range(n)]
    product["label"] = "({basis},{bit},{e1},{e2},{e3})"


def _wide_product(tree: dict[str, Any]) -> None:
    _signal_product(tree, 60)


def _wide_union(tree: dict[str, Any]) -> None:
    tree["alphabets"]["wide"] = {"enum": [f"w{i}" for i in range(3000)]}
    tree["alphabets"]["ann"]["union"] += ["wide", "wide"]


def _wide_table(tree: dict[str, Any]) -> None:
    tree["alphabets"]["ann"]["union"].append({"enum": [f"u{i}" for i in range(200)]})


def _huge_identity(tree: dict[str, Any]) -> None:
    tree["source"]["alice_marginal"] = {
        "scale": {"factor": "1/2", "of": {"identity": 100_000}}
    }


def _huge_space(tree: dict[str, Any]) -> None:
    tree["source"]["transmitted_dim"] = 10_000


@pytest.mark.parametrize(
    ("edit", "path", "at"),
    [
        (_wide_product, "/alphabets/signal", "describe"),
        (_wide_union, "/alphabets/ann/union", "describe"),
        (_wide_table, "/public/", "prepare"),
        (_huge_identity, "/source/alice_marginal", "describe"),
        (_huge_space, "/source/transmitted_dim", "describe"),
    ],
    ids=["product-alphabet", "union-alphabet", "rule-table", "identity", "dimension"],
)
def test_a_document_asking_for_too_much_work_is_refused_at_once(
    edit: Any, path: str, at: str
) -> None:
    """Bounded by the product of the sizes, before any is built."""
    tree = custom_tree()
    edit(tree)
    started = time.perf_counter()
    refused = core.describe_instance(document=tree)
    if at == "prepare":
        assert "refused" not in refused, refused
        refused = core.prepare("", refused["default_config"], document=tree)
    assert time.perf_counter() - started < 5.0
    assert (refused["stage"], refused["reason"]) == ("document", "document_too_large")
    assert refused["path"].startswith(path), refused


def test_the_bounds_sit_above_what_a_large_alphabet_needs() -> None:
    """A signal alphabet of 4,000 labels is still read, in well under a second."""
    tree = custom_tree("my_wide_bb84")
    _signal_product(tree, 10)
    started = time.perf_counter()
    described = core.describe_instance(document=tree)
    assert described["document"]["id"] == "my_wide_bb84"
    assert time.perf_counter() - started < 2.0


@pytest.mark.parametrize(
    "name",
    [
        "\\\\host\\share\\mine.json",
        "//host/share/mine.json",
        "\\\\?\\C:\\mine.json",
        "\\\\.\\C:\\mine.json",
    ],
)
def test_a_network_or_device_path_is_never_touched(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """m1: no stat and no open of a path that reaches the network."""

    def touched(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("the path was touched")

    monkeypatch.setattr(Path, "stat", touched)
    monkeypatch.setattr(Path, "read_text", touched)
    refused = core.describe_instance(document_file=name)
    assert refused["reason"] == "document_unreadable"
    assert "network" in refused["detail"]


def test_a_relative_document_file_is_refused() -> None:
    """m3: the server's working directory is the client's choice."""
    refused = core.describe_instance(document_file="mine.yaml")
    assert refused["reason"] == "document_unreadable"
    assert "absolute" in refused["detail"]


SECRET_FILES = [
    ("secrets.yaml", "password: hunter2\ntoken: [hunter2\n"),
    ("secrets.json", '{"password": "hunter2", "token": hunter2}'),
    ("settings.yaml", "password: hunter2\n"),
    ("settings.json", '{"password": "hunter2", "password": "hunter2"}'),
]


@pytest.mark.parametrize(("name", "content"), SECRET_FILES)
def test_a_refused_file_s_content_is_never_quoted(
    tmp_path: Path, name: str, content: str
) -> None:
    """m2: only the position of a parse failure, nothing of a non-document."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    refused = core.describe_instance(document_file=str(path))
    assert refused["reason"] == "document_unreadable"
    text = json.dumps(refused)
    assert "hunter2" not in text and "password" not in text and "token" not in text


def test_a_parse_failure_names_its_line(tmp_path: Path) -> None:
    path = tmp_path / "mine.yaml"
    path.write_text("format: certiqs-key/protocol-document\nx: [\n", "utf-8")
    refused = core.describe_instance(document_file=str(path))
    assert "line" in refused["detail"]


def test_a_long_refusal_is_clipped() -> None:
    """A refusal can quote the document; its detail and path are bounded."""
    tree = custom_tree()
    tree["stations"][0]["measurement"]["x" * 100_000] = 1
    refused = core.describe_instance(document=tree)
    assert refused["reason"] == "document_schema_violation"
    assert len(json.dumps(refused)) < 2 * core.MAX_DETAIL_CHARS + 1_000


def test_a_document_id_is_at_most_64_characters() -> None:
    """m4: an id becomes a directory name."""
    refused = core.describe_instance(document=custom_tree("a" * 65))
    assert (refused["reason"], refused["path"]) == (
        "document_schema_violation",
        "/identity/id",
    )
    assert "refused" not in core.describe_instance(document=custom_tree("a" * 64))


def test_the_worker_refuses_a_request_changed_after_the_start(
    no_worker: Path,
) -> None:
    """m5: the request's fields must still give its job's key."""
    tree = y_tree()
    config = core.describe_instance(document=tree)["default_config"]
    started = jobs.start_run("", config, document=tree)
    request = json.loads(
        (jobs.job_directory(started["job"]) / "request.json").read_text("utf-8")
    )
    assert not isinstance(worker.load_request(request), dict)
    changed = copy.deepcopy(request)
    changed["config"]["rounds"] = 1
    changed["config_digest"] = "0" * 64
    refused = worker.load_request(changed)
    assert isinstance(refused, dict) and refused["reason"] == "job_request_mismatch"
    malformed = {**request, "document_conversions": "not a list"}
    malformed.pop("job")
    refused = worker.load_request(malformed)
    assert isinstance(refused, dict) and refused["reason"] == "document_unreadable"


def test_one_digest_with_other_conversions_is_another_job(no_worker: Path) -> None:
    """Nit: a recorded float and an exact string of one value are two requests."""
    exact = custom_tree("my_half_bb84")
    exact["parameters"]["table"][1]["default"] = "1/2"
    floated = copy.deepcopy(exact)
    floated["parameters"]["table"][1]["default"] = 0.5
    first = core.describe_instance(document=exact)
    second = core.describe_instance(document=floated)
    assert first["document"]["digest"] == second["document"]["digest"]
    assert first["conversions"] == [] and second["conversions"]
    one = jobs.start_run("", first["default_config"], document=exact)
    two = jobs.start_run("", second["default_config"], document=floated)
    assert one["job"] != two["job"] and two["reused"] is False


def test_a_default_outside_its_domain_is_refused_when_described() -> None:
    """Nit: the engine's key check on the document's defaults, at once."""
    tree = custom_tree()
    tree["parameters"]["table"][0]["default"] = "3/4"
    refused = core.describe_instance(document=tree)
    assert (refused["stage"], refused["reason"]) == ("document", "outside_domain")
