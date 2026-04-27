"""
Tests pytest+testinfra pour le challenge "Tags" (tags always/configuration/never).
"""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
ALWAYS_FILE = "/tmp/challenge-tag-always.txt"
CONFIG_FILE = "/tmp/challenge-tag-configuration.txt"
RESET_FILE = "/tmp/challenge-tag-reset.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_always_file_exists(host):
    """La tâche taguée 'always' doit s'exécuter même avec --tags configuration."""
    f = host.file(ALWAYS_FILE)
    assert f.exists, (
        f"{ALWAYS_FILE} n'existe pas. La tâche taguée 'always' doit "
        f"s'exécuter quel que soit --tags."
    )


def test_configuration_file_exists(host):
    """La tâche taguée 'configuration' a tourné via --tags configuration."""
    f = host.file(CONFIG_FILE)
    assert f.exists, (
        f"{CONFIG_FILE} n'existe pas. La tâche taguée 'configuration' "
        f"doit s'exécuter avec --tags configuration."
    )


def test_reset_file_does_not_exist(host):
    """La tâche taguée 'never' ne doit PAS s'exécuter sans --tags reset."""
    f = host.file(RESET_FILE)
    assert not f.exists, (
        f"{RESET_FILE} existe — la tâche 'never' s'est exécutée alors "
        f"qu'elle ne devrait pas. Vérifier les tags."
    )
