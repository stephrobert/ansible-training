"""Tests pytest+testinfra pour le challenge ignore-errors."""

import re

import pytest

from conftest import lab_host, assert_idempotent, lab_solution_text

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


def test_ignore_errors_est_le_mecanisme_employe():
    """`failed_when: false` produirait exactement le même état système.

    Le test ci-dessus prouve que le play a continué, pas COMMENT. Or
    `failed_when: false` donne le même fichier : la tâche est simplement
    déclarée réussie, et le play continue aussi. La différence est réelle mais
    invisible dans l'état final :

    - `ignore_errors: true` : la tâche ÉCHOUE, on poursuit, elle est comptée
      dans `ignored=` du récap ;
    - `failed_when: false` : la tâche est déclarée OK, rien n'est ignoré, et
      un vrai échec passerait désormais inaperçu.

    L'objectif du lab étant `ignore_errors`, et l'état du système ne permettant
    pas de trancher, la vérification porte ici sur le playbook lui-même.
    """
    solution = lab_solution_text(__file__)

    assert re.search(r"^\s*ignore_errors:\s*(true|yes)\b", solution, re.M | re.I), (
        "Aucun `ignore_errors:` dans votre playbook. Le fichier de résultat "
        "peut exister sans lui (par exemple avec `failed_when: false`), mais "
        "ce n'est pas le mécanisme que ce challenge demande : `ignore_errors` "
        "laisse la tâche en échec et poursuit le play, là où `failed_when: "
        "false` prétend qu'elle a réussi."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
