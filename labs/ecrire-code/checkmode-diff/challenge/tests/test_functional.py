"""Tests pytest+testinfra pour le challenge checkmode-diff."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
LAB_FILE = "/etc/lab-checkmode.txt"
EXPECTED_CONTENT = "Lab checkmode validé"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists_after_real_run(host):
    """Le fichier doit exister APRÈS un ansible-playbook --diff (sans --check)."""
    f = host.file(LAB_FILE)
    assert f.exists, (
        f"{LAB_FILE} n'existe pas. Avez-vous lancé l'exécution réelle "
        f"(sans --check) ?"
    )


def test_file_content(host):
    """Le contenu doit correspondre à la consigne."""
    f = host.file(LAB_FILE)
    assert EXPECTED_CONTENT in f.content_string, (
        f"{LAB_FILE} ne contient pas '{EXPECTED_CONTENT}'."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
