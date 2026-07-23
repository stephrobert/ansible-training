"""Tests du lab 84 : premiers pas ansible-navigator + EE.

Les 4 fichiers sont livrés en squelette : ces tests ne passent que
lorsque l'apprenant les a complétés. En plus de la sémantique YAML, ils
exécutent réellement les outils disponibles sans conteneur : bash -n sur
le script, ansible-inventory sur l'inventaire, ansible-playbook
--syntax-check sur le playbook.

Le run complet dans l'EE (podman + pull de community-ansible-dev-tools) reste la
validation manuelle documentée dans le README : trop lourd et dépendant
du réseau pour ce harnais.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

LAB_DIR = Path(__file__).resolve().parents[2]


def test_setup_script_completed():
    script = LAB_DIR / "setup-ee.sh"
    assert script.is_file(), "setup-ee.sh manquant"
    assert script.stat().st_mode & 0o111, (
        "setup-ee.sh doit être exécutable (chmod +x)"
    )
    content = script.read_text()
    assert "???" not in content, (
        "setup-ee.sh contient encore des ??? : complétez le squelette"
    )
    assert "podman" in content, "Le script doit vérifier/installer podman"
    assert "ansible-navigator" in content, (
        "Le script doit vérifier/installer ansible-navigator"
    )
    assert "community-ansible-dev-tools" in content, (
        "Le script doit pré-tirer l'image community-ansible-dev-tools (podman pull)"
    )


def test_setup_script_valid_bash():
    """bash -n : le script doit être syntaxiquement valide."""
    result = subprocess.run(
        ["bash", "-n", str(LAB_DIR / "setup-ee.sh")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"bash -n rejette setup-ee.sh :\n{result.stderr}"
    )


def test_inventory_resolves_with_ansible_inventory():
    """Exécute réellement ansible-inventory sur votre inventaire."""
    result = subprocess.run(
        ["ansible-inventory", "-i", str(LAB_DIR / "inventory.yml"), "--list"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=LAB_DIR,
    )
    assert result.returncode == 0, (
        f"ansible-inventory rejette inventory.yml :\n{result.stderr}"
    )
    data = json.loads(result.stdout)
    hosts = data.get("_meta", {}).get("hostvars", {})
    for expected in ("web1.lab", "db1.lab"):
        assert expected in hosts, (
            f"{expected} absent de l'inventaire résolu : déclarez-le sous "
            "all.hosts avec son ansible_host"
        )
    assert hosts["web1.lab"].get("ansible_host"), (
        "web1.lab doit déclarer ansible_host (IP joignable depuis l'EE)"
    )


def test_ping_playbook_syntax_and_fqcn():
    """Exécute réellement ansible-playbook --syntax-check sur ping.yml."""
    content = (LAB_DIR / "ping.yml").read_text()
    assert "ansible.builtin.ping" in content, (
        "Le play doit utiliser le module ping en FQCN (ansible.builtin.ping)"
    )
    plays = yaml.safe_load(content)
    assert plays and plays[0].get("gather_facts") is False, (
        "gather_facts: false attendu : un ping n'a pas besoin des facts"
    )
    result = subprocess.run(
        [
            "ansible-playbook",
            "--syntax-check",
            "-i",
            str(LAB_DIR / "inventory.yml"),
            str(LAB_DIR / "ping.yml"),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=LAB_DIR,
    )
    assert result.returncode == 0, (
        f"ansible-playbook --syntax-check rejette ping.yml :\n{result.stderr}{result.stdout}"
    )


def test_navigator_config_semantics():
    cfg = yaml.safe_load((LAB_DIR / "ansible-navigator.yml").read_text())
    nav = cfg.get("ansible-navigator", {})
    ee = nav.get("execution-environment", {})
    assert "community-ansible-dev-tools" in str(ee.get("image", "")), (
        f"Image attendue : community-ansible-dev-tools (registre officiel), vu : {ee.get('image')!r}"
    )
    assert ee.get("container-engine") == "podman", (
        "container-engine: podman attendu (préconisation Red Hat, rootless)"
    )
    assert ee.get("pull", {}).get("policy") == "missing", (
        "pull.policy: missing attendu : tirer seulement si l'image est absente"
    )
    assert nav.get("mode") == "stdout", (
        "mode: stdout attendu : le mode interactive (TUI) bloque scripts et CI"
    )


def test_ansible_navigator_available():
    """L'outil enseigné doit répondre (sans lancer de conteneur)."""
    if shutil.which("ansible-navigator") is None:
        pytest.skip(
            "ansible-navigator absent du poste : pipx install "
            "ansible-navigator (c'est l'outil enseigné par ce lab)"
        )
    result = subprocess.run(
        ["ansible-navigator", "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"ansible-navigator --version échoue :\n{result.stderr}"
    )
