"""Tests pytest+testinfra pour le challenge lookups."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lookups-challenge.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_lookup_file_token(host):
    """lookup('file', ...) a bien lu le contenu du fichier source."""
    content = host.file(RESULT_FILE).content_string
    assert "token=MAGIC-TOKEN-RHCE-2026" in content, (
        f"Le contenu de files/api-token.txt n'a pas été récupéré. "
        f"Reçu : {content!r}"
    )


def test_lookup_env_home(host):
    """lookup('env', 'HOME') a retourné un chemin Unix."""
    content = host.file(RESULT_FILE).content_string
    assert "home=/" in content, (
        f"lookup('env', 'HOME') doit retourner un chemin commençant par /. "
        f"Reçu : {content!r}"
    )


def test_lookup_pipe_hostname(host):
    """lookup('pipe', 'hostname -s') a retourné une string non vide."""
    content = host.file(RESULT_FILE).content_string
    # Extraire la ligne host_local=...
    lines = [line for line in content.splitlines() if line.startswith("host_local=")]
    assert lines, f"Pas de ligne host_local= dans {content!r}"
    value = lines[0].split("=", 1)[1].strip()
    assert value and value != "(none)", (
        f"host_local doit être une string non vide. Reçu : {value!r}"
    )
