"""Tests pytest+testinfra pour le challenge lab 93 — découvrir collections."""

import re

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab93-collections.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné ?"
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, f"Mode attendu 0644, vu : {oct(f.mode)}"


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root"


def test_file_has_at_least_three_lines(host):
    """Le fichier liste au moins 3 collections."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) >= 3, (
        f"{RESULT_FILE} doit lister au moins 3 collections, vu : {len(lines)}.\n"
        f"Contenu : {content[:200]}"
    )


def test_file_contains_fqcn_format(host):
    """Au moins une ligne contient un FQCN namespace.collection."""
    content = host.file(RESULT_FILE).content_string
    fqcn_pattern = re.compile(r"^\S+\.\S+\s+\S+", re.MULTILINE)
    matches = fqcn_pattern.findall(content)
    assert len(matches) >= 1, (
        f"{RESULT_FILE} doit contenir au moins un FQCN type 'community.general 10.5.0', "
        f"vu : {content[:200]}"
    )
