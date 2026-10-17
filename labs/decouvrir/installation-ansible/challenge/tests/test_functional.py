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

from conftest import message

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
SOLUTION = CHALLENGE_DIR / "solution.sh"


def test_solution_script_exists():
    assert SOLUTION.exists(), message(
        en=f"The {SOLUTION} script must exist. Follow challenge/README.md.",
        fr=f"Le script {SOLUTION} doit exister. Suivre challenge/README.md.",
    )


def test_solution_script_executable():
    assert os.access(SOLUTION, os.X_OK), message(
        en=f"{SOLUTION} must be executable (chmod +x solution.sh).",
        fr=f"{SOLUTION} doit être exécutable (chmod +x solution.sh).",
    )


def test_solution_script_uses_set_eu():
    """Le script utilise `set -euo pipefail` (bonne pratique bash)."""
    content = SOLUTION.read_text()
    assert re.search(r"set\s+-[euo]+", content), message(
        en="The script must start with `set -euo pipefail` (strict failure).",
        fr="Le script doit débuter par `set -euo pipefail` (échec strict).",
    )


def test_solution_script_checks_ansible_version():
    """Le script vérifie la version d'ansible-core (≥ 2.18)."""
    content = SOLUTION.read_text()
    assert "ansible --version" in content or "ansible-core" in content, message(
        en="The script must invoke `ansible --version` to check the version.",
        fr="Le script doit invoquer `ansible --version` pour vérifier la version.",
    )


def test_solution_script_checks_binaries():
    """Le script vérifie les binaires standard annoncés (8 au total).

    L'énoncé annonce 8 binaires : les binaires distinctifs d'ansible-core
    toujours présents, plus un 8e outil (ansible-console côté core, ou
    ansible-lint que ce lab installe aussi). Le test se contentait de 4 : un
    apprenant pouvait en omettre la moitié sans être détecté.
    """
    content = SOLUTION.read_text()
    core_binaries = [
        "ansible-playbook",
        "ansible-doc",
        "ansible-galaxy",
        "ansible-vault",
        "ansible-inventory",
        "ansible-config",
    ]
    missing = [b for b in core_binaries if b not in content]
    assert not missing, message(
        en=f"The script must check every core ansible-core binary. "
        f"Missing: {missing}.",
        fr=f"Le script doit vérifier tous les binaires cœur d'ansible-core. "
        f"Manquant(s) : {missing}.",
    )
    assert "ansible-console" in content or "ansible-lint" in content, message(
        en="The script must also check an eighth tool: ansible-console "
        "(ansible-core) or ansible-lint (installed by this lab).",
        fr="Le script doit aussi vérifier un 8e outil : ansible-console "
        "(ansible-core) ou ansible-lint (installé par ce lab).",
    )


def test_solution_script_checks_modules_count():
    """Le script compte les modules disponibles via ansible-doc."""
    content = SOLUTION.read_text()
    assert "ansible-doc" in content, message(
        en="The script must invoke `ansible-doc` to count the modules.",
        fr="Le script doit invoquer `ansible-doc` pour compter les modules.",
    )


def test_solution_script_checks_collections():
    """Le script vérifie au moins une collection clé."""
    content = SOLUTION.read_text()
    expected_collections = ["ansible.posix", "community.general", "community.libvirt"]
    missing = [c for c in expected_collections if c not in content]
    assert not missing, message(
        en=f"The script must check the 3 key collections it announces. "
        f"Missing: {missing}.",
        fr=f"Le script doit vérifier les 3 collections clés annoncées. "
        f"Manquant(s) : {missing}.",
    )


def test_solution_script_returns_zero():
    """solution.sh doit retourner exit 0 quand toutes les vérifications passent."""
    result = subprocess.run(
        [str(SOLUTION)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, message(
        en=f"solution.sh failed (exit {result.returncode}).\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}",
        fr=f"solution.sh a échoué (exit {result.returncode}).\n"
        f"stdout : {result.stdout}\n"
        f"stderr : {result.stderr}",
    )
