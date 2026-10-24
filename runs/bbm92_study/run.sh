#!/usr/bin/env bash
# The BBM92 study's full run, every sweep in one pool, from the top of a clean
# checkout. The records name the checkout's commit with git_dirty false only
# if no tracked file changes while the run lasts, so the run writes to the
# git-ignored build/bbm92-study/ alone and the committed data under
# runs/bbm92_study/data/ is replaced only after the last point.
# Resumable: a point with a record.json.gz in build/ is skipped.
#
#   bash runs/bbm92_study/run.sh            # PY=<interpreter> WORKERS=<n> to override
#
# On Windows (Git Bash) PYTHONPATH takes Windows paths separated by ';',
# otherwise an editable install of another checkout wins (harness/PITFALLS.md).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if command -v cygpath > /dev/null; then
  export PYTHONPATH="$(cygpath -w "$PWD/src");$(cygpath -w "$PWD")"
else
  export PYTHONPATH="$PWD/src:$PWD"
fi
PY="${PY:-python}"
WORKERS="${WORKERS:-4}"
SWEEPS=(loss ladder alpha qber rounds solvers routes)
BUILD=build/bbm92-study
DATA=runs/bbm92_study/data

"$PY" -c "import certiqs_key; print(certiqs_key.__file__)"
test -z "$(git status --porcelain --untracked-files=no)" || {
  echo "tracked files are modified; run from a clean checkout" >&2; exit 1; }
mkdir -p "$BUILD"
"$PY" -m runs.bbm92_study.run "${SWEEPS[@]}" --workers "$WORKERS" --out "$BUILD" \
  > "$BUILD/run-log.txt" 2>&1

# The committed data: per point the record and its inputs, per sweep the summary.
for sweep in "${SWEEPS[@]}"; do
  rm -rf "${DATA:?}/$sweep"
  for point in "$BUILD/$sweep"/*/; do
    dest="$DATA/$sweep/$(basename "$point")"
    mkdir -p "$dest"
    for f in record.json.gz point.json lambda-ec.json alpha-from.json; do
      if [ -f "$point$f" ]; then cp "$point$f" "$dest/"; fi
    done
  done
done
cp "$BUILD/run-log.txt" "$DATA/run-log.txt"
"$PY" -m runs.bbm92_study.summarize "${SWEEPS[@]}" --out "$BUILD" --to "$DATA"
