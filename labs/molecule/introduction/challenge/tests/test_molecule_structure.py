"""Tests de structure du scénario Molecule du lab 62.

Ces tests valident que les fichiers Molecule sont conformes — sans exécuter
'molecule test' (qui nécessite Docker/Podman et peut être long).
"""

from pathlib import Path

import pytest
import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"


def test_molecule_yml_exists():
    """Le fichier molecule.yml du scénario default existe."""
    assert (MOLECULE_DIR / "molecule.yml").exists()


def test_converge_yml_exists():
    """converge.yml présent — joue le rôle sur l'instance."""
    assert (MOLECULE_DIR / "converge.yml").exists()


def test_verify_yml_exists():
    """verify.yml présent — assertions post-converge."""
    assert (MOLECULE_DIR / "verify.yml").exists()


def test_molecule_yml_has_driver():
    """molecule.yml déclare un driver."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert "driver" in config
    assert config["driver"]["name"] in ("default", "delegated", "docker", "podman")


def test_molecule_yml_has_platforms():
    """molecule.yml déclare au moins 1 plateforme de test."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert "platforms" in config
    assert len(config["platforms"]) >= 1


def test_molecule_yml_has_verifier():
    """molecule.yml déclare un verifier."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert "verifier" in config
    assert config["verifier"]["name"] in ("ansible", "testinfra", "goss")


def test_converge_calls_webserver_role():
    """converge.yml appelle bien le rôle webserver."""
    content = (MOLECULE_DIR / "converge.yml").read_text()
    assert "webserver" in content


def test_verify_uses_assert():
    """verify.yml utilise au moins une tâche ansible.builtin.assert."""
    content = (MOLECULE_DIR / "verify.yml").read_text()
    assert "assert" in content
