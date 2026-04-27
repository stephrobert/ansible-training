"""Tests structurels lab 86 — EE custom avec ansible-builder."""

import yaml
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]


def test_execution_environment_yaml_exists():
    f = LAB_DIR / "execution-environment.yml"
    assert f.is_file()
    data = yaml.safe_load(f.read_text())
    assert data["version"] == 3, "Schéma v3 obligatoire en 2026"


def test_execution_environment_uses_community_minimal_base():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    base = data["images"]["base_image"]["name"]
    assert "community-ee-minimal" in base, f"Base attendue community-ee-minimal, vu : {base}"


def test_execution_environment_pins_ansible_core():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    pin = data["dependencies"]["ansible_core"]["package_pip"]
    assert "==" in pin, "ansible-core doit être pinné avec =="


def test_requirements_yml_pins_versions():
    data = yaml.safe_load((LAB_DIR / "requirements.yml").read_text())
    for c in data["collections"]:
        assert "version" in c, f"Collection {c['name']} sans version pinnée"


def test_requirements_txt_pins_versions():
    content = (LAB_DIR / "requirements.txt").read_text()
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            assert "==" in line, f"Dépendance Python non pinnée : {line}"


def test_bindep_uses_platform_rpm_profile():
    content = (LAB_DIR / "bindep.txt").read_text()
    assert "[platform:rpm]" in content


def test_build_script_uses_podman_runtime():
    content = (LAB_DIR / "build-ee.sh").read_text()
    assert "--container-runtime podman" in content


def test_build_script_uses_ansible_builder():
    content = (LAB_DIR / "build-ee.sh").read_text()
    assert "ansible-builder build" in content


def test_ansible_cfg_disables_host_key_checking():
    content = (LAB_DIR / "configs" / "ansible.cfg").read_text()
    assert "host_key_checking = False" in content
