"""Action utilities.

Legal actions live on `obs["select"]["option"]` (a list). The agent returns
integer indices into that list; length ∈ [minCount, maxCount], no duplicates.
The engine only ever surfaces legal options — no client-side filtering needed.
"""
