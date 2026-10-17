"""Tests pytest+testinfra pour le challenge lab 91 — idempotence."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_marker_file_exists(host):
    f = host.file("/tmp/lab91-marker")
    assert f.exists, message(
        en="/tmp/lab91-marker missing: task 1 (shell + creates:) did not run.",
        fr="/tmp/lab91-marker absent — la tâche 1 (shell + creates:) n'a pas tourné.",
    )


def test_config_file_has_max_connections_200(host):
    """lineinfile doit avoir posé exactement max_connections = 200 (avec regexp)."""
    f = host.file("/tmp/lab91-config.cfg")
    assert f.exists, message(
        en="/tmp/lab91-config.cfg missing: task 2 failed.",
        fr="/tmp/lab91-config.cfg absent — tâche 2 KO.",
    )
    content = f.content_string
    assert "max_connections = 200" in content, message(
        en=f"max_connections = 200 is missing. Contents: {content[:200]}",
        fr=f"max_connections = 200 absent. Contenu : {content[:200]}",
    )
    # Vérifier qu'on n'a PAS de duplication (ligne 100 + ligne 200)
    occurrences = content.count("max_connections")
    assert occurrences == 1, message(
        en=f"Duplication detected: lineinfile without a regexp? {occurrences} occurrences found.",
        fr=f"Duplication détectée — lineinfile sans regexp ? {occurrences} occurrences trouvées.",
    )


def test_curl_output_file_exists(host):
    f = host.file("/tmp/lab91-curl.txt")
    assert f.exists, message(
        en="/tmp/lab91-curl.txt missing: task 3 failed.",
        fr="/tmp/lab91-curl.txt absent — tâche 3 KO.",
    )


def test_curl_output_starts_with_curl(host):
    """La sortie capturée commence bien par 'curl'."""
    content = host.file("/tmp/lab91-curl.txt").content_string
    assert content.startswith("curl"), message(
        en=f"/tmp/lab91-curl.txt must start with 'curl', seen: {content[:80]}",
        fr=f"/tmp/lab91-curl.txt doit commencer par 'curl', vu : {content[:80]}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
