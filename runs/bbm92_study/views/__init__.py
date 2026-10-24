r"""The worked example's figures as vector LaTeX, from committed view models.

The whitepaper's BBM92 appendix shows the protocol, the receiver and the
statistics. This package draws those views as TikZ and PGFPlots from
view-model JSON, so a figure is a function of committed data and can be redrawn
at a new pin with one command:

    python -m runs.bbm92_study.views --preview \
        --viewmodels runs/bbm92_study/data/viewmodels --out build/bbm92-views

Each figure module is a pure function from parsed JSON to a LaTeX string;
:mod:`.build` assembles them with their headers and :mod:`.__main__` is the thin
command line that reads the snapshot and writes the files. :mod:`.snapshot`
fills a snapshot folder, one device set at a time, from the builders'
view models, the set's preparation and, when there is one, its run record.
What each figure reads is in this folder's ``README.md``.
"""

from runs.bbm92_study.views.build import FIGURE_SET, build, files, preview, render_all

__all__ = ["FIGURE_SET", "build", "files", "preview", "render_all"]
