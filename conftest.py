"""
Configuration pytest globale pour le repo ansible-training.

Pose ANSIBLE_PRIVATE_KEY_FILE en variable d'environnement avec un chemin
absolu. Ainsi :

- Ansible (`ansible-playbook`) utilise cette clé via la résolution standard
  des variables ANSIBLE_*.
- testinfra (backend `ansible://`) hérite de la même variable et peut donc
  se connecter aux managed nodes sans avoir à interpoler `{{ inventory_dir }}`
  (testinfra ne résout pas Jinja2).

Ce conftest.py est découvert automatiquement par pytest depuis n'importe quel
sous-dossier — tous les tests `labs/**/challenge/tests/test_*.py` héritent.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()

os.environ.setdefault(
    "ANSIBLE_PRIVATE_KEY_FILE",
    str(REPO_ROOT / "ssh" / "id_ed25519"),
)
