"""Tests pytest+testinfra pour le challenge ignore-errors."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/ignore-after.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_play_continued(host):
    """Le fichier existe = le play a continué malgré l'erreur ignorée."""
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} n'existe pas — soit ignore_errors n'a pas été posé, "
        f"soit la tâche suivante a aussi planté."
    )
    assert "play continued" in f.content_string
