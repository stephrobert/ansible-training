"""Tests pytest+testinfra pour le challenge lab 97 — migration rôle → collection."""

import yaml
from pathlib import Path

import pytest

from conftest import lab_host

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = LAB_DIR / "challenge"
COLL_ROOT = CHALLENGE_DIR / "ansible_collections" / "student" / "lab97_migrated"

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab97-migration.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_collection_initialized():
    assert COLL_ROOT.is_dir(), (
        f"{COLL_ROOT} absent — exécutez "
        "`ansible-galaxy collection init student.lab97_migrated --init-path ansible_collections/`."
    )


def test_runtime_yml_has_redirect():
    f = COLL_ROOT / "meta" / "runtime.yml"
    assert f.is_file(), "meta/runtime.yml absent"
    data = yaml.safe_load(f.read_text())
    routing = data.get("plugin_routing", {}).get("modules", {})
    assert "lab97_check" in routing, (
        "plugin_routing.modules.lab97_check absent dans meta/runtime.yml"
    )
    redirect = routing["lab97_check"].get("redirect", "")
    assert "lab97_check" in redirect and "lab97_migrated" in redirect, (
        f"redirect doit pointer vers student.lab97_migrated.lab97_check, vu : {redirect}"
    )


def test_runtime_yml_has_deprecation():
    data = yaml.safe_load((COLL_ROOT / "meta" / "runtime.yml").read_text())
    routing = data["plugin_routing"]["modules"]["lab97_check"]
    assert "deprecation" in routing, "deprecation: absent"
    assert "removal_version" in routing["deprecation"], (
        "removal_version absent dans deprecation"
    )


def test_module_python_migrated():
    f = COLL_ROOT / "plugins" / "modules" / "lab97_check.py"
    assert f.is_file(), (
        f"{f} absent — déplacez/créez le module dans plugins/modules/."
    )
    content = f.read_text()
    for section in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
        assert section in content, f"Section {section} absente du module"


def test_proof_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent — solution.yml a-t-elle tourné avec "
        "ANSIBLE_COLLECTIONS_PATH=challenge/ansible_collections ?"
    )


def test_proof_file_mode(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644


def test_proof_file_contains_new_fqcn_result(host):
    """Le fichier doit prouver que le module a tourné via le nouveau FQCN."""
    content = host.file(RESULT_FILE).content_string
    assert "lab97-migrated-OK" in content or "lab97-OK" in content, (
        f"Le fichier doit contenir la sortie msg du module migré, vu : {content[:200]}"
    )
