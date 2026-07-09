# ISMCTS — Step-by-Step Walkthrough

High-level map of what happens, in which file, when the ISMCTS agent
plays. Two zoom levels: the **match loop** (how a local EXP match
drives the agents) and the **decision loop** (what one
`ISMCTSAgent.choose()` call does internally). Companion to the formal
pipeline diagram in [`mdp-formalization.md`](mdp-formalization.md);
this document is deliberately operational — every box names the
function that implements it.

## Zoom 1 — one local match (EXP-003 flow)

```mermaid
sequenceDiagram
    participant L as local_ladder.main()<br/>(scripts/local_ladder.py)
    participant E as cabt env<br/>(kaggle_environments)
    participant W as _wrap_for_cabt()<br/>(scripts/local_ladder.py)
    participant A as ISMCTSAgent.choose()<br/>(agents/ismcts_agent.py)
    participant H as HeuristicAgent.choose()<br/>(agents/heuristic_agent.py)

    L->>L: build agents via AGENT_REGISTRY[name](seed, deck, iterations)
    L->>E: make("cabt", randomSeed=seed); env.run([wrap_a, wrap_b])
    loop until current.result != -1
        E->>W: obs dict (select, current, logs, search_begin_input)
        alt first call (obs.select is None)
            W-->>E: 60-card deck list
        else acting seat = ISMCTS
            W->>A: choose(obs)
            A-->>W: option indices
            W-->>E: indices
        else acting seat = heuristic
            W->>H: choose(obs)
            H-->>W: first maxCount indices
            W-->>E: indices
        end
        E->>E: apply selection, resolve effects,<br/>advance state (native engine)
    end
    E-->>L: env.state rewards
    L->>L: row {outcome, fallbacks}; summarize()<br/>→ Wilson CI (stats/wilson.py)
```

## Zoom 2 — one ISMCTS decision (`ismcts.decide`)

Everything below happens inside a single `choose()` call, i.e. one
in-game decision. Budget: `iterations` (EXP-003: 1000).

```mermaid
sequenceDiagram
    participant D as ismcts.decide()<br/>(search/ismcts.py)
    participant S as sample_determinization()<br/>(search/determinize.py)
    participant B as search_begin/step/end()<br/>(env/search_engine.py)
    participant N as InfoSetNode<br/>(search/node.py)
    participant U as ucb1_score()<br/>(search/ucb.py)

    D->>D: root = InfoSetNode()<br/>root_moves = enumerate_moves(obs.select)
    loop iterations (default 1000)
        D->>S: sample_determinization(obs, decks, rng)
        S->>S: visible_cards(): recursive sweep by playerIndex
        S->>S: hidden pools = 60-list − visible;<br/>shuffle; slice deck/prize/hand segments
        S-->>D: determinization kwargs
        D->>B: search_begin(obs, **det)
        B->>B: lib.SearchBegin(blob + arrays)<br/>→ engine rebuilds the battle
        B-->>D: {observation, search_id}
        loop selection descent
            D->>D: enumerate_moves(select)<br/>keys = canonical option JSON
            D->>N: mark_available(keys)  [m_a += 1]
            alt node has unvisited available moves
                D->>D: EXPAND: rng.choice(unvisited)
                D->>B: search_step(id, indices)
                D->>D: ROLLOUT: uniform random到 terminal<br/>(_rollout, ~93 steps, ~11 ms)
            else all available moves visited
                D->>U: score = q(±sign) + c·√(ln m_a / n_a)
                Note over D,U: sign flips at opponent nodes<br/>(they minimize root's value)
                D->>B: search_step(id, best move indices)
            end
        end
        D->>N: BACKPROP: node.update(r_T) along path<br/>r_T ∈ {−1, 0, +1} from root's perspective
    end
    D->>B: search_end()  [engine recycles memory]
    D->>N: root.best_action_by_visits()
    D-->>D: map winning key → indices in the REAL obs;<br/>return list[int]
```

## The same story as a table

| # | Step | Where | What happens |
|---|---|---|---|
| 1 | Observation arrives | `scripts/local_ladder.py::_wrap_for_cabt` (local) / `main.py::agent` (Kaggle) | Raw dict: `select` (legal options), `current` (board), `logs`, `search_begin_input` (serialized state blob) |
| 2 | Decision entry | `agents/ismcts_agent.py::ISMCTSAgent.choose` | Delegates to `decide()`; catches `SearchApiError`/`DeterminizationError` → heuristic fallback + `fallback_events` log |
| 3 | Root setup | `search/ismcts.py::decide` | Empty `InfoSetNode` root; `enumerate_moves` builds (canonical key → indices) for the real observation |
| 4 | Determinize | `search/determinize.py::sample_determinization` | Sweep visible cards (`visible_cards`), subtract from the 60-lists, shuffle hidden pools, slice into deck/prize/hand/active segments. Fail-loud if accounting doesn't close |
| 5 | Reconstruct | `env/search_engine.py::search_begin` → native `SearchBegin` | Engine rebuilds a playable battle from blob + our hidden assignment; returns `{observation, search_id}` |
| 6 | Select | `search/ismcts.py::_select_move` + `search/ucb.py::ucb1_score` | Subset-armed UCB1 over moves legal in *this* determinization; availability counts (`m_a`) instead of parent visits; sign flip at opponent nodes |
| 7 | Step | `env/search_engine.py::search_step` → native `SearchStep` | Applies the move inside the simulation; new `{observation, search_id}` |
| 8 | Expand + Rollout | `search/ismcts.py` (expansion branch + `_rollout`) | One unvisited move expanded per iteration (Browne's default); uniform-random play to terminal (~0.12 ms/step) |
| 9 | Backprop | `search/node.py::InfoSetNode.update` | Terminal reward $r_T \in \{-1, 0, +1\}$ (ADR-004) added along the visited path |
| 10 | Decide | `search/node.py::best_action_by_visits` | Max root visit count (Cowling's rule); key mapped back to indices of the real observation |
| 11 | Cleanup | `env/search_engine.py::search_end` | Engine recycles all search states of this decision |

## Where each design decision plugs in

- **ADR-001** (SO-ISMCTS, uniform determinization) → steps 4–6.
- **ADR-003** (heuristic evaluator, Phase 4) → will replace the
  uniform-random policy inside step 8 (H2's treatment arm).
- **ADR-004** (terminal reward) → step 9's $r_T$.
- **open-ideas / informed-determinization** → a smarter step 4.
- **open-ideas / oracle & PIMC baselines** → replace steps 4–5 with the
  true state (oracle) or independent per-determinization trees (PIMC).
- **Fallback validity flag** → step 2's exception path; every EXP
  reports the counter.

Keep this document in sync when the decision path changes — it is the
first thing to reread when the codebase stops fitting in your head.
