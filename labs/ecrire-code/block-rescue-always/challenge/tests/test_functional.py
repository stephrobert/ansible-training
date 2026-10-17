"""Tests pytest+testinfra pour le challenge block-rescue-always.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_rescue_executed(host):
    f = host.file("/tmp/challenge-rescue.txt")
    assert f.exists, message(
        en="rescue: did not run. It only runs when a task INSIDE the block "
           "fails: if the block succeeds, rescue is skipped, and that is the "
           "whole point of the construct.",
        fr="rescue: n'a pas tourné. Il ne s'exécute que lorsqu'une tâche DU "
           "block échoue : si le block réussit, rescue est sauté, et c'est "
           "tout le principe de la construction.",
    )
    assert "rescue triggered" in f.content_string, message(
        en="The rescue file does not carry « rescue triggered ».",
        fr="Le fichier de rescue ne porte pas « rescue triggered ».",
    )


def test_always_executed(host):
    f = host.file("/tmp/challenge-always.txt")
    assert f.exists, message(
        en="always: did not run. It runs in every case, success or failure: "
           "if its file is missing, the section is probably indented inside "
           "the block instead of beside it.",
        fr="always: n'a pas tourné. Il s'exécute dans tous les cas, succès "
           "comme échec : si son fichier manque, c'est sans doute que la "
           "section est indentée dans le block au lieu d'être à côté.",
    )
    assert "always executed" in f.content_string, message(
        en="The always file does not carry « always executed ».",
        fr="Le fichier d'always ne porte pas « always executed ».",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
