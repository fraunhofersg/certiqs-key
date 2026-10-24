r"""Write the worked example's figures from a snapshot folder.

    python -m runs.bbm92_study.views --viewmodels DIR --out DIR \
        [--keyrate-data DIR] [--station N] [--preview]

Reads the snapshot folder ``--viewmodels`` (``snapshot.json`` and one
subfolder per device set, :func:`~runs.bbm92_study.views.snapshot.read_snapshot`)
and, with ``--keyrate-data``, each sweep's
``<DIR>/<sweep>/summary.csv`` that exists. Writes ``views-preamble.tex``, one
``.tex`` per figure and its proposed caption as ``<name>.caption.tex`` to
``--out``, and with ``--preview`` also ``views-preview.tex``, which it compiles
with ``latexmk -pdf`` in the output folder into ``views-preview.pdf``. After a
clean compile the auxiliaries (``.aux``, ``.log``, ``.fls``, ``.fdb_latexmk``)
are removed, so the folder holds sources and PDF only; after a failed one they
stay, for the log. The exit code is the compiler's. A figure skipped, or
drawn from a placeholder input, is named in a message on the way.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from runs.bbm92_study.views.build import build, files, preview
from runs.bbm92_study.views.keyrate import FIGURES as KEYRATE_FIGURES
from runs.bbm92_study.views.keyrate import Row, parse_summary
from runs.bbm92_study.views.snapshot import read_snapshot

PREVIEW = "views-preview"
"""The preview's file stem: ``views-preview.tex`` and ``views-preview.pdf``."""


def _latexmk(latexmk: str, folder: Path, *options: str) -> int:
    done = subprocess.run(
        [latexmk, *options, f"{PREVIEW}.tex"],
        cwd=folder,
        check=False,
        capture_output=True,
        text=True,
    )
    return done.returncode


def _sweeps(folder: Path) -> dict[str, list[Row]]:
    out: dict[str, list[Row]] = {}
    for spec in KEYRATE_FIGURES:
        path = folder / spec.sweep / "summary.csv"
        if path.is_file():
            out[spec.sweep] = parse_summary(path.read_text(encoding="utf-8"))
    return out


def main(argv: Sequence[str] | None = None) -> int:
    """Read the inputs, write the figures, optionally compile the preview."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--viewmodels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--keyrate-data", type=Path)
    parser.add_argument("--station", type=int, default=0)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)

    data = read_snapshot(args.viewmodels)
    sweeps = _sweeps(args.keyrate_data) if args.keyrate_data else None
    figures, messages = build(data, station=args.station, sweeps=sweeps)
    for message in messages:
        print(message)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in files(figures).items():
        (args.out / name).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out / name}")
    if not args.preview:
        return 0
    bib = Path(__file__).resolve().parents[3] / "refs" / "references.bib"
    relative = Path(os.path.relpath(bib, args.out.resolve())).as_posix()
    (args.out / f"{PREVIEW}.tex").write_text(
        preview(figures, bibliography=relative), encoding="utf-8", newline="\n"
    )
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        print(f"latexmk not found: {PREVIEW}.tex written, not compiled")
        return 1
    code = _latexmk(
        latexmk, args.out, "-pdf", "-interaction=nonstopmode", "-halt-on-error"
    )
    if code == 0:
        _latexmk(latexmk, args.out, "-c")
    print(f"latexmk exit {code}: {args.out / (PREVIEW + '.pdf')}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
