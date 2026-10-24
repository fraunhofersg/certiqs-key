r"""The sifting rule and the key map as two booktabs tables, from ``protocol_map.json``.

The interactive view shows both as paginated tables beside the protocol map:
the sifting step's pass/fail per announcement class and
the key-rule step's raw key map, one row per raw outcome pair. On paper the
same two maps fit in two compact tables set side by side, the body of one
table float:

* **sifting**, the announcement classes ``K = C_A x C_B`` as a matrix, one row
  per value of the first message and one column per value of the second, each
  cell a bold ``pass`` or a muted cross for ``fail``, and a dot where no raw
  pair announces the class (the view model's "pass (no pairs)", which it
  counts as neither);
* **key per readout**, one row per value of the key holder's readout: its
  announcement, the classes of the other message under which it yields a key
  value, and that value, with ``\\perp`` where it never does.

Both tables are read from the operations' ``table`` fields by column name, the
step found by its ``type``; no outcome label is interpreted. What the marks
mean, and the counts, are in the caption :func:`_caption` writes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from runs.bbm92_study.views.tex import Rendered, escape, math

__all__ = ["render_keymap"]


def _operation(
    model: Mapping[str, Any], step_type: str, column: str
) -> Mapping[str, Any]:
    """Return the operation of the ``step_type`` step whose table has ``column``."""
    for step in model["steps"]:
        if step.get("type") != step_type:
            continue
        for op in step["operations"]:
            table = op.get("table")
            if table and column in table["columns"]:
                return dict(op)
    raise ValueError(f"no {step_type} operation with a {column!r} column")


def _rows(op: Mapping[str, Any]) -> list[dict[str, Any]]:
    columns = op["table"]["columns"]
    return [dict(zip(columns, row, strict=True)) for row in op["table"]["rows"]]


def _column_head(model: Mapping[str, Any], name: str) -> str:
    """Return a column's heading: a register's math if it names one."""
    for register in model.get("registers", []):
        if register.get("label") == name and register.get("math"):
            return f"${math(register['math'])}$"
    return escape(name)


def _ordered(values: Sequence[Any]) -> list[Any]:
    seen: list[Any] = []
    for v in values:
        if v not in seen:
            seen.append(v)
    return seen


def _sifting_table(model: Mapping[str, Any]) -> str:
    op = _operation(model, "sifting", "sifting")
    columns = op["table"]["columns"]
    first, second = columns[0], columns[1]
    rows = _rows(op)
    firsts = _ordered([r[first] for r in rows])
    seconds = _ordered([r[second] for r in rows])
    cell = {(r[first], r[second]): str(r["sifting"]) for r in rows}

    def show(value: str | None) -> str:
        if value == "pass":
            return r"\textbf{pass}"
        if value == "fail":
            return r"\textcolor{cqMuted}{$\times$}"
        return r"\textcolor{cqMuted}{$\cdot$}"

    head = (
        f"{_column_head(model, first)} $\\backslash$ {_column_head(model, second)} & "
        + " & ".join(escape(s) for s in seconds)
        + r" \\"
    )
    body = [
        escape(a) + " & " + " & ".join(show(cell.get((a, b))) for b in seconds) + r" \\"
        for a in firsts
    ]
    spec = "l" + "c" * len(seconds)
    span = rf"\multicolumn{{{len(seconds) + 1}}}{{l}}"
    return "\n".join(
        [
            rf"\begin{{tabular}}[t]{{{spec}}}",
            r"\toprule",
            rf"{span}{{\textbf{{sifting}} per announcement class}} \\",
            r"\midrule",
            head,
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def _key_table(model: Mapping[str, Any]) -> str:
    op = _operation(model, "key_rule", "key")
    columns = op["table"]["columns"]
    readout, mine, theirs = columns[1], columns[2], columns[3]
    rows = _rows(op)
    holder = next(
        (
            str(p["value"])
            for p in op.get("parameters", [])
            if p.get("name") == "holder"
        ),
        None,
    )
    body: list[str] = []
    for value in _ordered([r[readout] for r in rows]):
        mine_rows = [r for r in rows if r[readout] == value]
        announced = _ordered([r[mine] for r in mine_rows])
        keyed = [r for r in mine_rows if r["key"] != "perp"]
        passing = _ordered([r[theirs] for r in keyed])
        keys = _ordered([r["key"] for r in keyed])
        body.append(
            " & ".join(
                [
                    escape(value),
                    ", ".join(escape(a) for a in announced),
                    ", ".join(escape(c) for c in passing) if passing else "---",
                    ", ".join(escape(k) for k in keys) if keys else r"$\perp$",
                ]
            )
            + r" \\"
        )
    key_head = r"key $r$" + (f" ({escape(holder)})" if holder else "")
    return "\n".join(
        [
            r"\begin{tabular}[t]{llll}",
            r"\toprule",
            r"\multicolumn{4}{l}{\textbf{key} per readout} \\",
            r"\midrule",
            f"{_column_head(model, readout)} & {_column_head(model, mine)} & "
            f"keyed with {_column_head(model, theirs)} & {key_head} \\\\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def render_keymap(model: Mapping[str, Any]) -> Rendered:
    """Return the two tables side by side, the body of a table float, and a caption.

    The left table is the sifting matrix, the right the key per readout.
    """
    body = (
        "\n".join(
            [
                r"{\figmain\setlength{\tabcolsep}{2.8pt}%",
                _sifting_table(model) + "%",
                r"\hspace{1em}%",
                _key_table(model) + "%",
                "}",
            ]
        )
        + "\n"
    )
    return Rendered(body, _caption(model))


def _caption(model: Mapping[str, Any]) -> str:
    """Write the table's caption from the same data it reads."""
    sifting = [
        str(r["sifting"]) for r in _rows(_operation(model, "sifting", "sifting"))
    ]
    passing = sifting.count("pass")
    failing = sifting.count("fail")
    unrealised = len(sifting) - passing - failing
    op = _operation(model, "key_rule", "key")
    holder = next(
        (
            str(p["value"])
            for p in op.get("parameters", [])
            if p.get("name") == "holder"
        ),
        "the key holder",
    )
    columns = op["table"]["columns"]
    first, second = _column_head(model, columns[2]), _column_head(model, columns[3])
    return " ".join(
        [
            "Sifting and the key map of the worked example.",
            f"Left: for each pair of announcements, {first} from the first message "
            f"and {second} from the second, whether the round passes sifting "
            r"(\textbf{pass}) or is discarded ($\times$); a dot marks a pair no "
            f"outcome of the honest protocol announces. Of the {len(sifting)} pairs, "
            f"{passing} pass, {failing} are discarded and {unrealised} never occur.",
            f"Right: for each of {escape(holder)}'s readouts, the announcement it "
            "leads to, the "
            f"announcements of the other party that make the round a key round, "
            r"and the key bit; $\perp$ marks a readout that never yields a key bit.",
        ]
    )
