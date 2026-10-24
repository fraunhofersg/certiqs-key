# The pair-source honest models (`ideal_pair`, `spdc_pair`)

These two models generate the statistics a run expects from an honest
implementation of [BBM92](../../bbm92/README.md). They describe the data only. The
security analysis does not trust the source: it assumes nothing about what the
source emits, and no source certificate is taken from these models.

Choose a model with `source_model`: `ideal_pair` or `spdc`. Both use the arm
transmittances $\eta_A$ (`alice_transmittance`) and $\eta_B$
(`bob_transmittance`); detector efficiencies and dark counts belong to the
stations.

## Ideal pair

Each round the source emits one polarization-entangled pair with visibility
$v$ (`visibility`):

$$\rho=v\,\lvert\Phi^+\rangle\langle\Phi^+\rvert+(1-v)\,\frac{\mathbb 1}{4},
\qquad \lvert\Phi^+\rangle=\frac{\lvert VV\rangle+\lvert HH\rangle}{\sqrt2}.$$

Each arm loses its photon independently. The four patterns of surviving photons
have weights $\eta_A\eta_B$, $\eta_A(1-\eta_B)$, $(1-\eta_A)\eta_B$ and
$(1-\eta_A)(1-\eta_B)$. If only one photon survives, its polarization is
maximally mixed, $\mathbb 1/2$; if neither does, both stations receive vacuum.
No round carries more than one photon per arm. Rational parameters give exact
rational statistics.

In a matched basis the two parties' bits disagree with probability $(1-v)/2$,
in either basis.

## SPDC source

The source emits two equal-phase two-mode squeezed vacua, one on the
horizontal modes $A_H$–$B_H$ and one on the vertical modes $A_V$–$B_V$. Each
has mean photon number $\bar n$ in each of its two modes, so the mean number of
emitted pairs per round is $\mu=2\bar n$ (`mean_pairs`). Each squeezer emits $k$ photon
pairs with probability

$$\frac{\bar n^{\,k}}{(1+\bar n)^{k+1}},$$

and its one-pair component is $(\lvert HH\rangle+\lvert VV\rangle)/\sqrt2$.
All pair numbers are included, so multi-pair emission appears in the
statistics. This is a single-spectral-mode model: spectral multimode emission
and visibility noise are not parameters of it, and misalignment is set through
the stations' optics.

### Modes and Grams

Order the input annihilation operators as $(a_{A_H},a_{A_V},a_{B_H},a_{B_V})$.
The state's centred moments are $N=\bar n\,\mathbb 1_4$ and
$M=\sqrt{\bar n(\bar n+1)}\,S$, where $S$ exchanges the two arms' two-mode
blocks. For a set of monitored detector ports, $A$ and $B$ are the $2\times2$
sums of their input Gram matrices at Alice's and Bob's station. They include
the station's detector efficiencies and are multiplied once by that arm's
transmittance; the loss ports are not observed. $A$ and $B$ are Hermitian
contractions, not normalized states.

The vacuum-overlap calculation uses the covariance in annihilation and
conjugate coordinates, which gives the detection matrix
$\operatorname{diag}(K,K^{\mathsf T})$ with $K=\operatorname{diag}(A,B)$.
The **transpose** on Bob's Gram in the formula below is essential, even for
complex Hermitian Grams: an adjoint in its place describes a different source
correlation. Gaussian characteristic functions and on/off detection are
described in Ferraro, Olivares and Paris, *Gaussian states in continuous
variable quantum information* (2005), §§1.5 and 5.3.2, Eq. (5.20). The
reduction below is derived for this model.

### The no-click probability

The full eight-dimensional vacuum determinant is

$$\det\!\Big(\mathbb 1_8+\begin{pmatrix}\bar n\,\mathbb 1_4 & m\,S\\ m\,S & \bar n\,\mathbb 1_4\end{pmatrix}\operatorname{diag}(K,K^{\mathsf T})\Big),
\qquad m=\sqrt{\bar n(\bar n+1)}.$$

Reorder its coordinates into the groups $(a_A,a_B^{*})$ and $(a_B,a_A^{*})$.
The two determinant factors are complex conjugates; one is

$$D=\det\begin{pmatrix}\mathbb 1_2+\bar n A & m B^{\mathsf T}\\ m A & \mathbb 1_2+\bar n B^{\mathsf T}\end{pmatrix}.$$

With $C=\mathbb 1_2+\bar n A$, which is invertible, the Schur complement gives

$$\begin{aligned}
D&=\det C\,\det\!\big(\mathbb 1_2+\bar n B^{\mathsf T}-m^2 A C^{-1}B^{\mathsf T}\big)\\
&=\det\!\big(C(\mathbb 1_2+\bar n B^{\mathsf T})-\bar n(\bar n+1)AB^{\mathsf T}\big)\\
&=\det\!\big(\mathbb 1_2+\bar n\,(A+B^{\mathsf T}-AB^{\mathsf T})\big).
\end{aligned}$$

The second equality uses $AC=CA$. For positive contractions the determinant is
real and positive, by the vacuum-overlap expression; equivalently, its
continuation from zero efficiency cannot cross zero. So the square root of the
full determinant is $D$, and

$$P(\text{no monitored optical click})=\frac1D .$$

All square roots cancel: rational Grams and a rational $\bar n$ give a rational
probability, which is evaluated exactly.

**Limiting cases**, each also obtained by summing the two geometric photon-number
distributions: with both stations fully monitored the vacuum probability is
$(1+\bar n)^{-2}$; with only one arm monitored, at transmittance $\eta$, it is
$(1+\bar n\eta)^{-2}$; with no monitored port it is $1$.

### Click patterns and dark counts

Dark counts are independent: for a set $U$ of the eight detector ports, they
multiply the optical no-click probability of $U$ by
$\prod_{i\in U}(1-p_{\mathrm{dark},i})$. For an exact set $C$ of clicking
ports, inclusion–exclusion gives

$$P(C)=\sum_{T\subseteq C}(-1)^{|T|}\,P\big(\text{no click on }\overline{C}\cup T\big),$$

where $\overline{C}$ is the complement of $C$. The calculation is rational
throughout, dark counts included; exact zeros stay zero, and no cancellation
threshold or photon cutoff enters. Each station then groups its sixteen click
patterns into `nc`, `H`, `V`, `D`, `A`, `mc`. Detector efficiency is already
in the Grams and is not applied a second time.

The stations' Grams are computed from the optics in floating point. Before the
model uses them, they are declared as an exactly valid measurement within the
run's declared tolerance, and the run records the displacement. The statistics
are those of the declared measurement; the displacement is not a bound on the
change in key rate.
