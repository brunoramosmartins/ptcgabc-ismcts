# Exercise 04 — Evaluator, Ablation Statistics, and the Shipping Clock

Phase 4 exercises companion to
[`notes/phase4-evaluator-design.md`](../notes/phase4-evaluator-design.md)
and [`evaluator/threat.py`](../evaluator/threat.py). Each answer is short
and rigorous; where code is referenced, the code is the source of truth
and the exercise justifies *why* it looks the way it does. Numbers come
from `experiments/registry.md` (EXP-008, EXP-011, EXP-012).

## 1. Why Wilson and not Wald at the boundary

EXP-011 produced the cell `aggro-fire` vs `dragapult-ex`: $w = 50$ wins
in $n = 50$. The Wald interval is

$$
\hat p \pm z \sqrt{\frac{\hat p (1 - \hat p)}{n}}
= 1 \pm 1.96 \sqrt{\frac{1 \cdot 0}{50}} = [1, 1],
$$

a zero-width interval claiming certainty after 50 games — absurd. The
Wilson interval comes from inverting the *score* test: keep every $p$
that the null $H_0\!: p = p_0$ would not reject,

$$
\left| \frac{\hat p - p_0}{\sqrt{p_0 (1 - p_0)/n}} \right| \le z .
$$

Squaring and clearing the denominator:

$$
(\hat p - p_0)^2 \, n = z^2 p_0 (1 - p_0)
\;\Longleftrightarrow\;
p_0^2 \left(n + z^2\right) - p_0 \left(2 n \hat p + z^2\right) + n \hat p^2 = 0 .
$$

The quadratic formula gives the two interval endpoints

$$
p_0 = \frac{\hat p + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat p (1-\hat p)}{n} + \frac{z^2}{4 n^2}}}{1 + \frac{z^2}{n}} .
$$

At $\hat p = 1$, $n = 50$, $z = 1.96$ ($z^2 = 3.8416$):

$$
\text{center} = \frac{1 + 3.8416/100}{1 + 3.8416/50} = \frac{1.038416}{1.076832} = 0.96435,
\qquad
\text{halfwidth} = \frac{1.96 \cdot \frac{1.96}{2 \cdot 50}}{1.076832} = \frac{0.038416}{1.076832} = 0.03568,
$$

so the interval is $[0.9287,\, 1.0000]$ — exactly the `[0.929, 1.000]`
printed by `scripts/exp011_analysis.py`. The variance term $z^2/(4n^2)$
never vanishes, which is what keeps the interval honest at the
boundary. This is why the house rule is *Wilson, never bare
proportions*: the cells where Wald degenerates (0 % and 100 %) are
precisely the cells people most want to quote.

## 2. The H4 family grows to $k = 7$

H4 tests every feature of the final evaluator by dropping it and
running a paired contrast. With F7 the family is $k = 7$, so
per-feature significance uses $\alpha' = \alpha / 7$:

$$
\alpha' = \frac{0.05}{7} = 0.007143,
\qquad
z_{\alpha'/2} = \Phi^{-1}\!\left(1 - \frac{0.007143}{2}\right) = \Phi^{-1}(0.996429) \approx 2.69 ,
$$

versus $z \approx 2.64$ at $k = 6$. The cost of admitting F7 is a
half-percent stricter criterion for *every* feature — the design note's
"keep $k$ small" rule priced in math. (Report raw and corrected
$p$-values side by side, per the statistical-reporting house rule.)

## 3. What effect size can the paired design even see?

The McNemar/sign test looks only at discordant pairs. Let $n$ be the
paired instances, $d$ the discordant count, and
$\Delta = (\text{only}_A - \text{only}_B)/n$ the paired win-rate
difference. Since $\text{only}_A + \text{only}_B = d$,

$$
\text{only}_A = \frac{d + n\Delta}{2} .
$$

Under $H_0$, $\text{only}_A \sim \mathrm{Bin}(d, \tfrac12)$ with mean
$d/2$ and sd $\sqrt{d}/2$. The normal-approximation test rejects when
$|\text{only}_A - d/2| > z_{\alpha/2} \sqrt{d}/2$. Under the
alternative the mean shifts by $n\Delta/2$, so power $1-\beta$ requires

$$
\frac{n \Delta / 2}{\sqrt{d}/2} \ge z_{\alpha/2} + z_{1-\beta}
\;\Longleftrightarrow\;
\Delta_{\min} = \frac{\sqrt{d}\,\left(z_{\alpha/2} + z_{1-\beta}\right)}{n} .
$$

**EXP-011 check (retrospective):** $n = 200$, v1-tuned's $d = 70$,
Bonferroni $m = 3$ gives $z_{\alpha/2} = 2.394$, and $z_{0.8} = 0.842$:

$$
\Delta_{\min} = \frac{\sqrt{70} \cdot (2.394 + 0.842)}{200}
= \frac{8.367 \cdot 3.236}{200} \approx 0.135 .
$$

The design had 80 % power only for $\gtrsim$ 13.5 pp challenger
effects — coherent with what happened: the −12.5 pp aggro-fire effect
was detected (barely, corrected $p = 0.011$), the −3.0 pp v1-tuned
effect had no chance, and the rule correctly reads that as "tie goes
to the incumbent", not "proved equal".

**Forward consequence for H4 (Phase 5):** at $N = 500$ pairs,
$z_{\alpha'/2} = 2.69$ ($k = 7$), and an optimistic discordance of
$q = 0.2$ ($d = 100$):

$$
\Delta_{\min} = \frac{\sqrt{100} \cdot (2.69 + 0.842)}{500} \approx 0.071 .
$$

Per-feature rollout-guidance effects are plausibly *smaller* than
7 pp. So H4's realistic outcome is a few features separating and
several honest "inconclusive at this $N$" verdicts — which the
research question treats as findings, not failures. Knowing this
*before* Phase 5 is the point of the exercise.

## 4. F7's threat model is a signal, not a bound

Let $M(p)$ be card $p$'s move list and, per `evaluator/threat.py`,

$$
D(p, e) = \max \,\{\, d_{\text{printed}}(m) : m \in M(p),\; c(m) \le e \,\} \cup \{0\}.
$$

**(a) Monotonicity.** If $e' \ge e$ then
$\{m : c(m) \le e\} \subseteq \{m : c(m) \le e'\}$, and a max over a
superset is no smaller, so $D(p, e') \ge D(p, e)$. The $+1$ in
$T = \max_p D(p, e_p + 1)$ therefore never *reduces* a threat — it is
the one-attachment-per-turn ceiling applied to every board Pokémon at
once.

**(b) Damage axis — floor.** For variable-damage moves the printed
base is parsed ("100×" → 100), so
$d_{\text{printed}}(m) \le d_{\text{true}}(m)$ and, for any fixed
affordability set, the computed max under-estimates: this axis can
only *miss* threat.

**(c) Cost axis — ceiling.** $c(m)$ counts energy tokens color-blind:
a move needing $\{R\}\{R\}$ is admitted when two $\{W\}$ are attached.
The true affordable set is a subset of the admitted one, so on this
axis the computed max *over*-estimates: F7 can fire on a threat that
is not actually live next turn.

**(d) Compound.** Since (b) pushes down and (c) pushes up,
$T$ is neither a lower nor an upper bound of the true worst-case
next-turn damage. Why is that acceptable? Because F7 is a *preference
rule* — it reorders options, it does not estimate value. A biased
reordering signal is exactly what the H4 ablation measures: if the
compound bias makes F7 useless or harmful, the ablation says so and
the descope rule removes it. The approximations would only be a
methodological problem if we claimed the trade behavior follows from
the model being exact — we claim only that it is measurable.

## 5. The net-score algebra of retreating

With uniform weight $W = 1$: an ATTACK option scores $+1$ (F1).
A RETREAT option scores $-1$ (F6), plus F7's
$+\text{prizes}(a)$ when the active $a$ is under lethal threat. Net,
under threat:

$$
s(\text{RETREAT}) - s(\text{ATTACK}) = \bigl(\text{prizes}(a) - 1\bigr) - 1 = \text{prizes}(a) - 2 .
$$

| active | prizes | net | greedy behavior under lethal threat |
|---|---|---|---|
| plain | 1 | $-1$ | attacks — accepts the 1-prize trade |
| ex | 2 | $0$ | exact tie — coin-flips between trade and retreat |
| Mega ex | 3 | $+1$ | retreats — refuses the 3-prize trade |

The tie at prizes $= 2$ is *designed indifference*, not an oversight:
breaking it would require a second constant (a $\lambda \ne 1$),
violating the one-feature-one-weight descope rule, and uniform weights
are the author's declared choice for a clean H4 interpretation. If the
ablation shows F7 matters, tuning $\lambda$ is a *registered* follow-up
with its own experiment — not a silent tweak.

## 6. Policy C's clock, derived — and EXP-012's wall-clock estimate

Policy C spends, at each decision, $t_k = (b_k - r)/h$ with reserve
$r = 60$ s, horizon $h = 80$, and bank $b_1 = 600$ s. The bank then
evolves as $b_{k+1} = b_k - t_k$. Substituting:

$$
b_{k+1} - r = (b_k - r) - \frac{b_k - r}{h} = (b_k - r)\left(1 - \frac{1}{h}\right),
$$

so the *spendable* bank decays geometrically,

$$
b_k - r = (b_1 - r) \left(\frac{h-1}{h}\right)^{k-1} = 540 \cdot \left(\frac{79}{80}\right)^{k-1},
\qquad
t_k = \frac{540}{80} \left(\frac{79}{80}\right)^{k-1} = 6.75 \cdot 0.9875^{\,k-1} .
$$

**(a) "Cannot deplete by construction", formalized.** Every factor
$(79/80)^{k-1} > 0$, so $b_k > r = 60$ s for all $k$: the bank never
reaches the reserve, for *any* game length or hardware speed — the
worst case is vanishing per-move budgets, never a forfeit. (The floor
$t \ge 0.05$ s spends at most $0.05$ s/move once budgets get that
small, which the reserve absorbs for hundreds of moves.)

**(b) Cumulative spend after $m$ decisions** (geometric sum):

$$
S_m = \sum_{k=1}^{m} t_k = 540 \left(1 - \left(\frac{79}{80}\right)^{m}\right).
$$

At the observed decision depth $m \approx 65$ (EXP-007/008 saw at most
68–69):

$$
\left(\frac{79}{80}\right)^{65} = e^{65 \ln(0.9875)} = e^{-65 \cdot 0.012579} = e^{-0.8176} \approx 0.4415,
\qquad
S_{65} \approx 540 \cdot 0.5585 \approx 302 \text{ s} .
$$

EXP-008's confirmation stage observed a cumulative p99 of **310.7 s**
over 80 games — the geometric model lands within 3 % of the measured
tail, which is the derivation validating the instrument rather than
the other way around.

**(c) EXP-012 ETA.** Per match: our seat $\approx 302$ s (upper bound —
fast forced selects spend less), heuristic opponent $\approx 0$,
engine stepping overhead small $\Rightarrow \approx 5\text{–}6$ min per
match. The sweep is $4 \times 50 = 200$ matches:

$$
200 \times 5.5 \text{ min} \approx 18 \text{ h} .
$$

This is the roadmap's "wall-clock estimate" exercise made concrete —
and it is also the *prediction* the run tests: per-match `seconds`
far above $\sim 360$ s would mean the budget model is wrong somewhere,
which is exactly what EXP-012's operational columns exist to catch.
