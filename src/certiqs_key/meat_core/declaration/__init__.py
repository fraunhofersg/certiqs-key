"""The declaration: its data, its admission, its validation, its sectors.

declaration  the tuple D of ``def:declaration``, as data
admission    the EXACT admission of the declared families -- ``def:declaration``'s
             exact-admissibility paragraph and ``eq:declorder``; no
             declared-tolerance apparatus exists
validation   the hard checks of ``def:admissible-declaration`` and spec/architecture.md
3.6, which
             this module owns because in one process a composition root is not a
             module but the input validation the engine runs before it solves
bundle       an operator bundle read into a declaration
companion    the admission of the compiled reference companion (no run of its own)
             beside an admitted declaration (``req:companion-admission``)
sectors      the classification, the removal checklist and the operations
             refused (``def:classes``, ``prop:exact-cancellation``, ``thm:removal``,
             ``prop:retention``, ``prop:no-averaging``,
             ``prop:removal-compose``)
"""

from __future__ import annotations
