"""Tests lab 80 — playbook mixte clair + vault."""

import pytest
from conftest import lab_host


@pytest.fixture(scope="module")
def host():
    return lab_host("web1.lab")


def test_file_exists(host):
    f = host.file("/tmp/lab80-challenge.txt")
    assert f.exists


def test_clair_variables(host):
    """Variables main.yml (clair) bien lues."""
    content = host.file("/tmp/lab80-challenge.txt").content_string
    assert "Env: lab80" in content
    assert "Port: 80" in content


def test_vault_admin_token(host):
    """vault_admin_token (group_vars/all/vault.yml) déchiffré."""
    content = host.file("/tmp/lab80-challenge.txt").content_string
    assert "Admin token starts: lab80_admi" in content  # 10 premiers chars


def test_vault_web_secret(host):
    """vault_web_secret (group_vars/webservers/vault.yml) déchiffré."""
    content = host.file("/tmp/lab80-challenge.txt").content_string
    # 'web_secret_lab80_xyz' = 20 chars
    assert "Web secret length: 20" in content
