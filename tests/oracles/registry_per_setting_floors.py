"""The hand-derived registry, part one: per-setting multi-click floors.

WHAT THIS FILE IS. Every number below was derived BY HAND from the claim files of
the per-setting floors effort: reductions/wpfss ``def:weight-route``,
``prop:route`` and ``rem:minweight``, with receiver ``def:slot``. Nothing
was read off the implementation: an oracle registry "moves with its module and
is NEVER REGENERATED FROM THE CODE IT TESTS" (PRINCIPLES.md section 2.3). The
derivations are written beside the values so a reader can redo each with a
pencil, and the derivation, not the table, stays authoritative.

WHY A NEW FILE. The existing registries are frozen cuts with partition tests over
the original names; these values are new evidence for new claim text,
so they get a file of their own. The entry record and the two exact
helpers live here because the sibling registries import them, and that
dependency runs the way the modules do: a submodule reads wpfss and the
receiver, never the reverse.

THE REPRESENTATION. Every scalar is a ``fractions.Fraction``; every matrix is a
tuple of tuples of Fractions and every one of them is REAL. No float appears.

THE TWO GROUPS.

* PSF-A -- ``def:weight-route`` Eq. ``eq:weightroute`` and ``eq:latdown`` on
  toy two-setting slots with declared per-setting floors, with and without a
  dark-count improvement ``r_min``, at stated lattice exponents ``kappa``.
* PSF-B -- ``rem:minweight``: the uniform special case (every per-setting weight
  equal) gives the numbers of the t-uniform route term for term, the one-setting
  (probe-free) slot is that case, and consuming the uniform weight would be
  weakly smaller by the stated gain.

THE FILE IS PARTITIONED, AND THE RECEIVER GROUP IS A FILE OF ITS OWN.
``registry_per_setting_floors_probe.py`` carries group PSF-C, the receiver
with a probe source, which the removable probe-conditioning submodule states,
together with the oracle entries of every group (one frozen tuple). The cut is
textual: no value moved, changed or was recomputed, and that file's header
keeps the paragraphs of this one that described the group. The dependency
runs ONE WAY: that file imports the entry record and the cases from here, and
nothing here names anything there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction as F

__all__ = [
    "PER_SETTING_ROUTE_CASES",
    "HandOracleEntry",
    "PerSettingRouteCase",
    "RealMatrix",
    "lattice_floor",
    "unrounded_routed_weight",
]

#: A real matrix of exact rationals, as a tuple of rows.
RealMatrix = tuple[tuple[F, ...], ...]


@dataclass(frozen=True)
class HandOracleEntry:
    """One frozen expected value or relation, with its derivation and observable.

    The field set follows ``registry.OracleEntry`` and the decoy registry's entry:
    ``kind`` is one of ``registry.KINDS``; ``claims`` are claim ids of
    ``spec/modules/**`` that resolve to claim files; ``observable`` names the
    QUANTITY the implementer's comparison reads -- the function that computes it
    is the implementer's choice and is never named here.
    """

    oracle_id: str
    claims: tuple[str, ...]
    kind: str
    subject: str
    derivation: str
    #: The hypotheses under which the value holds, stated so that it cannot be
    #: satisfied by reinterpretation.
    hypotheses: tuple[str, ...]
    #: What the implementer compares, and how (exactly, or within a tolerance).
    observable: str
    #: The single headline value where there is one; the tables carry the rest.
    value: F | int | str | None = None


def lattice_floor(x: F, kappa: int) -> F:
    """Return ``lat(x) = 2^-kappa floor(2^kappa x)`` of Eq. ``eq:latdown``.

    The largest integer multiple of ``2^-kappa`` that is at most ``x``: the
    DOWNWARD rounding onto the declared lattice, exact on a rational.
    """
    scale = 2**kappa
    return F(math.floor(x * scale), scale)


def unrounded_routed_weight(q_t: F, p_t: F, r_min: F) -> F:
    """Return ``hat p = q_t((1 - r_min) p^(t) + r_min)`` of Eq. ``eq:weightroute``."""
    return q_t * ((1 - r_min) * p_t + r_min)


# ===========================================================================
#  Group PSF-A and PSF-B -- the weight route with per-setting floors
# ===========================================================================
#
#  Every case has the K = 2 canonical alphabet Y = (nc, c1, c2, mc) of
#  receiver ``def:clickalphabet`` with the canonical coarse-graining of wpfss
#  ``lem:descent`` Eq. ``eq:canonicalcg`` (injective off MC, MC = {{1,2}} one
#  pattern), so R descends trivially and R^cg is R. The bounded letter is mc
#  with O_1 = MC_K = cg^{-1}(mc), exactly a fibre, and r = 1. The per-setting
#  floors p^(t) are DECLARED numbers of the slot (receiver ``def:slot``); they
#  are not computed from any optics.

_Y_K2 = ("nc", "c1", "c2", "mc")

#: No dark counts: R^cg is the identity, every letter is absorbing, and
#: r_min(mc) = min(R_{mc|nc}, R_{mc|c1}, R_{mc|c2}) = 0.
_R_IDENTITY_K2: tuple[tuple[str, tuple[tuple[str, F], ...]], ...] = (
    ("nc", (("nc", F(1)), ("c1", F(0)), ("c2", F(0)), ("mc", F(0)))),
    ("c1", (("nc", F(0)), ("c1", F(1)), ("c2", F(0)), ("mc", F(0)))),
    ("c2", (("nc", F(0)), ("c1", F(0)), ("c2", F(1)), ("mc", F(0)))),
    ("mc", (("nc", F(0)), ("c1", F(0)), ("c2", F(0)), ("mc", F(1)))),
)

#: Independent per-port dark counts p_dc|1 = 1/2, p_dc|2 = 1/4 (monotone R):
#: R_{S|S'} = prod_{k in S minus S'} p_dc|k * prod_{k not in S} (1 - p_dc|k)
#: for S' subset S, else 0. Column by column (rows nc, c1, c2, mc):
#:   nc : ((1/2)(3/4), (1/2)(3/4), (1/2)(1/4), (1/2)(1/4)) = (3/8, 3/8, 1/8, 1/8)
#:   c1 : (0, 1 - 1/4, 0, 1/4) = (0, 3/4, 0, 1/4)
#:   c2 : (0, 0, 1 - 1/2, 1/2) = (0, 0, 1/2, 1/2)
#:   mc : (0, 0, 0, 1)              -- absorbing
#: r_min(mc) = min(1/8, 1/4, 1/2) = 1/8, from the nc column (both ports dark).
_R_DARK_K2: tuple[tuple[str, tuple[tuple[str, F], ...]], ...] = (
    ("nc", (("nc", F(3, 8)), ("c1", F(3, 8)), ("c2", F(1, 8)), ("mc", F(1, 8)))),
    ("c1", (("nc", F(0)), ("c1", F(3, 4)), ("c2", F(0)), ("mc", F(1, 4)))),
    ("c2", (("nc", F(0)), ("c1", F(0)), ("c2", F(1, 2)), ("mc", F(1, 2)))),
    ("mc", (("nc", F(0)), ("c1", F(0)), ("c2", F(0)), ("mc", F(1)))),
)

_JointWeights = tuple[tuple[tuple[str, str], F], ...]


@dataclass(frozen=True)
class PerSettingRouteCase:
    """One slot routed through Eq. ``eq:weightroute`` and Eq. ``eq:latdown``."""

    case_id: str
    claims: tuple[str, ...]
    letters: tuple[str, ...]
    #: (setting, q_t) in the declared order of T.
    settings: tuple[tuple[str, F], ...]
    #: R^cg column by column: (column letter, ((row letter, value), ...)).
    descended_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    bounded_letter: str
    r_min: F
    #: The slot entry's per-setting weights (setting, p^(t)).
    slot_weights: tuple[tuple[str, F], ...]
    #: p_i = min_t p^(t), the uniform weight of receiver def:slot.
    uniform_weight: F
    #: ((bounded letter, t), hat p) before the floor; zero at every other (y,t).
    unrounded_weights: _JointWeights
    unrounded_total: F
    #: (kappa, ((bounded letter, t), lat(hat p)), p = sum of the floored weights).
    floored: tuple[tuple[int, _JointWeights, F], ...]
    #: The weights a route consuming the uniform weight p_i would form, unrounded.
    uniform_route_weights: _JointWeights
    #: sum_t q_t (1 - r_min)(p^(t) - p_i), the gain of rem:minweight, unrounded.
    per_setting_gain: F
    derivation: str


_ROUTE_CLAIMS = (
    "reductions/wpfss/def:weight-route",
    "reductions/wpfss/prop:route",
    "reductions/wpfss/rem:minweight",
    "receiver/def:slot",
    "receiver/prop:slotvalid",
)

PSF_TWO_SETTING_NO_DARK = PerSettingRouteCase(
    case_id="PSF-2S-R0",
    claims=_ROUTE_CLAIMS,
    letters=_Y_K2,
    settings=(("off", F(3, 4)), ("on", F(1, 4))),
    descended_matrix=_R_IDENTITY_K2,
    bounded_letter="mc",
    r_min=F(0),
    slot_weights=(("off", F(1, 2)), ("on", F(3, 4))),
    uniform_weight=F(1, 2),
    unrounded_weights=((("mc", "off"), F(3, 8)), (("mc", "on"), F(3, 16))),
    unrounded_total=F(9, 16),
    floored=(
        (3, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))), F(1, 2)),
        (4, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(3, 16))), F(9, 16)),
        (53, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(3, 16))), F(9, 16)),
    ),
    uniform_route_weights=((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))),
    per_setting_gain=F(1, 16),
    derivation="""\
TWO SETTINGS, NO DARK COUNTS. q_off = 3/4, q_on = 1/4 (dyadic, sum 1 exactly,
def:joint-family). The slot entry (MC_K, (p^(off), p^(on))) = (MC_K, (1/2, 3/4))
of the amended receiver def:slot: one DECLARED weight per setting, the LED-on
floor the larger, as in the effort. R^cg = identity, so r_min(mc) = 0.

EQ. eq:weightroute, hat p_(y_i,t) = q_t((1 - r_min) p^(t)_i + r_min), read at the
weight OF THE JOINT OUTCOME'S OWN SETTING (the B1b change):
    hat p_(mc,off) = (3/4)(1/2) = 3/8 ,   hat p_(mc,on) = (1/4)(3/4) = 3/16 ,
and p_(y,t) = 0 at every other (y,t); total 6/16 + 3/16 = 9/16 < 1.

EQ. eq:latdown, lat(x) = 2^-kappa floor(2^kappa x):
  kappa = 3 (every declared number is a multiple of 1/8: 3/4, 1/4, 1/2, 3/4, 0, 1):
    lat(3/8) = 3/8 (on the lattice), lat(3/16) = floor(8 * 3/16)/8 = floor(3/2)/8
    = 1/8; p = 3/8 + 1/8 = 1/2, 1 - p = 1/2.  THE FLOOR BITES AT THE ON LETTER.
  kappa = 4: both weights are multiples of 1/16 and are unchanged; p = 9/16.
  kappa = 53 (the binary64 ceiling of eq:latinv): unchanged; p = 9/16.
Each floored weight is at most its unrounded one, which is prop:route's reason
the emitted weight is certified.

THE UNIFORM ROUTE (rem:minweight). p_i = min(1/2, 3/4) = 1/2 at both settings:
(3/4)(1/2) = 3/8 and (1/4)(1/2) = 1/8, total 1/2. The per-setting route gains
sum_t q_t (1 - r_min)(p^(t) - p_i) = (3/4)(1)(0) + (1/4)(1)(3/4 - 1/2) = 1/16,
which is exactly 3/16 - 1/8 at the on letter: nothing at the setting whose weight
is the minimum.""",
)

PSF_TWO_SETTING_DARK = PerSettingRouteCase(
    case_id="PSF-2S-R18",
    claims=_ROUTE_CLAIMS,
    letters=_Y_K2,
    settings=(("off", F(3, 4)), ("on", F(1, 4))),
    descended_matrix=_R_DARK_K2,
    bounded_letter="mc",
    r_min=F(1, 8),
    slot_weights=(("off", F(1, 2)), ("on", F(3, 4))),
    uniform_weight=F(1, 2),
    unrounded_weights=((("mc", "off"), F(27, 64)), (("mc", "on"), F(25, 128))),
    unrounded_total=F(79, 128),
    floored=(
        (3, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))), F(1, 2)),
        (4, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(3, 16))), F(9, 16)),
        (6, ((("mc", "off"), F(27, 64)), (("mc", "on"), F(3, 16))), F(39, 64)),
        (7, ((("mc", "off"), F(27, 64)), (("mc", "on"), F(25, 128))), F(79, 128)),
    ),
    uniform_route_weights=((("mc", "off"), F(27, 64)), (("mc", "on"), F(9, 64))),
    per_setting_gain=F(7, 128),
    derivation="""\
TWO SETTINGS WITH A DARK-COUNT IMPROVEMENT. Same q_t and slot as PSF-2S-R0. The
dark-count channel is the independent per-port product form with p_dc|1 = 1/2,
p_dc|2 = 1/4; its columns are written above the case. R^cg_{mc|mc} = 1: the
bounded letter is ABSORBING (prop:route Eq. eq:absorbing), and
    r_min(mc) = min over y' != mc of R^cg_{mc|y'} = min(1/8, 1/4, 1/2) = 1/8 .
r = 1, so wpfss cor:oneabsorbing permits a non-zero r_min.

EQ. eq:weightroute:
  (mc,off): (3/4)((7/8)(1/2) + 1/8) = (3/4)(7/16 + 2/16) = (3/4)(9/16) = 27/64 ;
  (mc,on) : (1/4)((7/8)(3/4) + 1/8) = (1/4)(21/32 + 4/32) = (1/4)(25/32) = 25/128 ;
total 54/128 + 25/128 = 79/128 < 1.

EQ. eq:latdown (every declared number -- q_t, p^(t), r_min and every entry of
R^cg -- is a multiple of 1/8, so kappa = 3 is an admissible declaration):
  kappa = 3: lat(27/64) = floor(27/8)/8 = 3/8 ; lat(25/128) = floor(25/16)/8 = 1/8 ;
             p = 1/2.
  kappa = 4: floor(27/4)/16 = 6/16 = 3/8 ; floor(25/8)/16 = 3/16 ; p = 9/16.
  kappa = 6: 27/64 is on the lattice ; floor(25/2)/64 = 12/64 = 3/16 ;
             p = 27/64 + 12/64 = 39/64.
  kappa = 7: both on the lattice, unchanged ; p = 79/128.

THE UNIFORM ROUTE. p_i = 1/2: (3/4)(9/16) = 27/64 and (1/4)(9/16) = 9/64 = 18/128.
Gain sum_t q_t (1 - r_min)(p^(t) - p_i) = (1/4)(7/8)(1/4) = 7/128, which is
25/128 - 18/128 at the on letter.""",
)

PSF_UNIFORM_NO_DARK = PerSettingRouteCase(
    case_id="PSF-UNI-R0",
    claims=_ROUTE_CLAIMS,
    letters=_Y_K2,
    settings=(("off", F(3, 4)), ("on", F(1, 4))),
    descended_matrix=_R_IDENTITY_K2,
    bounded_letter="mc",
    r_min=F(0),
    slot_weights=(("off", F(1, 2)), ("on", F(1, 2))),
    uniform_weight=F(1, 2),
    unrounded_weights=((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))),
    unrounded_total=F(1, 2),
    floored=(
        (3, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))), F(1, 2)),
        (53, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))), F(1, 2)),
    ),
    uniform_route_weights=((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))),
    per_setting_gain=F(0),
    derivation="""\
THE UNIFORM SPECIAL CASE, rem:minweight's last paragraph. p^(off) = p^(on) = 1/2,
so the uniform weight is 1/2 = p^(t) at every t, and eq:weightroute is evaluated
on THE SAME DECLARED NUMBERS q_t, r_min = 0 and p_i = 1/2 as the t-uniform route
of before B1b evaluated:
    (mc,off): (3/4)(1/2) = 3/8 ,   (mc,on): (1/4)(1/2) = 1/8 ,   p = 1/2 .
Both are multiples of 1/8, so the floor changes nothing at kappa = 3 or 53. The
per-setting and uniform-route weights are identical entry for entry and the gain
is 0: "the routed weights, their total p, the complement 1 - p and everything the
flat instance builds from them are then the numbers that route gave".""",
)

PSF_UNIFORM_DARK = PerSettingRouteCase(
    case_id="PSF-UNI-R18",
    claims=_ROUTE_CLAIMS,
    letters=_Y_K2,
    settings=(("off", F(3, 4)), ("on", F(1, 4))),
    descended_matrix=_R_DARK_K2,
    bounded_letter="mc",
    r_min=F(1, 8),
    slot_weights=(("off", F(1, 2)), ("on", F(1, 2))),
    uniform_weight=F(1, 2),
    unrounded_weights=((("mc", "off"), F(27, 64)), (("mc", "on"), F(9, 64))),
    unrounded_total=F(9, 16),
    floored=(
        (3, ((("mc", "off"), F(3, 8)), (("mc", "on"), F(1, 8))), F(1, 2)),
        (6, ((("mc", "off"), F(27, 64)), (("mc", "on"), F(9, 64))), F(9, 16)),
    ),
    uniform_route_weights=((("mc", "off"), F(27, 64)), (("mc", "on"), F(9, 64))),
    per_setting_gain=F(0),
    derivation="""\
THE UNIFORM SPECIAL CASE WITH r_min = 1/8 (the dark-count channel of PSF-2S-R18).
(1 - 1/8)(1/2) + 1/8 = 7/16 + 2/16 = 9/16, so
    (mc,off): (3/4)(9/16) = 27/64 ,   (mc,on): (1/4)(9/16) = 9/64 ,
total 36/64 = 9/16. kappa = 3: floor(27/8)/8 = 3/8 and floor(9/8)/8 = 1/8, p = 1/2;
kappa = 6: both on the lattice, p = 9/16. Identical to the t-uniform route's
numbers entry for entry; gain 0.""",
)

PSF_ONE_SETTING_NO_DARK = PerSettingRouteCase(
    case_id="PSF-1S-R0",
    claims=(*_ROUTE_CLAIMS, "reductions/def:joint-family"),
    letters=_Y_K2,
    settings=(("off", F(1)),),
    descended_matrix=_R_IDENTITY_K2,
    bounded_letter="mc",
    r_min=F(0),
    slot_weights=(("off", F(1, 2)),),
    uniform_weight=F(1, 2),
    unrounded_weights=((("mc", "off"), F(1, 2)),),
    unrounded_total=F(1, 2),
    floored=(
        (1, ((("mc", "off"), F(1, 2)),), F(1, 2)),
        (53, ((("mc", "off"), F(1, 2)),), F(1, 2)),
    ),
    uniform_route_weights=((("mc", "off"), F(1, 2)),),
    per_setting_gain=F(0),
    derivation="""\
THE ONE-SETTING (PROBE-FREE) SLOT. T = {off}, q_off = 1 (def:joint-family: a
singleton T with q = 1, V identified with Y). Receiver def:slot: "At a
one-setting family, T = {off}, an entry has the single weight p^(off)_i = p_i and
is written (O_i, p_i)" -- here (MC_K, 1/2). eq:weightroute: 1 * (1 * 1/2 + 0) =
1/2; p = 1/2. kappa = 1 is admissible (1/2 and 1 are multiples of 1/2) and the
floor changes nothing. This is the case every probe-free instance is in, and it
is bit-identical to the t-uniform route (rem:minweight).""",
)

PSF_ONE_SETTING_DARK = PerSettingRouteCase(
    case_id="PSF-1S-R18",
    claims=(*_ROUTE_CLAIMS, "reductions/def:joint-family"),
    letters=_Y_K2,
    settings=(("off", F(1)),),
    descended_matrix=_R_DARK_K2,
    bounded_letter="mc",
    r_min=F(1, 8),
    slot_weights=(("off", F(1, 2)),),
    uniform_weight=F(1, 2),
    unrounded_weights=((("mc", "off"), F(9, 16)),),
    unrounded_total=F(9, 16),
    floored=(
        (3, ((("mc", "off"), F(1, 2)),), F(1, 2)),
        (4, ((("mc", "off"), F(9, 16)),), F(9, 16)),
    ),
    uniform_route_weights=((("mc", "off"), F(9, 16)),),
    per_setting_gain=F(0),
    derivation="""\
THE ONE-SETTING SLOT WITH r_min = 1/8. hat p_(mc,off) = 1 * ((7/8)(1/2) + 1/8)
= 9/16; kappa = 3: floor(8 * 9/16)/8 = floor(9/2)/8 = 4/8 = 1/2 (THE FLOOR
BITES); kappa = 4: 9/16 unchanged. The t-uniform route gives the same numbers.""",
)

PER_SETTING_ROUTE_CASES: tuple[PerSettingRouteCase, ...] = (
    PSF_TWO_SETTING_NO_DARK,
    PSF_TWO_SETTING_DARK,
    PSF_UNIFORM_NO_DARK,
    PSF_UNIFORM_DARK,
    PSF_ONE_SETTING_NO_DARK,
    PSF_ONE_SETTING_DARK,
)
