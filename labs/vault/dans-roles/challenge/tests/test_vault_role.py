"""Tests lab 81 — vault dans rôle."""

import pytest
from conftest import lab_host


@pytest.fixture(scope="module")
def host():
    return lab_host("db1.lab")


def test_file_exists(host):
    f = host.file("/tmp/lab81-secured-app.txt")
    assert f.exists


def test_default_user(host):
    """secured_app_user (default clair)."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "user: appuser" in content


def test_override_port(host):
    """secured_app_port override par le play (9999)."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "port: 9999" in content


def test_db_password_decrypted(host):
    """vault_secured_app_db_password déchiffré et exposé via secured_app_db_password."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "RoleDBPas" in content


def test_api_token_decrypted(host):
    """vault_secured_app_api_token déchiffré."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "role_api_tok_lab81_xyz" in content
