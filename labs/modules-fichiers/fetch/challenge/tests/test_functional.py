"""Tests pytest pour le challenge module fetch.

Particularité : `fetch:` rapatrie des fichiers du managed node vers le
control node. Les tests vérifient des fichiers LOCAUX (côté
control node = la machine où tourne pytest), pas via testinfra ssh.
"""

import os
from pathlib import Path

from conftest import assert_idempotent


# Le dest fetch est relatif au cwd du playbook ansible-playbook, soit la racine
# du dépôt. On la déduit de l'emplacement de ce fichier
# (labs/<section>/<lab>/challenge/tests/) plutôt que de la coder en dur :
# le dépôt se clone où l'apprenant veut. ANSIBLE_TRAINING_ROOT reste
# prioritaire pour les cas particuliers.
_REPO_ROOT = Path(__file__).resolve().parents[5]
COLLECTED_DIR = Path(os.environ.get("ANSIBLE_TRAINING_ROOT", _REPO_ROOT)) / "collected"


def test_collected_dir_exists():
    assert COLLECTED_DIR.is_dir(), f"Repertoire {COLLECTED_DIR} introuvable — verifier le cwd du run ansible-playbook"


def test_web1_os_release_fetched():
    f = COLLECTED_DIR / "web1-os-release.txt"
    assert f.exists()
    assert "NAME=" in f.read_text()


def test_db1_os_release_fetched():
    f = COLLECTED_DIR / "db1-os-release.txt"
    assert f.exists()
    assert "NAME=" in f.read_text()


def test_web1_tag_content():
    f = COLLECTED_DIR / "web1-tag.txt"
    assert f.exists()
    assert "RHCE-LAB-2026" in f.read_text()


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Ce lab n'avait aucun contrôle d'idempotence, et sans la justification que
    portent les trois labs légitimement exemptés (touch, async, changed_when).
    C'était un oubli : `fetch` compare les sommes de contrôle et ne rapatrie
    pas un fichier identique, la solution converge (mesuré).
    """
    assert_idempotent(__file__)
