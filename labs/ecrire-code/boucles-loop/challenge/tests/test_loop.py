"""Tests pytest+testinfra pour le challenge boucles-loop."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/loop-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_user_alice_exists(host):
    assert host.user("chal_alice").exists


def test_user_charlie_exists(host):
    assert host.user("chal_charlie").exists


def test_user_bob_does_not_exist(host):
    """Bob a enabled: false → ne doit PAS être créé."""
    assert not host.user("chal_bob").exists, (
        "chal_bob ne doit PAS être créé (enabled: false)"
    )


def test_result_file_content(host):
    """Le fichier contient les users actifs triés par nom."""
    content = host.file(RESULT_FILE).content_string
    assert "chal_alice,chal_charlie" in content
