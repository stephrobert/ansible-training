"""Tests lab 77 — Introduction Vault."""

import pytest

from conftest import lab_host

TARGET = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET)


def test_result_file_exists(host):
    """Le fichier prouve que les 2 fichiers chiffrés ont été déchiffrés."""
    f = host.file("/tmp/lab77-challenge-result.txt")
    assert f.exists


def test_db_secrets_decrypted(host):
    """db_user du fichier chiffré db_secrets.yml apparaît dans le fichier final."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "db_user: app_admin" in content


def test_api_secrets_decrypted(host):
    """api_endpoint du fichier chiffré api_secrets.yml apparaît dans le fichier final."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "api_endpoint: https://api.example.com/v1" in content


def test_db_password_partial(host):
    """db_password (chiffré) commence bien par 'Challenge'."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "ChallengeDB2026" in content[:200] or "Challenge" in content


def test_api_key_present(host):
    """api_key (chiffré) est bien présent dans la sortie."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "challenge_api_xyz789" in content
