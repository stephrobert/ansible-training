"""dsoxlab — CLI de suivi d'avancement des labs pédagogiques.

Stocke les runs pytest dans une SQLite locale
(`~/.local/share/dsoxlab/progress.db`) et affiche un dashboard de
progression par section/lab. Embarqué dans ce repo en attendant le
projet `dsoxlab` standalone.

Entry points :
- `python -m dsoxlab`  → CLI
- `bin/dsoxlab`         → wrapper bash (à symlinker dans ~/.local/bin/)
- Hook pytest auto chargé via conftest.py
"""

__version__ = "0.1.0"
