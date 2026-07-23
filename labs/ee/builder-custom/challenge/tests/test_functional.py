"""Tests du lab 86 : EE custom avec ansible-builder.

Les 5 fichiers sont livrés en squelette : ces tests ne passent que
lorsque l'apprenant les a écrits. Si ansible-builder est présent sur le
poste, la définition est en plus soumise à `ansible-builder create`
(génération du Containerfile, sans build long ni pull d'image).
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

LAB_DIR = Path(__file__).resolve().parents[2]


def test_execution_environment_uses_v3():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    assert data.get("version") == 3, (
        "version: 3 attendu : sans schéma explicite, ansible-builder "
        "retombe sur un mode hérité qui ignore vos dépendances"
    )


def test_execution_environment_uses_community_minimal_base():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    base = str(data.get("images", {}).get("base_image", {}).get("name", ""))
    assert "community-ee-minimal" in base, (
        f"Base attendue : community-ee-minimal (registre officiel), vu : {base!r}"
    )


def test_execution_environment_pins_ansible_core():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    deps = data.get("dependencies", {})
    pin = str(deps.get("ansible_core", {}).get("package_pip", ""))
    assert pin.startswith("ansible-core=="), (
        "dependencies.ansible_core.package_pip doit épingler strictement "
        "(ansible-core==X.Y.Z) : une plage >= casse la reproductibilité"
    )


def test_execution_environment_wires_dependency_files():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    deps = data.get("dependencies", {})
    assert deps.get("galaxy") == "requirements.yml", (
        "dependencies.galaxy doit pointer requirements.yml"
    )
    assert deps.get("python") == "requirements.txt", (
        "dependencies.python doit pointer requirements.txt"
    )
    assert deps.get("system") == "bindep.txt", (
        "dependencies.system doit pointer bindep.txt"
    )


def test_requirements_yml_pins_versions():
    data = yaml.safe_load((LAB_DIR / "requirements.yml").read_text())
    collections = data.get("collections") or []
    assert collections, (
        "requirements.yml doit déclarer au moins une collection à embarquer"
    )
    for c in collections:
        assert isinstance(c, dict) and "version" in c, (
            f"Collection {c!r} sans version épinglée : pas de latest dans un "
            "EE de production"
        )


def test_requirements_txt_pins_versions():
    lines = [
        line.strip()
        for line in (LAB_DIR / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert lines, "requirements.txt doit déclarer au moins une dépendance Python"
    for line in lines:
        assert "==" in line, (
            f"Dépendance Python non épinglée : {line!r} (format paquet==X.Y.Z)"
        )


def test_bindep_uses_platform_rpm_profile():
    content = (LAB_DIR / "bindep.txt").read_text()
    assert "[platform:rpm]" in content, (
        "bindep.txt doit utiliser le profil [platform:rpm] (base UBI/RHEL)"
    )
    real = [
        line
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert real, "bindep.txt doit déclarer au moins un paquet système"


def test_build_script_completed():
    script = LAB_DIR / "build-ee.sh"
    assert script.stat().st_mode & 0o111, "build-ee.sh doit être exécutable"
    content = script.read_text()
    assert "???" not in content, "build-ee.sh contient encore des ???"
    assert "ansible-builder build" in content, (
        "build-ee.sh doit lancer ansible-builder build"
    )
    assert "--container-runtime podman" in content, (
        "Le runtime préconisé est podman (--container-runtime podman)"
    )
    result = subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"bash -n rejette build-ee.sh :\n{result.stderr}"


def test_ansible_cfg_disables_host_key_checking():
    content = (LAB_DIR / "configs" / "ansible.cfg").read_text()
    assert "host_key_checking = False" in content, (
        "configs/ansible.cfg (livré) doit garder host_key_checking = False"
    )


def test_definition_accepted_by_ansible_builder(tmp_path):
    """Exécute réellement ansible-builder sur votre définition.

    `ansible-builder create` génère le Containerfile sans builder l'image
    (pas de pull, pas de réseau) : il prouve que la définition est
    acceptée. Skip honnête si le binaire n'est pas installé.
    """
    if shutil.which("ansible-builder") is None:
        pytest.skip(
            "ansible-builder absent du poste : pipx install ansible-builder "
            "pour valider ce point (le build complet reste manuel)"
        )
    result = subprocess.run(
        [
            "ansible-builder",
            "create",
            "--file",
            "execution-environment.yml",
            "--context",
            str(tmp_path / "context"),
        ],
        cwd=LAB_DIR,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"ansible-builder refuse votre définition :\n{result.stdout}{result.stderr}"
    )
    assert (tmp_path / "context" / "Containerfile").is_file(), (
        "Containerfile non généré : la définition n'est pas exploitable"
    )
