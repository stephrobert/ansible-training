"""Tests pytest+testinfra pour le challenge archive + unarchive."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Preparation : 3 fichiers source ===

@pytest.mark.parametrize("n", [1, 2, 3])
def test_source_file_exists(host, n):
    f = host.file(f"/opt/data-source/file{n}.txt")
    assert f.exists
    assert f"Donnee {n}" in f.content_string


# === Archive ===

def test_archive_exists(host):
    f = host.file("/opt/backup/data.tar.gz")
    assert f.exists
    assert f.is_file
    assert f.size > 100, "Archive trop petite — verifier que les fichiers source sont inclus"


# === Unarchive ===

def test_restored_dir_exists(host):
    assert host.file("/opt/restored").is_directory


def test_restored_file_content(host):
    f = host.file("/opt/restored/file1.txt")
    assert f.exists
    assert "Donnee 1" in f.content_string


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
