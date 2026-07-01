"""Tests for the standalone Kaggle shim in submissions/heuristic_main.py."""

from __future__ import annotations

import importlib.util
import pathlib
import sys


def _load_shim(monkeypatch, tmp_path: pathlib.Path):
    (tmp_path / "deck.csv").write_text("\n".join(str(1000 + i) for i in range(60)) + "\n")
    monkeypatch.chdir(tmp_path)
    src = pathlib.Path(__file__).resolve().parent.parent / "submissions" / "heuristic_main.py"
    spec = importlib.util.spec_from_file_location("heuristic_shim", src)
    module = importlib.util.module_from_spec(spec)
    sys.modules["heuristic_shim"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_heuristic_shim_returns_deck_on_initial_call(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_shim(monkeypatch, tmp_path)
    deck = module.agent({"select": None})
    assert len(deck) == 60


def test_heuristic_shim_picks_first_maxcount(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_shim(monkeypatch, tmp_path)
    obs = {
        "select": {
            "option": [{"id": i} for i in range(5)],
            "minCount": 1,
            "maxCount": 2,
        }
    }
    assert module.agent(obs) == [0, 1]
