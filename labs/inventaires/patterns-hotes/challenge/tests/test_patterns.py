"""Tests pytest+testinfra pour le challenge patterns d'hôtes.

Ce test désactive la fixture auto-replay et lance lui-même les 3 commandes
ansible-playbook avec différents --limit pour vérifier les patterns.
"""

import os
import subprocess
from pathlib import Path

import pytest

from conftest import lab_host

REPO_ROOT = Path(__file__).resolve().parents[4]
LAB_ROOT = Path(__file__).resolve().parents[2]
INVENTORY = LAB_ROOT / "inventory" / "hosts.yml"
SOLUTION = LAB_ROOT / "challenge" / "solution.yml"

# Désactive le replay automatique du conftest.py — on lance nous-mêmes les
# commandes avec différents --limit, et on doit nettoyer les marqueurs
# entre les runs.
os.environ["LAB_NO_REPLAY"] = "1"


def _cleanup_markers():
    """Supprime les marqueurs sur tous les hôtes."""
    subprocess.run(
        [
            "ansible", "all",
            "-i", str(INVENTORY),
            "-m", "ansible.builtin.shell",
            "-a", "rm -f /tmp/lab56-mark-*.txt",
            "-b",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )


def _run_playbook(limit_pattern):
    """Lance le playbook avec un --limit donné."""
    result = subprocess.run(
        [
            "ansible-playbook",
            "-i", str(INVENTORY),
            str(SOLUTION),
            "--limit", limit_pattern,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Playbook échoué pour pattern '{limit_pattern}'\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


def _marker(host):
    """Helper: chemin du fichier marqueur attendu."""
    return f"/tmp/lab56-mark-{host}.txt"


def test_intersection_webservers_staging(web1, web2, db1):
    """Pattern 'webservers:&staging' → web1 uniquement (intersection)."""
    _cleanup_markers()
    _run_playbook("webservers:&staging")

    assert web1.file(_marker("web1.lab")).exists, "web1.lab doit avoir le marqueur"
    assert not web2.file(_marker("web2.lab")).exists, "web2.lab ne doit PAS avoir le marqueur (pas dans staging)"
    assert not db1.file(_marker("db1.lab")).exists, "db1.lab ne doit PAS avoir le marqueur (pas un webserver)"


def test_exclusion_webservers_minus_web1(web1, web2, db1):
    """Pattern 'webservers:!web1.lab' → web2 uniquement."""
    _cleanup_markers()
    _run_playbook("webservers:!web1.lab")

    assert not web1.file(_marker("web1.lab")).exists, "web1.lab doit être exclu"
    assert web2.file(_marker("web2.lab")).exists, "web2.lab doit avoir le marqueur"
    assert not db1.file(_marker("db1.lab")).exists, "db1.lab ne doit PAS avoir le marqueur (pas un webserver)"


def test_all_minus_staging(web1, web2, db1):
    """Pattern 'all:!staging' → web2 et db1 (web1 est dans staging, exclu)."""
    _cleanup_markers()
    _run_playbook("all:!staging")

    assert not web1.file(_marker("web1.lab")).exists, "web1.lab doit être exclu (dans staging)"
    assert web2.file(_marker("web2.lab")).exists, "web2.lab doit avoir le marqueur"
    assert db1.file(_marker("db1.lab")).exists, "db1.lab doit avoir le marqueur"


def test_cleanup_after(web1, web2, db1):
    """Cleanup final après les tests pour ne pas polluer."""
    _cleanup_markers()
    assert not web1.file(_marker("web1.lab")).exists
    assert not web2.file(_marker("web2.lab")).exists
    assert not db1.file(_marker("db1.lab")).exists
