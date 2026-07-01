"""Bundle the current agent as a .tar.gz for Kaggle upload.

Kaggle expects a top-level `main.py` and `deck.csv` in the archive
(no nesting):

    tar -czvf submission.tar.gz main.py deck.csv

Runtime layout on Kaggle: files land at /kaggle_simulations/agent/.
Max bundle size: 197.7 MiB. See docs/engineering.md for the full contract.

Phase 0 first use — implements the bundle step for agents/random_agent.py.
"""
