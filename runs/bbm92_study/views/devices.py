r"""The device parameters of the study, perfect and realistic, as a table.

It sits beside the optics figure so that every later figure can name its
device set and a reader finds each value, and for the realistic set its
source, in one place.

The values are :data:`runs.bbm92_study.sweeps.REALISTIC`, the sweeps' own, so
the table cannot drift from the runs; each row names the registered source of
its realistic value. The channel is a row of its own: the same for both sets.

ONE SYMBOL PER QUANTITY, NAMED HERE
===================================
:data:`SYMBOLS` and :func:`efficiency_symbol` are the table's symbol column,
and the compact optics figure (``optics_compact.py``) labels its elements with
the same ones, so that figure and table read as one; a test checks that every
symbol the figure prints is in the table.
"""

from __future__ import annotations

import math as _math

from runs.bbm92_study.sweeps import REALISTIC
from runs.bbm92_study.views.tex import Rendered, numeral

__all__ = ["SYMBOLS", "efficiency_symbol", "render_devices"]

SYMBOLS = {
    "visibility": "V",
    "dark_count": r"p_{\mathrm{dc}}",
    "basis_split": "T",
    "pbs_leak_transmitted": r"\epsilon_{\mathrm{t}}",
    "pbs_leak_reflected": r"\epsilon_{\mathrm{r}}",
    "rotation": r"\theta",
    "channel": r"\eta_{\mathrm{ch}}",
}
"""Math (no ``$``) for each quantity of the table, by the sweeps' parameter name.

``rotation`` is Bob's analyser rotation: his half-wave plate is turned by
half of it, since a plate turned by ``t`` rotates the polarization by ``2t``.
"""


def efficiency_symbol(port: str) -> str:
    r"""Return the efficiency symbol of the detector at ``port``: ``\eta_H``, ..."""
    return rf"\eta_{port}"


def _cite(key: str, where: str = "") -> str:
    return rf"\parencite[{where}]{{{key}}}" if where else rf"\parencite{{{key}}}"


def render_devices() -> Rendered:
    """Return the table body (booktabs) and its caption."""
    eff = float(REALISTIC["efficiency"])
    low = eff * float(REALISTIC["mismatch_ratio"])
    dark = float(REALISTIC["dark_count"])
    split = float(REALISTIC["basis_split"])
    leak_t = float(REALISTIC["pbs_leak_transmitted"])
    leak_r = float(REALISTIC["pbs_leak_reflected"])
    rotation = _math.sin(float(REALISTIC["misalignment_rad"])) ** 2
    visibility = float(REALISTIC["visibility"])
    s = {name: f"${symbol}$" for name, symbol in SYMBOLS.items()}
    eta = {port: efficiency_symbol(port) for port in "HVDA"}
    rows = [
        (
            "source visibility",
            s["visibility"],
            "$1$",
            f"${numeral(visibility, 3)}$",
            _cite("wengerowsky2019submarine", "p.~3"),
        ),
        (
            r"efficiency, $H$, $D$ detectors",
            f"${eta['H']} = {eta['D']}$",
            "$1$",
            f"${numeral(eff, 3)}$",
            _cite("neumann2022transnational", "p.~14"),
        ),
        (
            r"efficiency, $V$, $A$ detectors",
            f"${eta['V']} = {eta['A']}$",
            "$1$",
            f"${numeral(low, 3)}$",
            _cite("wengerowsky2019submarine", "p.~3"),
        ),
        (
            "dark clicks, per detector and round",
            s["dark_count"],
            "$0$",
            rf"${numeral(dark, 3)}$",
            _cite("joshi2020network", "pp.~2, 8"),
        ),
        (
            "basis splitter, transmittance",
            s["basis_split"],
            r"$\tfrac12$",
            f"${numeral(split, 3)}$",
            _cite("joshi2020network", "p.~8"),
        ),
        (
            "polarizing splitter, transmitted leak",
            s["pbs_leak_transmitted"],
            "$0$",
            f"${numeral(leak_t, 3)}$",
            _cite("joshi2020network", "p.~8"),
        ),
        (
            "polarizing splitter, reflected leak",
            s["pbs_leak_reflected"],
            "$0$",
            f"${numeral(leak_r, 3)}$",
            _cite("joshi2020network", "p.~8"),
        ),
        (
            r"Bob's analyser rotation",
            rf"$\sin^2{SYMBOLS['rotation']}$",
            "$0$",
            f"${numeral(rotation, 3)}$",
            _cite("neumann2022transnational", "p.~5"),
        ),
        (
            "channel, each arm",
            rf"${SYMBOLS['channel']} = 10^{{-L/20}}$",
            r"\multicolumn{2}{c}{the same}",
            None,
            "",
        ),
    ]
    lines = [
        r"{\figmain\setlength{\tabcolsep}{4pt}%",
        r"\begin{tabular}{@{}llrrl@{}}",
        r"\toprule",
        r"quantity & symbol & perfect & realistic & source \\",
        r"\midrule",
    ]
    for quantity, symbol, perfect, realistic, source in rows:
        cells = [quantity, symbol, perfect] + ([realistic] if realistic else [])
        lines.append(" & ".join([*cells, source]) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}%", "}", ""]
    caption = (
        "The two device sets of the key-rate figures, at the same channel: "
        "perfect devices, and realistic ones with every value from a registered "
        "experiment. The realistic values are a composite of reported ones, not "
        "one experiment's: the $V$ and $A$ detectors keep the reported ratio of "
        r"two measured efficiencies, $54\,\%$ to $59\,\%$, applied to $0.8$. A "
        "round is one emitted pair, so $n$ counts emitted pairs; the "
        r"dark-click probability is the dark-count rate, about $1$\,kHz, times "
        r"the coincidence window, about $130$\,ps: the chance that a dark click "
        "falls in the window around the partner's photon. A CW experiment maps "
        "onto these rounds through a time grid of that window in the weak-source "
        "limit. The source is untrusted, so $V$ enters only the honest "
        "statistics; it stands in for all source noise, multi-pair accidentals "
        "included (the source model emits one pair per round), and is held fixed "
        "across loss. Measured visibilities include the analysers of their "
        "experiment, so adding the receiver imperfections on top counts some "
        "noise twice, which is conservative. The reported visibility is "
        r"$98\,\%$ in the diagonal basis and $97\,\%$ in the rectilinear one; "
        "the model has one. Not modelled: multi-pair emission, detector dead "
        "time, afterpulsing and timing jitter. The QBER figure varies $V$ for "
        "both sets; the ladder adds the realistic values one at a time."
    )
    return Rendered("\n".join(lines), caption)
