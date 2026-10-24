# Optical BB84: developer notes

The page for someone inspecting or running the instance is
[README.md](README.md).

## Files

| File | What it is |
| --- | --- |
| `protocol.yaml` | the instance: a protocol document whose receiver is the C1-C3 element graph of catalogue components, with `route` and `acceptance_map` switching the reduction and the acceptance map |
| `surface.py` | loads `protocol.yaml` with the packaged loader and exposes the shared run surface |
| `optics.py`, `device.py` | re-exports of `instances/common/optics.py` and of `ROUTES`, kept for the golden test that imports them |

The document layer
(`instances/declared/`) lowers `protocol.yaml` to the receiver, reduction and compiler
constructors. What the instance needs beyond the document is shared in `instances/common/`:
the receiver as catalogue components and the analytic port Grams
(`optics.py`), the snapped receiver family (`declare.py`), the passive
receiver's requests and the three routes (`passive_device.py`), the hard
errors (`errors.py`), the source part (`sources.py`), the channel interface
(`channel.py`), the below-cutoff witness (`witness.py`) and the honest channel
(one photon, a depolarizer, and loss), the library model
`honest/single_photon_loss_depolarizing.py`.

## Invariants that are easy to break

- **`PARAMETERS` leaves `exact_window` absent; `default_config()` fills
  $m^{\ast}=N+1$.** Absent is a legal declaration, and it selects the uniform
  analytic high-photon bound, which at $N=1$ gives $p_{\mathrm{mc}}=0$ and no
  key. That zero is the correct value of that bound. Do not "fix" it in the
  receiver. The runnable default asks for the smallest exact window instead.
- **The `acceptance_map` row defaults to `merged-discard`; `default_config()`
  fills `announcement-resolved`.** The row describes the declaration surface,
  so a configuration that sets no such key keeps its meaning.
- **No acceptance map may resolve Alice's $\mathsf Z$ bit.** It is the key and
  is never announced. The library model's `raw_joint_distribution` computes
  the raw `X × V` table as a diagnostic only.
- **The declared family is the object every downstream claim is about.**
  `instances/common/declare.py` snaps the float receiver onto an exactly
  admissible family and
  records the displacement in the run record's `snaps`. No module repairs what
  it was handed (`spec/architecture.md` §2.8). No relation between the key rate
  of the declared and the computed family is claimed; `meat-core`'s
  `prop:optol-nobound` shows none holds in general.
- **Expected route ordering:** `encoded >= licensed+two-sector >= licensed`
  (`tests/integration/test_optical_bb84_slice.py` measures it). A result that
  breaks it is a finding.

No claim is made here on whether resolving the multi-click rate moves the loss wall.

## Tests

`tests/unit/test_optical_bb84_{optics,declare,device,honest}.py`;
`tests/integration/test_optical_bb84_slice.py`. `test_optical_bb84_honest.py`
measures how loss moves the no-click and multi-click rates in opposite
directions. The device tests read the template's lowering through
`tests/support/lowered_templates.py` and
`tests/support/optical_bb84_prologue.py`;
`tests/unit/test_declared_lowering_optical.py` holds the lowered station
against `passive_device_requests`.
