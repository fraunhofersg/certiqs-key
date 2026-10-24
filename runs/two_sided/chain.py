r"""Run a list of loss points in order for one instance and route, warm-chained.

Each point after the first starts from the previous point's final iterate
(``--warm-start``), so a loss sweep walks along the axis instead of starting
every point cold. One process, one point after another: running instances or
routes in parallel is the production driver's job, not this helper's.

Every point is an ordinary :mod:`runs.two_sided.point` run with its own output
directory ``<output-root>/<loss>db`` and its own record; the chain adds only
the ``--warm-start`` of each point after the first, which the record then
carries as the seed's path and sha256. The first point starts cold unless
``--warm-start`` is given here too. A point that refuses or fails stops the
chain: its successor would have no seed.

Example::

    python -m runs.two_sided.chain --instance bbm92 --route encoded \\
      --loss-db 9 10 11 --rounds 100000000 --lambda-ec 0 \\
      --lambda-ec-purpose "diagnostic" --zero-ec-label "unreconciled diagnostic" \\
      --dark-count 1/1000000 --iterations 300 --oracle spectral \\
      --method pairwise --output-root build/chain-bbm92
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from certiqs_key.runs.iterate_file import ITERATE_FILE_NAME, WarmStartFileError
from certiqs_key.runs.record import RunRecord

from . import point


def parser() -> argparse.ArgumentParser:
    """Return the chain parser: the point parser with a list of losses."""
    result = argparse.ArgumentParser(description=__doc__)
    point.add_point_options(result)
    result.add_argument("--loss-db", type=float, nargs="+", required=True)
    result.add_argument("--output-root", type=Path, required=True)
    return result


def point_arguments(
    arguments: argparse.Namespace, loss_db: float, previous: Path | None
) -> argparse.Namespace:
    """Return one point's arguments: this loss, its directory, the seed."""
    values = vars(arguments).copy()
    values.pop("output_root")
    values["loss_db"] = loss_db
    values["output"] = arguments.output_root / f"{loss_db:g}db"
    if previous is not None:
        values["warm_start"] = previous
    return argparse.Namespace(**values)


def run_chain(
    arguments: argparse.Namespace,
    *,
    oracle: object,
    run_point: Callable[..., RunRecord] = point.run_point,
) -> list[RunRecord]:
    """Run the points in the order given, each seeded by its predecessor."""
    records: list[RunRecord] = []
    previous: Path | None = None
    for loss_db in arguments.loss_db:
        single = point_arguments(arguments, loss_db, previous)
        record = run_point(single, oracle=oracle)
        records.append(record)
        if "final_iterate" not in record.payload:
            break
        previous = _relative(single.output / ITERATE_FILE_NAME)
    return records


def _relative(path: Path) -> Path:
    """Return the path relative to the working directory when it lies inside it.

    The seed's path is a locator the configuration keeps beside its hash
    (and out of its digest); a relative one reads the same on every machine
    that runs the chain from the repository root. A path outside the working
    directory is kept as given rather than written with ``..``.
    """
    try:
        return path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        return path


def main(argv: Sequence[str] | None = None) -> int:
    """Run the chain with the public QICS oracle."""
    arguments = parser().parse_args(argv)
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    try:
        run_chain(arguments, oracle=QicsSectorChoiOracle())
    except WarmStartFileError as refused:
        print(f"refused: {refused.reason}: {refused}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
