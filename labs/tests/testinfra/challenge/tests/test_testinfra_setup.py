"""Tests structure du setup testinfra (lab 66)."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"


def test_molecule_yml_uses_testinfra_verifier():
    """molecule.yml doit déclarer testinfra comme verifier."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert config["verifier"]["name"] == "testinfra"


def test_testinfra_tests_dir_exists():
    """Le dossier tests/ contenant les fichiers Python testinfra existe."""
    assert (MOLECULE_DIR / "tests").is_dir()


def test_testinfra_has_at_least_one_python_test():
    """Au moins un fichier test_*.py est présent."""
    test_files = list((MOLECULE_DIR / "tests").glob("test_*.py"))
    assert len(test_files) >= 1


def test_testinfra_uses_host_fixture():
    """Les tests utilisent l'API host (`def test_x(host):`)."""
    test_files = list((MOLECULE_DIR / "tests").glob("test_*.py"))
    found = False
    for f in test_files:
        content = f.read_text()
        if "def test_" in content and "host" in content:
            found = True
            break
    assert found, "Au moins un test doit utiliser la fixture 'host'"


def test_at_least_4_assertions():
    """Au moins 4 fonctions de test (richesse pédagogique)."""
    test_files = list((MOLECULE_DIR / "tests").glob("test_*.py"))
    total = sum(f.read_text().count("def test_") for f in test_files)
    assert total >= 4
