"""Observation utilities.

The `cabt` env returns observations as plain dicts (no wrapper class in the
current SDK — `cg.api` from the sample submission does not exist). Fields used
downstream:

- obs["select"]                    — None on the deck-submission turn
- obs["select"]["option"]          — list of legal options
- obs["select"]["minCount"]        — min items to return
- obs["select"]["maxCount"]        — max items to return
- obs["logs"]                      — accumulated game log
- obs["current"]                   — turn context (yourIndex, result, ...)

Phase 1 defines encoding of these fields into search-friendly shapes.
"""
