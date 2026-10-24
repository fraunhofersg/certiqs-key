# The headline run's key-rate report

The BBM92 study's headline point, `../qber/realistic-L10-Q0p01/` (10 dB of
loss, 10^6 coincidences, realistic devices), rendered with the key-rate
report:

- `report.html`, `report.md`: the report;
- `record.html`, `record.md`: the record excerpts it links.

The record names the engine commit it was computed at (`../PROVENANCE.md`);
the report is rendered by the report code of the commit that holds these
files. Its links into the contracts and the repository are relative, so they
resolve in a checkout and on the Pages site, which serves the HTML at the same
path. Re-render from the top of the repository with

    python -m certiqs_key.runs.report runs/bbm92_study/data/qber/realistic-L10-Q0p01/record.json.gz \
        --format html --contract-base ../../../../ --repo-base ../../../../ --pages-site \
        --out runs/bbm92_study/data/headline-report/report.html
    python -m certiqs_key.runs.report runs/bbm92_study/data/qber/realistic-L10-Q0p01/record.json.gz \
        --format md --contract-base ../../../../ --repo-base ../../../../ \
        --out runs/bbm92_study/data/headline-report/report.md
