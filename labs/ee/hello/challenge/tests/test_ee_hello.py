"""Tests structurels lab 84 — Hello EE.

Le lab installe ansible-navigator + Podman et lance un premier playbook
dans un EE. On vérifie ici la structure du lab : fichiers présents,
syntaxes correctes. L'exécution Podman elle-même nécessite la présence
de Podman + ansible-navigator côté apprenant — non testée ici.
"""

import os
import shutil
import yaml
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]


def test_setup_script_exists():
    script = LAB_DIR / "setup-ee.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111, "setup-ee.sh doit être exécutable"


def test_setup_script_checks_podman_and_navigator():
    content = (LAB_DIR / "setup-ee.sh").read_text()
    assert "podman" in content
    assert "ansible-navigator" in content


def test_inventory_yaml_valid():
    inv = LAB_DIR / "inventory.yml"
    assert inv.is_file()
    data = yaml.safe_load(inv.read_text())
    assert "all" in data
    assert "hosts" in data["all"]
    assert "web1.lab" in data["all"]["hosts"]
    assert "db1.lab" in data["all"]["hosts"]


def test_ping_playbook_uses_fqcn():
    pb = LAB_DIR / "ping.yml"
    content = pb.read_text()
    assert "ansible.builtin.ping" in content


def test_navigator_config_uses_creator_ee():
    cfg = LAB_DIR / "ansible-navigator.yml"
    assert cfg.is_file()
    data = yaml.safe_load(cfg.read_text())
    image = data["ansible-navigator"]["execution-environment"]["image"]
    assert "creator-ee" in image, f"Image attendue creator-ee, vu : {image}"


def test_navigator_config_uses_podman():
    cfg = LAB_DIR / "ansible-navigator.yml"
    data = yaml.safe_load(cfg.read_text())
    engine = data["ansible-navigator"]["execution-environment"]["container-engine"]
    assert engine == "podman"
