"""Tests pytest+testinfra pour le challenge lab 93 — découvrir collections."""

import re

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab93-collections.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, message(
        en=f"{RESULT_FILE} missing on {TARGET_HOST}: did solution.yml run?",
        fr=f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné ?",
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, message(
        en=f"Expected mode 0644, seen: {oct(f.mode)}",
        fr=f"Mode attendu 0644, vu : {oct(f.mode)}",
    )


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root", message(
        en=f"The file belongs to {f.user}, expected root.",
        fr=f"Le fichier appartient à {f.user}, attendu root.",
    )


def test_file_has_at_least_three_lines(host):
    """Le fichier liste au moins 3 collections."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) >= 3, message(
        en=f"{RESULT_FILE} must list at least 3 collections, seen: {len(lines)}.\n"
        f"Contents: {content[:200]}",
        fr=f"{RESULT_FILE} doit lister au moins 3 collections, vu : {len(lines)}.\n"
        f"Contenu : {content[:200]}",
    )


def test_file_contains_fqcn_format(host):
    """Au moins une ligne contient un FQCN namespace.collection."""
    content = host.file(RESULT_FILE).content_string
    fqcn_pattern = re.compile(r"^\S+\.\S+\s+\S+", re.MULTILINE)
    matches = fqcn_pattern.findall(content)
    assert len(matches) >= 1, message(
        en=f"{RESULT_FILE} must contain at least one FQCN such as 'community.general 10.5.0', "
        f"seen: {content[:200]}",
        fr=f"{RESULT_FILE} doit contenir au moins un FQCN type 'community.general 10.5.0', "
        f"vu : {content[:200]}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
