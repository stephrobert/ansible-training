"""Tests lab 78 — encrypt_string."""

import pytest
from conftest import lab_host, assert_idempotent


@pytest.fixture(scope="module")
def host():
    return lab_host("db1.lab")


def test_result_file_exists(host):
    f = host.file("/tmp/lab78-challenge.txt")
    assert f.exists


def test_admin_username_clair(host):
    """admin_username (en clair dans group_vars/all.yml) est bien lu."""
    content = host.file("/tmp/lab78-challenge.txt").content_string
    assert "lab78_admin" in content


def test_admin_password_decrypted(host):
    """admin_password (chiffré inline) commence bien par AdminS."""
    content = host.file("/tmp/lab78-challenge.txt").content_string
    assert "starts: Admin" in content


def test_password_length(host):
    """Longueur du password révélée dans le contenu (preuve déchiffrement)."""
    content = host.file("/tmp/lab78-challenge.txt").content_string
    assert "length:" in content


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
