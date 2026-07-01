"""Tests for scripts/submit.py — the Kaggle bundle builder."""

from __future__ import annotations

import pathlib
import tarfile

import pytest

from scripts.submit import build_bundle


def _write_deck(path: pathlib.Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


def _write_valid_deck(path: pathlib.Path) -> None:
    _write_deck(path, [str(1000 + i) for i in range(60)])


def _write_valid_main(path: pathlib.Path) -> None:
    path.write_text(
        "def agent(obs_dict):\n"
        "    return []\n"
    )


def test_build_bundle_produces_flat_archive(tmp_path: pathlib.Path) -> None:
    main = tmp_path / "main.py"
    deck = tmp_path / "deck.csv"
    out = tmp_path / "submission.tar.gz"
    _write_valid_main(main)
    _write_valid_deck(deck)

    build_bundle(main, deck, out)

    assert out.exists()
    with tarfile.open(out, "r:gz") as tar:
        names = sorted(tar.getnames())
    assert names == ["deck.csv", "main.py"]


def test_deck_must_have_60_lines(tmp_path: pathlib.Path) -> None:
    main = tmp_path / "main.py"
    deck = tmp_path / "deck.csv"
    out = tmp_path / "submission.tar.gz"
    _write_valid_main(main)
    _write_deck(deck, [str(1000 + i) for i in range(59)])

    with pytest.raises(ValueError, match="60"):
        build_bundle(main, deck, out)


def test_deck_lines_must_be_integers(tmp_path: pathlib.Path) -> None:
    main = tmp_path / "main.py"
    deck = tmp_path / "deck.csv"
    out = tmp_path / "submission.tar.gz"
    _write_valid_main(main)
    _write_deck(deck, ["not-an-int"] + [str(1000 + i) for i in range(59)])

    with pytest.raises(ValueError, match="card ID"):
        build_bundle(main, deck, out)


def test_main_must_define_agent(tmp_path: pathlib.Path) -> None:
    main = tmp_path / "main.py"
    deck = tmp_path / "deck.csv"
    out = tmp_path / "submission.tar.gz"
    main.write_text("def not_agent(obs):\n    return []\n")
    _write_valid_deck(deck)

    with pytest.raises(ValueError, match="agent"):
        build_bundle(main, deck, out)
