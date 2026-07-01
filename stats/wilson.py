r"""Wilson score interval for binomial proportions.

Formal derivation lives in `exercises/ex05_statistical_inference.md`
(Phase 5). This module implements the two-sided Wilson interval used by
[`docs/benchmark-protocol.md`](../docs/benchmark-protocol.md) for every
win-rate report. Wilson dominates the normal approximation near $p = 0$
and $p = 1$ and never leaves $[0, 1]$.

For $k$ successes out of $n$ Bernoulli trials with $\hat p = k/n$ and
$z$ the standard-normal quantile for the desired two-sided coverage:

$$
\hat p_{\pm} \;=\;
\frac{\hat p + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}
     {1 + \frac{z^2}{n}}.
$$
"""

from __future__ import annotations

import math

Z_95 = 1.959963984540054  # two-sided 95% normal quantile


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple[float, float]:
    """Return (lower, upper) endpoints of the Wilson score interval.

    Boundary conventions:
    - trials == 0 → (0.0, 1.0), i.e. the trivial "no information" interval.
    - The endpoints are clamped to [0, 1] but the closed form already
      respects this by construction; the clamp defends against float error.
    """
    if trials < 0:
        raise ValueError(f"trials must be >= 0, got {trials}")
    if successes < 0 or successes > trials:
        raise ValueError(f"successes must be in [0, {trials}], got {successes}")
    if trials == 0:
        return 0.0, 1.0

    n = trials
    p_hat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denom
    margin = z * math.sqrt(p_hat * (1 - p_hat) / n + z2 / (4 * n * n)) / denom
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return lo, hi
