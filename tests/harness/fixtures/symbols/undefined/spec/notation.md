# Notation Reference (fixture)

A miniature of `spec/notation.md`: one symbol table read by the positional
Macro/Rendered rule, and a section 3.9 read by the inline rule. Every other
column is prose the checker does not parse.

## 3. Symbol tables

### 3.1 State spaces and operator sets

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Hs{A}` | $\mathcal{H}(A)$ | Hilbert space of the system label $A$ | |
| `\Qsys` | $Q$ | The declared measured system | Sectors $Q_s$ |
| `\Flag` | $\mathrm{Flg}$ | Flag system | Post-squashing only |

### 3.8 Miscellaneous operators

| Macro | Rendered | Meaning | Notes |
| --- | --- | --- | --- |
| `\Wflag` | $W_{\mathrm{Flg}}$ | Flag-space weight | Expands through `\Flag`'s braces |

### 3.9 Reserved, superseded, and deprecated symbols

**Reserved (meaning never established by the sources):** `\Res`
($R_{\mathrm{es}}$).

## 4. What is not catalogued here

`\Loc` and `\Spare` are module-local and live in part B; they are deliberately
absent from every table above.
