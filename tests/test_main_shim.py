"""Tests for the top-level `main.py` Kaggle entry point."""

from __future__ import annotations

import importlib
import importlib.util
import pathlib
import sys


def _load_main_module(monkeypatch, tmp_path: pathlib.Path):
    """Import main.py in isolation, with cwd pointing at a fake submission root."""
    (tmp_path / "deck.csv").write_text("\n".join(str(1000 + i) for i in range(60)) + "\n")
    monkeypatch.chdir(tmp_path)

    src = pathlib.Path(__file__).resolve().parent.parent / "main.py"
    spec = importlib.util.spec_from_file_location("kaggle_main", src)
    module = importlib.util.module_from_spec(spec)
    sys.modules["kaggle_main"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_agent_returns_deck_on_initial_call(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_main_module(monkeypatch, tmp_path)
    deck = module.agent({"select": None})
    assert len(deck) == 60
    assert all(isinstance(x, int) for x in deck)


def test_agent_returns_indices_within_bounds(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_main_module(monkeypatch, tmp_path)
    obs = {
        "select": {
            "option": [{"id": i} for i in range(5)],
            "minCount": 2,
            "maxCount": 2,
        }
    }
    choice = module.agent(obs)
    assert len(choice) == 2
    assert len(set(choice)) == 2
    assert all(0 <= i < 5 for i in choice)
