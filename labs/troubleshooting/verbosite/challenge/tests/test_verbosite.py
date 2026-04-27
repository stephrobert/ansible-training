"""Tests pytest+testinfra pour le challenge lab 89 — profile_tasks."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab89-profile.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné "
        f"avec ANSIBLE_CONFIG=labs/89-…/ansible.cfg ?"
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, (
        f"{RESULT_FILE} doit avoir mode 0644, vu : {oct(f.mode)}"
    )


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root", (
        f"{RESULT_FILE} doit appartenir à root, vu : {f.user}"
    )


def test_file_has_three_non_empty_lines(host):
    """Le fichier contient EXACTEMENT 3 lignes non vides (les 3 noms de tâches)."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) == 3, (
        f"{RESULT_FILE} doit contenir exactement 3 lignes non vides "
        f"(les 3 noms de tâches), vu : {len(lines)} ligne(s).\n"
        f"Contenu : {content[:200]}"
    )
