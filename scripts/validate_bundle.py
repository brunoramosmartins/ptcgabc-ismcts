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

bad = False
for i in range(2):
    st = env.state[i]
    print(f"agent {i}: status={st['status']} reward={st['reward']}")
    if st["status"] == "ERROR":
        bad = True

n_decisions = len(env.steps)
print(f"steps: {n_decisions}")
if bad:
    print("SELF-PLAY FAILED: an agent errored (see traceback above)")
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
        print("running self-play (this exercises real decisions; "
              "may take a few minutes)...\n")
        proc = subprocess.run(
            [sys.executable, "-c", _SELF_PLAY],
            cwd=tmp, text=True, timeout=900,
        )
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
