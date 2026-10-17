"""Tests pytest+testinfra pour le challenge register-set-fact."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/system-id.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing: register captures a result, set_fact "
           f"turns it into a variable, and a last task writes it down.",
        fr=f"{RESULT_FILE} est absent : register capture un résultat, "
           f"set_fact en fait une variable, et une dernière tâche l'écrit.",
    )


def test_hostname_captured(host):
    """Le set_fact a bien capturé le hostname depuis register."""
    content = host.file(RESULT_FILE).content_string
    assert "system_id=db1:" in content, message(
        en=f"The file must contain 'system_id=db1:' (the short hostname). "
        f"Received: {content!r}",
        fr=f"Le fichier doit contenir 'system_id=db1:' (hostname court). "
        f"Reçu : {content!r}",
    )


def test_kernel_captured(host):
    """Le set_fact a bien capturé une signature kernel (.el9)."""
    content = host.file(RESULT_FILE).content_string
    assert ".el9" in content or ".x86_64" in content, message(
        en=f"The file must contain a kernel signature (.el9 or .x86_64). "
        f"Received: {content!r}",
        fr=f"Le fichier doit contenir une signature kernel (.el9 ou .x86_64). "
        f"Reçu : {content!r}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
