"""Tests pytest+testinfra pour le challenge boucles-loop.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/loop-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_user_alice_exists(host):
    assert host.user("chal_alice").exists, message(
        en="chal_alice was not created. The loop must walk the list of users "
           "and create those that are enabled.",
        fr="chal_alice n'a pas été créé. La boucle doit parcourir la liste "
           "des utilisateurs et créer ceux qui sont activés.",
    )


def test_user_charlie_exists(host):
    assert host.user("chal_charlie").exists, message(
        en="chal_charlie was not created, while chal_alice was: the loop "
           "stops too early, or the condition excludes him by mistake.",
        fr="chal_charlie n'a pas été créé alors que chal_alice l'a été : la "
           "boucle s'arrête trop tôt, ou la condition l'exclut à tort.",
    )


def test_user_bob_does_not_exist(host):
    """Bob a enabled: false → ne doit PAS être créé."""
    assert not host.user("chal_bob").exists, message(
        en="chal_bob must NOT be created: his entry carries enabled: false. "
           "The when: goes on the task and reads item.enabled, item by item.",
        fr="chal_bob ne doit PAS être créé : son entrée porte enabled: false. "
           "Le when: se pose sur la tâche et lit item.enabled, élément par "
           "élément.",
    )


def test_result_file_content(host):
    """Le fichier contient les users actifs triés par nom."""
    content = host.file(RESULT_FILE).content_string
    assert "chal_alice,chal_charlie" in content, message(
        en="The file does not carry « chal_alice,chal_charlie ». Filter the "
           "enabled users, keep their name, sort them, then join(','): "
           "without sort the order is the list's, and it differs.",
        fr="Le fichier ne porte pas « chal_alice,chal_charlie ». Filtre les "
           "utilisateurs activés, garde leur nom, trie, puis join(',') : sans "
           "sort, l'ordre est celui de la liste, et il diffère.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
