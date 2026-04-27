"""Tests structurels lab 88 — Debug d'un EE cassé.

Vérifie que la version corrigée de l'apprenant (challenge/execution-environment.yml)
respecte les bonnes pratiques 2026 : schéma v3, collections valides, deps existantes.
"""

import yaml
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE = LAB_DIR / "challenge"


def test_buggy_files_present_for_diagnosis():
    """Les fichiers buggy doivent être présents pour le diagnostic."""
    assert (LAB_DIR / "execution-environment-buggy.yml").is_file()
    assert (LAB_DIR / "requirements-buggy.yml").is_file()
    assert (LAB_DIR / "requirements-buggy.txt").is_file()


def test_buggy_yaml_lacks_version_3():
    """Le fichier buggy ne contient pas version: 3 (bug volontaire)."""
    data = yaml.safe_load((LAB_DIR / "execution-environment-buggy.yml").read_text())
    assert "version" not in data, "Le fichier buggy doit illustrer l'oubli de version: 3"


def test_corrected_yaml_has_version_3():
    """La version corrigée doit avoir version: 3."""
    data = yaml.safe_load((CHALLENGE / "execution-environment.yml").read_text())
    assert data.get("version") == 3


def test_corrected_requirements_uses_valid_collection():
    """La version corrigée n'utilise plus 'community.does-not-exist'."""
    data = yaml.safe_load((CHALLENGE / "requirements.yml").read_text())
    names = [c["name"] for c in data["collections"]]
    assert "community.does-not-exist" not in names
    assert all("." in name for name in names), "Toutes les collections doivent être FQCN"


def test_corrected_python_deps_use_real_version():
    """La version corrigée utilise une version PyPI existante (pas 9999.0.0)."""
    content = (CHALLENGE / "requirements.txt").read_text()
    assert "9999.0.0" not in content, "Version 9999.0.0 inexistante doit avoir été corrigée"


def test_corrected_has_bindep():
    """La version corrigée déclare aussi system deps."""
    assert (CHALLENGE / "bindep.txt").is_file()
    content = (CHALLENGE / "bindep.txt").read_text()
    assert "[platform:rpm]" in content
