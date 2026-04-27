"""Tests structure config Molecule enrichie."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"


def test_requirements_yml_present():
    assert (MOLECULE_DIR / "requirements.yml").exists()


def test_prepare_yml_present():
    assert (MOLECULE_DIR / "prepare.yml").exists()


def test_molecule_yml_has_inventory_host_vars():
    """molecule.yml configure host_vars pour override les variables du rôle."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert "provisioner" in config
    assert "inventory" in config["provisioner"]
    assert "host_vars" in config["provisioner"]["inventory"]


def test_molecule_yml_has_test_sequence():
    """test_sequence personnalisée déclarée dans molecule.yml."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert "scenario" in config
    seq = config["scenario"].get("test_sequence", [])
    assert "idempotence" in seq, "idempotence doit être dans test_sequence"
    assert "verify" in seq


def test_molecule_yml_has_callback_options():
    """Configuration callback Ansible (profile_tasks, timer)."""
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    callbacks = config["provisioner"]["config_options"]["defaults"].get("callback_enabled", "")
    assert "profile_tasks" in callbacks
