"""Tests pytest+testinfra pour le challenge wait_for + pause.

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


def test_marker_file_exists(host):
    """Le fichier cree par la commande en arriere-plan (apres 3s) doit exister."""
    f = host.file("/tmp/lab-waitfor-marker.txt")
    assert f.exists, message(
        en="/tmp/lab-waitfor-marker.txt does not exist. The background "
           "command creates it after three seconds: launch it with async: "
           "and poll: 0, otherwise Ansible waits for it and there is nothing "
           "left to wait for.",
        fr="/tmp/lab-waitfor-marker.txt n'existe pas. La commande en arrière-"
           "plan le crée après trois secondes : lance-la avec async: et "
           "poll: 0, sinon Ansible l'attend et il n'y a plus rien à attendre.",
    )


def test_success_file_exists(host):
    """Le fichier de succes ecrit apres validation des conditions."""
    f = host.file("/tmp/lab-waitfor-success.txt")
    assert f.exists, message(
        en="/tmp/lab-waitfor-success.txt does not exist: the play stopped "
           "before this task, most likely on a wait_for that timed out.",
        fr="/tmp/lab-waitfor-success.txt n'existe pas : le play s'est arrêté "
           "avant cette tâche, le plus souvent sur un wait_for en dépassement "
           "de délai.",
    )
    assert f.mode == 0o644, message(
        en=f"/tmp/lab-waitfor-success.txt is {oct(f.mode)}, expected 0644.",
        fr=f"/tmp/lab-waitfor-success.txt est en {oct(f.mode)}, attendu 0644.",
    )


def test_success_content(host):
    content = host.file("/tmp/lab-waitfor-success.txt").content_string
    assert "Synchronisation OK" in content, message(
        en="The file does not carry « Synchronisation OK ».",
        fr="Le fichier ne porte pas « Synchronisation OK ».",
    )


def test_sshd_listening(host):
    """sshd doit ecouter sur 22/TCP (pre-requis Ansible)."""
    cmd = host.run("ss -tln | grep ':22 '")
    assert cmd.rc == 0, message(
        en="sshd is not listening on 22/TCP, which wait_for is supposed to "
           "check: a port that was never open makes the whole lab pointless.",
        fr="sshd n'écoute pas sur 22/TCP, ce que wait_for est censé "
           "contrôler : un port jamais ouvert vide le lab de son sens.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
