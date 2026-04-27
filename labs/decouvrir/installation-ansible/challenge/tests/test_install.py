"""Tests pytest pour le challenge installation-ansible.

Ce lab est local au control node — pas d'invocation testinfra/SSH.
Le test lance le `solution.sh` écrit par l'apprenant et vérifie son code
retour, **et** que le script invoque réellement les vérifications attendues
(pas juste un `exit 0`).
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
SOLUTION = CHALLENGE_DIR / "solution.sh"


def test_solution_script_exists():
    assert SOLUTION.exists(), (
        f"Le script {SOLUTION} doit exister. Suivre challenge/README.md."
    )


def test_solution_script_executable():
    assert os.access(SOLUTION, os.X_OK), (
        f"{SOLUTION} doit être exécutable (chmod +x solution.sh)."
    )


def test_solution_script_uses_set_eu():
    """Le script utilise `set -euo pipefail` (bonne pratique bash)."""
    content = SOLUTION.read_text()
    assert re.search(r"set\s+-[euo]+", content), (
        "Le script doit débuter par `set -euo pipefail` (échec strict)."
    )


def test_solution_script_checks_ansible_version():
    """Le script vérifie la version d'ansible-core (≥ 2.18)."""
    content = SOLUTION.read_text()
    assert "ansible --version" in content or "ansible-core" in content, (
        "Le script doit invoquer `ansible --version` pour vérifier la version."
    )


def test_solution_script_checks_binaries():
    """Le script vérifie la présence des binaires (au moins 4 sur 8)."""
    content = SOLUTION.read_text()
    expected_binaries = [
        "ansible",
        "ansible-playbook",
        "ansible-doc",
        "ansible-galaxy",
        "ansible-vault",
        "ansible-inventory",
        "ansible-config",
        "ansible-console",
    ]
    found = sum(1 for b in expected_binaries if b in content)
    assert found >= 4, (
        f"Le script doit vérifier au moins 4 binaires Ansible standard. "
        f"Vu : {found} mention(s) parmi {expected_binaries}."
    )


def test_solution_script_checks_modules_count():
    """Le script compte les modules disponibles via ansible-doc."""
    content = SOLUTION.read_text()
    assert "ansible-doc" in content, (
        "Le script doit invoquer `ansible-doc` pour compter les modules."
    )


def test_solution_script_checks_collections():
    """Le script vérifie au moins une collection clé."""
    content = SOLUTION.read_text()
    expected_collections = ["ansible.posix", "community.general", "community.libvirt"]
    found = sum(1 for c in expected_collections if c in content)
    assert found >= 1, (
        f"Le script doit vérifier au moins une collection parmi "
        f"{expected_collections}."
    )


def test_solution_script_returns_zero():
    """solution.sh doit retourner exit 0 quand toutes les vérifications passent."""
    result = subprocess.run(
        [str(SOLUTION)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"solution.sh a échoué (exit {result.returncode}).\n"
        f"stdout : {result.stdout}\n"
        f"stderr : {result.stderr}"
    )
