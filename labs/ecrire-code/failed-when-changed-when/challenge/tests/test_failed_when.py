"""Tests pytest+testinfra pour le challenge failed-when-changed-when."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/failed-when-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    """Le fichier existe = la 1ère tâche n'a pas planté (failed_when override)."""
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} doit exister. Si non, la 1ère tâche a marqué failed "
        f"alors que rc=1 devrait être OK avec failed_when."
    )


def test_rc_captured(host):
    content = host.file(RESULT_FILE).content_string
    assert "rc=1" in content


def test_changed_state(host):
    content = host.file(RESULT_FILE).content_string
    assert "ok=changed" in content
