# Threats to Validity — working collection

**Status:** harvest document (Phase 4). Source material for section 7 of
`writeup.md` (budget: ~200 words), built from `decision-journal.md` and
`experiments/registry.md` as the threats occurred, not reconstructed at
the end. Each entry: the threat, the evidence, what was done, and the
one-line version that survives compression.

---

## 1. Construct validity — we kept authoring the test condition

The recurring pattern, named in ADR-002's erratum: every time the test
condition was *invented* (mirror-deck H1, a homemade candidate pool, a
filler opponent model chosen for convenience) instead of *imported from
deployment*, the two diverged — H1 held in the mirror but the agent
lost to its own baseline on the ladder (submission-log row #3);
determinization condition moved the agent 11–16 pp (EXP-009/010), the
same order as the largest deck effect.

**Counterweight, honestly reported:** when the real field finally
arrived, EXP-011 reproduced EXP-007's homemade-pool deck ranking in
exactly the same order — the proxy pool was flawed *and* immaterial to
that particular decision. The threat is real but not uniformly fatal;
the writeup should say when proxies sufficed, not only when they broke.

**Residual:** the official Abomasnow starter was never tested *as our
deck* (open-ideas `official-starter-as-candidate`).

**One-liner:** local conditions we authored diverged from deployment
three times; the one time we could check end-to-end, the proxy ranking
survived contact with the real field.

## 2. Instrument validity — the engine fought the measurement

Three engine clocks (TIL #2), two of which damaged EXP-011 before any
verdict: the 600 s overage bank injected `TIMEOUT` losses *only against
slow-deck challengers* (anti-challenger bias in a selection
experiment), and the first fix validated green on a probe that could
not have failed, then poisoned 11 more cells; the 2000 s episode cap
aborted sweeps without writing rows (loud, therefore harmless). A
separate encoding bug misread −1 losses as draws in a first analysis
(EXP-010) — caught by the trajectory corpus, line 1.

**What was done:** registry amendments (never rewrites) with enumerated
affected units; heal-don't-discard with an equivalence argument
(seeded, iteration-bounded arms); probes required to fail loudly and to
run on known-failing inputs; regression tests pinning each mode;
outcome encodings read from the producer, never assumed.

**One-liner:** the instrument broke three ways mid-experiment; all
three are documented amendments with regression tests, and no verdict
was computed on poisoned rows.

## 3. Statistical power — what the design could not have seen

`exercises/ex04_evaluator_math.md` §3: EXP-011's paired design had 80 %
power only for effects ≳ 13.5 pp (n = 200, Bonferroni m = 3). The
−3.0 pp v1-tuned result is a *tie under the rule*, not demonstrated
equality. Forward: the H4 per-feature ablation at N = 500 and k = 7 has
MDE ≈ 7 pp — several features will plausibly land "inconclusive at
this N," and the pre-registration treats a null as a finding.

**One-liner:** paired tests with ties-to-incumbent decide replacements;
they bound, but do not measure, small effects — reported MDEs make that
explicit.

## 4. Ladder non-stationarity — absolute ratings are not comparable

A frozen, deterministic agent drifted 38 points in 11 days
(submission-log row #2: 527.9 → 536.0 → 497.8) — the ladder pool moves
under every rating. Consequence, adopted as a rule: only same-instant
differences between simultaneously active submissions are evidence
(rows #3 vs #4, and the planned #4 vs #5 A/B).

**One-liner:** the ladder's own drift (±38 on a frozen agent) exceeds
many effects of interest; every ladder claim is a same-instant paired
read.

## 5. Local hardware ≠ Kaggle worker

Stated at EXP-012's registration: Policy C yields a hardware-dependent
iteration count, so local runs validate budget logic, artifact absence,
and strength consistency — not the deployed strength itself. The
per-move ~6.75 s local yield (~1 370 iterations) has no measured Kaggle
counterpart.

**One-liner:** the shipping clock was validated locally; its Kaggle
iteration yield is unmeasured and assumed similar in order only.

## 6. Wall-clock nondeterminism in long sweeps

The same engine seed completed in 120 s after crashing a sweep at
2 001.9 s (journal 2026-07-22; host-suspend hypothesis). Pairing is
anchored on the engine seed and completed-game outcomes are
clock-independent, so verdicts are unaffected — but no timing claim in
the writeup may come from sweep byproducts; timing gets dedicated runs
(EXP-008 is the template).

**One-liner:** wall-clock numbers from long unattended sweeps are
untrusted; timing claims trace to dedicated calibration runs.

## 7. Interim peeks — controlled, logged, rule-locked

Peeks happened (EXP-009 at n = 113; EXP-011 at 397/600). Controls: the
analysis scripts' `--interim` mode refuses verdicts, every peek was
journaled before completion with "no decision is taken here," and no
peek changed N, the rule, or the stopping point.

**One-liner:** interim looks were taken and disclosed; decision rules
ran only on complete, pre-registered designs.

---

*Compression target for `writeup.md` §7: threats 1, 2 and 4 carry the
most weight; 3 and 5–7 can compress to a sentence each. The section's
job is not to confess everything equally but to show the reader which
failure modes were live and how each was contained.*
