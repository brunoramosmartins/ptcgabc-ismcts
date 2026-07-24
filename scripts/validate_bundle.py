"""Reproduce the Kaggle Validation Episode locally.

The Validation Episode plays the submitted agent against a copy of
itself in a full `cabt` match. This script reproduces it: extract the
bundle, then run the bundled agent against itself in a real match,
isolated in a subprocess whose CWD is the extracted bundle.

Crucially, the agent is loaded by *path* (a string handed to
`env.run`), not by `import main` — so kaggle-environments runs it the
same way the worker does, via `get_last_callable` → `exec(code, env)`,
where ``__file__`` is undefined. An earlier version imported the module
(``__file__`` defined) and therefore missed exactly the crash that took
down the real Validation Episode. Load agents the way the platform
does, or the check is theatre.

    python scripts/validate_bundle.py [build/submission-ismcts.tar.gz]

Exit 0 and "SELF-PLAY OK" ⇒ the bundle survives a full self-play match
locally. A traceback or an ERROR status ⇒ the same failure the
Validation Episode would hit, now with a local stack trace.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tarfile
import tempfile

DEFAULT_BUNDLE = "build/submission-ismcts.tar.gz"

# Must strictly exceed the engine's own whole-episode backstop
# (`runTimeout = 2000`), or this harness can kill a match the platform
# would have allowed and report our own impatience as a bundle failure.
# The old 900 s was sized for the fixed-500-iteration shim (~45 s
# self-play); under the adaptive budget each agent may legitimately spend
# up to its full 600 s bank, so two agents can run far past that.
SELF_PLAY_TIMEOUT = 2100

# Runs inside the extracted bundle dir. Loads the agent BY PATH so
# kaggle-environments execs it exactly as the worker does. debug=True
# surfaces agent exceptions instead of silently marking ERROR.
_SELF_PLAY = r"""
import os, sys, traceback
from kaggle_environments import make

main_path = os.path.abspath("main.py")
env = make("cabt", debug=True, configuration={"randomSeed": 42})
try:
    env.run([main_path, main_path])
except Exception:
    print("=== EXCEPTION DURING env.run ===")
    traceback.print_exc()
    sys.exit(2)

bad = []
for i in range(2):
    st = env.state[i]
    obs = st.get("observation") or {}
    print(f"agent {i}: status={st['status']} reward={st['reward']} "
          f"remainingOverageTime={obs.get('remainingOverageTime')}")
    # ERROR = crashed before deciding. TIMEOUT = drained the 600s bank,
    # which is the failure mode the adaptive budget (EXP-008) exists to
    # prevent — a check that only looks for ERROR would pass a forfeit.
    if st["status"] in ("ERROR", "TIMEOUT"):
        bad.append(f"agent {i}: {st['status']}")

n_decisions = len(env.steps)
print(f"steps: {n_decisions}")
if bad:
    print("SELF-PLAY FAILED: " + "; ".join(bad))
    sys.exit(3)
print(f"SELF-PLAY OK: completed {n_decisions} steps")
sys.exit(0)
"""


def main() -> int:
    bundle = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BUNDLE)
    if not bundle.exists():
        print(f"bundle not found: {bundle}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(bundle) as tar:
            tar.extractall(tmp)  # noqa: S202 - our own freshly-built bundle
        print(f"extracted {bundle} -> {tmp}")
        print("running self-play (this exercises real decisions under the "
              "adaptive budget;\nboth agents think at ~6.75 s/move, so "
              "expect 10-20 minutes, not seconds)...\n")
        proc = subprocess.run(
            [sys.executable, "-c", _SELF_PLAY],
            cwd=tmp, text=True, timeout=SELF_PLAY_TIMEOUT,
        )
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
