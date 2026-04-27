"""Tests pytest+testinfra pour le challenge precedence-variables."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/precedence-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_extra_vars_wins(host):
    """--extra-vars (niveau 22) écrase tous les autres niveaux."""
    content = host.file(RESULT_FILE).content_string
    assert "winner=extra_vars_wins" in content, (
        f"--extra-vars doit gagner. Reçu : {content!r}"
    )


def test_play_vars_does_not_win(host):
    content = host.file(RESULT_FILE).content_string
    assert "winner=play_vars" not in content, (
        "vars: du play ne doit PAS gagner (extra-vars passé en CLI)"
    )


def test_vars_files_does_not_win(host):
    content = host.file(RESULT_FILE).content_string
    assert "winner=vars_files" not in content, (
        "vars_files: ne doit PAS gagner (extra-vars passé en CLI)"
    )
