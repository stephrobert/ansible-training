"""Tests pytest+testinfra pour le challenge lab 94 — requirements.yml multi-sources."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab94-collections.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent — solution.yml a-t-elle installé puis déposé ?"
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root"


def test_file_lists_at_least_three_collections(host):
    """L'inventaire contient au moins 3 collections."""
    content = host.file(RESULT_FILE).content_string
    # Filtrer pour ne compter que les vraies lignes (pas les en-têtes)
    fqcn_lines = [
        line for line in content.splitlines()
        if line.strip()
        and "." in line.split()[0]
        and not line.startswith(("#", "Collection", "---", "Path"))
    ]
    assert len(fqcn_lines) >= 3, (
        f"{RESULT_FILE} doit lister au moins 3 collections au format FQCN, "
        f"vu : {len(fqcn_lines)}.\nContenu : {content[:300]}"
    )
