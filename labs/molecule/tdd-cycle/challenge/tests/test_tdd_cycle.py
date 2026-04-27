"""Tests structure du cycle TDD avec Molecule (lab 64)."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"
ROLE_DIR = LAB_ROOT / "roles" / "users"


def test_role_users_structure_complete():
    """Le rôle users a toute la structure standard."""
    for d in ["tasks", "defaults", "meta"]:
        assert (ROLE_DIR / d).exists(), f"Dossier {d} manquant"


def test_role_users_argument_specs_present():
    """argument_specs.yml présent (TDD = validation des entrées AVANT execution)."""
    spec = ROLE_DIR / "meta/argument_specs.yml"
    assert spec.exists()
    content = yaml.safe_load(spec.read_text())
    assert "argument_specs" in content
    assert "main" in content["argument_specs"]
    assert "users_to_create" in content["argument_specs"]["main"]["options"]


def test_verify_yml_has_at_least_4_assertions():
    """Le verify.yml du TDD doit avoir plusieurs assertions (un test par feature)."""
    content = (MOLECULE_DIR / "verify.yml").read_text()
    assert content.count("ansible.builtin.assert") >= 4, (
        "Pattern TDD : un assertion par feature attendue"
    )


def test_converge_uses_users_role():
    content = (MOLECULE_DIR / "converge.yml").read_text()
    assert "users" in content


def test_converge_creates_alice_with_zsh():
    """converge.yml crée alice avec /bin/zsh (preuve que les vars existent)."""
    content = (MOLECULE_DIR / "converge.yml").read_text()
    assert "alice" in content
    assert "/bin/zsh" in content


def test_tasks_main_uses_loop():
    """tasks/main.yml itère sur users_to_create (pattern Loop)."""
    content = (ROLE_DIR / "tasks/main.yml").read_text()
    assert "loop:" in content or "with_items" in content
    assert "users_to_create" in content
