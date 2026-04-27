"""Tests structure des dépendances entre rôles (lab 72)."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]


def test_webserver_meta_has_dependencies():
    """meta/main.yml du webserver déclare des dependencies."""
    meta = yaml.safe_load((LAB_ROOT / "roles/webserver/meta/main.yml").read_text())
    deps = meta.get("dependencies", [])
    assert len(deps) >= 2, "Au moins 2 dépendances attendues"


def test_dependencies_include_selinux_and_firewall():
    meta = yaml.safe_load((LAB_ROOT / "roles/webserver/meta/main.yml").read_text())
    deps_names = [d["role"] for d in meta["dependencies"]]
    assert "selinux_setup" in deps_names
    assert "firewall_setup" in deps_names


def test_dependent_roles_exist():
    """Les rôles dépendants existent dans le filesystem."""
    assert (LAB_ROOT / "roles/selinux_setup/tasks/main.yml").exists()
    assert (LAB_ROOT / "roles/firewall_setup/tasks/main.yml").exists()


def test_dependent_roles_have_tasks():
    """Chaque dépendance a au moins une tâche."""
    selinux = (LAB_ROOT / "roles/selinux_setup/tasks/main.yml").read_text()
    firewall = (LAB_ROOT / "roles/firewall_setup/tasks/main.yml").read_text()
    assert "name:" in selinux
    assert "name:" in firewall


def test_dependencies_pass_vars():
    """Les dependencies peuvent passer des vars."""
    meta = yaml.safe_load((LAB_ROOT / "roles/webserver/meta/main.yml").read_text())
    deps = meta["dependencies"]
    # Au moins une dépendance avec vars: explicite
    assert any("vars" in d for d in deps), (
        "Au moins une dépendance doit illustrer le passage de vars"
    )
