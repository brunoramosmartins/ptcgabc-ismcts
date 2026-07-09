"""Bundle the current agent as a .tar.gz for Kaggle upload.

Kaggle expects a `.tar.gz` archive with `main.py` and `deck.csv` **at the
top level** (no nesting):

    submission.tar.gz
    ├── main.py
    └── deck.csv

Runtime layout on the worker: files land at `/kaggle_simulations/agent/`.
Max bundle size: 197.7 MiB. See `docs/engineering.md` for the full contract.

Usage:

    python scripts/submit.py                       # → submission.tar.gz
    python scripts/submit.py --out build/foo.tar.gz
    python scripts/submit.py --deck decks/selected/deck.csv --main main.py

The script does **not** upload anything. Author uploads the resulting archive
manually via the Kaggle "My Submissions" tab, per the git/GitHub rules in
`.claude/CLAUDE.md`.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys
import tarfile
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MAIN = REPO_ROOT / "main.py"
DEFAULT_DECK = REPO_ROOT / "decks" / "selected" / "deck.csv"
# Built bundles are artifacts, not source: they land in build/ (already
# gitignored), keeping the repo root clean. Kaggle's "top level"
# requirement applies to the files INSIDE the archive, not to where the
# archive itself lives.
DEFAULT_OUT = REPO_ROOT / "build" / "submission.tar.gz"

BUNDLE_MAX_BYTES = 197 * 1024 * 1024 + int(0.7 * 1024 * 1024)


def _validate_deck(deck_path: pathlib.Path) -> None:
    """Fail fast if deck.csv is not 60 valid integer lines."""
    lines = deck_path.read_text().splitlines()
    if len(lines) < 60:
        raise ValueError(
            f"{deck_path} has {len(lines)} lines; Kaggle requires 60."
        )
    for i in range(60):
        try:
            int(lines[i])
        except ValueError as exc:
            raise ValueError(
                f"{deck_path}:{i + 1} is not an integer card ID: {lines[i]!r}"
            ) from exc


def _validate_main(main_path: pathlib.Path) -> None:
    """Sanity-check the entry point exposes a top-level `agent` function."""
    src = main_path.read_text()
    if "def agent(" not in src:
        raise ValueError(
            f"{main_path} does not define a top-level `agent` function."
        )


# Engine modules the ISMCTS shim needs at runtime, bundled preserving
# their repo-relative package structure so imports work unchanged.
ENGINE_MODULES = [
    "env/__init__.py",
    "env/search_engine.py",
    "search/__init__.py",
    "search/determinize.py",
    "search/node.py",
    "search/ucb.py",
    "search/ismcts.py",
]


def build_bundle(
    main_path: pathlib.Path,
    deck_path: pathlib.Path,
    out_path: pathlib.Path,
    with_engine: bool = False,
) -> pathlib.Path:
    """Assemble the .tar.gz Kaggle expects.

    Args:
        main_path: Top-level ``main.py`` (must define ``agent``).
        deck_path: 60-line deck CSV.
        out_path: Destination archive.
        with_engine: When True, also bundle ``ENGINE_MODULES`` (the
            ISMCTS search stack) preserving their package paths. The
            files are copied from the repo root next to ``scripts/``.

    Returns:
        The archive path.

    Raises:
        ValueError: On main/deck validation failure, a missing engine
            module, or an oversized bundle.
    """
    _validate_main(main_path)
    _validate_deck(deck_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        staging = pathlib.Path(tmp)
        shutil.copy2(main_path, staging / "main.py")
        shutil.copy2(deck_path, staging / "deck.csv")
        arcnames = ["main.py", "deck.csv"]

        if with_engine:
            for rel in ENGINE_MODULES:
                src = REPO_ROOT / rel
                if not src.exists():
                    raise ValueError(f"engine module missing: {src}")
                dest = staging / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                arcnames.append(rel)

        with tarfile.open(out_path, "w:gz") as tar:
            for arc in arcnames:
                tar.add(staging / arc, arcname=arc)

    size = out_path.stat().st_size
    if size > BUNDLE_MAX_BYTES:
        raise ValueError(
            f"Bundle {out_path} is {size} bytes; Kaggle max is "
            f"{BUNDLE_MAX_BYTES} bytes (197.7 MiB)."
        )
    return out_path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--main", type=pathlib.Path, default=DEFAULT_MAIN)
    p.add_argument("--deck", type=pathlib.Path, default=DEFAULT_DECK)
    p.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    p.add_argument("--with-engine", action="store_true",
                   help="Bundle the ISMCTS search stack (env/ + search/).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    out = build_bundle(args.main, args.deck, args.out,
                       with_engine=args.with_engine)
    size_mib = out.stat().st_size / (1024 * 1024)
    with tarfile.open(out) as tar:
        names = sorted(tar.getnames())
    print(f"wrote {out} ({size_mib:.2f} MiB)")
    print(f"contents: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
