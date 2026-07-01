# Kaggle Reference Data

Reference material for the Pokémon TCG AI Battle Challenge. Downloaded from the two competition pages; consolidated here because the Simulation and Strategy Category downloads ship the same card data byte-for-byte.

## Contents

| Path | Origin | Versioned? |
|---|---|---|
| `cards/EN_Card_Data.csv` | Both comp pages | ✅ |
| `cards/JP_Card_Data.csv` | Both comp pages | ✅ |
| `cards/pdf/Card_ID List_EN.pdf` | Both comp pages | ❌ (>100MB, `.gitignore`d) |
| `cards/pdf/Card_ID List_JP.pdf` | Both comp pages | ❌ (>100MB, `.gitignore`d) |
| `sample_submission/main.py` | Simulation Category | ✅ |
| `sample_submission/deck.csv` | Simulation Category | ✅ |

The PDFs are kept locally for visual card lookup but not committed — re-download from Kaggle if needed.

## Source

- Simulation Category: https://www.kaggle.com/competitions/pokemon-tcg-ai-battle
- Strategy Category: https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy

Both competition entries are mandatory to enter the challenge. Downloaded on 2026-07-01.

## Card Data Schema (`EN_Card_Data.csv`)

Columns: `Card ID`, `Card Name`, `Expansion`, `Collection No.`, `Stage (Pokémon)/Type (Energy and Trainer)`, `Rule`, `Category`, `Previous stage`, `HP`, `Type`, `Weakness`, `Resistance (Type)`, `Retreat`, `Move Name`, `Cost`, `Damage`, `Effect Explanation`.

2102 rows (one per card). One card may span multiple rows if it has more than one move.

## Sample Submission

The Kaggle-provided `sample_submission/main.py` is the canonical template for the Simulation Category. Key takeaways for our own agent:

- Entry point: `def agent(obs_dict: dict) -> list[int]`
- Convert the raw dict via `to_observation_class` from `cg.api`
- On the initial call, `obs.select is None` — return the 60 card IDs of the deck (read from `deck.csv`)
- On every other call, return a list of indices into `obs.select.option`, of length in `[obs.select.minCount, obs.select.maxCount]`, with no duplicates
- At runtime the file lives at `/kaggle_simulations/agent/deck.csv`; locally it lives next to `main.py`

Our own submission (`scripts/submit.py`) bundles `main.py` + `deck.csv` following this same convention.
