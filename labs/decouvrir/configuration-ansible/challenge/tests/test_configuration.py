"""Tests pytest+testinfra pour le challenge lab 03a — configuration Ansible."""

import configparser
import re
from pathlib import Path

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab03a-config.txt"

LAB_DIR = Path(__file__).resolve().parents[2]
ANSIBLE_CFG = LAB_DIR / "ansible.cfg"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_ansible_cfg_exists():
    assert ANSIBLE_CFG.is_file(), (
        f"{ANSIBLE_CFG} absent — créez le fichier en suivant les indices du challenge."
    )


def test_ansible_cfg_has_forks_20():
    cfg = configparser.ConfigParser()
    cfg.read(ANSIBLE_CFG)
    assert cfg.get("defaults", "forks", fallback=None) == "20", (
        "ansible.cfg [defaults] doit définir forks = 20"
    )


def test_ansible_cfg_has_stdout_callback_yaml():
    cfg = configparser.ConfigParser()
    cfg.read(ANSIBLE_CFG)
    assert cfg.get("defaults", "stdout_callback", fallback=None) == "yaml", (
        "ansible.cfg [defaults] doit définir stdout_callback = yaml"
    )


def test_ansible_cfg_has_profile_tasks_callback():
    cfg = configparser.ConfigParser()
    cfg.read(ANSIBLE_CFG)
    callbacks = cfg.get("defaults", "callbacks_enabled", fallback="")
    assert "ansible.posix.profile_tasks" in callbacks, (
        f"callbacks_enabled doit inclure ansible.posix.profile_tasks, vu : '{callbacks}'"
    )


def test_proof_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné "
        f"depuis le dossier labs/03a-... (avec ansible.cfg projet) ?"
    )


def test_proof_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, f"Mode attendu 0644, vu : {oct(f.mode)}"


def test_proof_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root"


def test_proof_file_has_at_least_three_lines(host):
    """La sortie de ansible-config dump --only-changed doit contenir ≥3 lignes."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) >= 3, (
        f"{RESULT_FILE} doit contenir ≥3 lignes non vides, vu : {len(lines)}.\n"
        f"Contenu : {content[:200]}"
    )


def test_proof_file_contains_config_keys(host):
    """Le contenu doit ressembler à une sortie ansible-config dump (clés FORKS, STDOUT_CALLBACK)."""
    content = host.file(RESULT_FILE).content_string
    assert re.search(r"DEFAULT_FORKS|FORKS\b", content), (
        "Le fichier doit contenir une référence à FORKS (sortie ansible-config dump)"
    )
