"""Tests pytest pour le challenge installation-ansible.

Ce lab est local au control node — pas d'invocation testinfra/SSH.
Le test lance le `solution.sh` écrit par l'apprenant et vérifie son code retour.
"""

import os
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


def test_solution_script_returns_zero():
    """solution.sh doit retourner exit 0 (toutes les vérifications passent)."""
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
