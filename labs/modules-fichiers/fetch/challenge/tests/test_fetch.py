"""Tests pytest pour le challenge module fetch.

Particularité : `fetch:` rapatrie des fichiers du managed node vers le
control node. Les tests vérifient des fichiers LOCAUX (côté
control node = la machine où tourne pytest), pas via testinfra ssh.
"""

import os
from pathlib import Path

import pytest

# Le dest fetch est relatif au cwd du playbook ansible-playbook
# (généralement le repo root ansible-training).
COLLECTED_DIR = Path(os.environ.get("ANSIBLE_TRAINING_ROOT", "/home/bob/Projets/ansible-training")) / "collected"


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
