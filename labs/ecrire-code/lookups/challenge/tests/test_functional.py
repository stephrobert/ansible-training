"""Tests pytest+testinfra pour le challenge lookups."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lookups-challenge.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing: the play writes the results of the "
           f"three lookups into a single file.",
        fr=f"{RESULT_FILE} est absent : le play écrit le résultat des trois "
           f"lookups dans un seul fichier.",
    )


def test_lookup_file_token(host):
    """lookup('file', ...) a bien lu le contenu du fichier source."""
    content = host.file(RESULT_FILE).content_string
    assert "token=MAGIC-TOKEN-RHCE-2026" in content, message(
        en=f"The content of files/api-token.txt was not retrieved. "
        f"Received: {content!r}",
        fr=f"Le contenu de files/api-token.txt n'a pas été récupéré. "
        f"Reçu : {content!r}",
    )


def test_lookup_env_home(host):
    """lookup('env', 'HOME') a retourné un chemin Unix."""
    content = host.file(RESULT_FILE).content_string
    assert "home=/" in content, message(
        en=f"lookup('env', 'HOME') must return a path starting with /. "
        f"Received: {content!r}",
        fr=f"lookup('env', 'HOME') doit retourner un chemin commençant par /. "
        f"Reçu : {content!r}",
    )


def test_lookup_pipe_hostname(host):
    """lookup('pipe', 'hostname -s') a retourné une string non vide."""
    content = host.file(RESULT_FILE).content_string
    # Extraire la ligne host_local=...
    lines = [line for line in content.splitlines() if line.startswith("host_local=")]
    assert lines, message(
        en=f"No host_local= line in {content!r}",
        fr=f"Pas de ligne host_local= dans {content!r}",
    )
    value = lines[0].split("=", 1)[1].strip()
    assert value and value != "(none)", message(
        en=f"host_local must be a non-empty string. Received: {value!r}",
        fr=f"host_local doit être une string non vide. Reçu : {value!r}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
