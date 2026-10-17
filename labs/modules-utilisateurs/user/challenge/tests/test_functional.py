"""Tests pytest+testinfra pour le challenge module user.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"

GROUPE = "rhce-team"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Groupe rhce-team ===

def test_group_rhce_team_exists(host):
    assert host.group(GROUPE).exists, message(
        en=f"The {GROUPE} group does not exist. It comes first: the three "
           f"accounts take it as their primary group, and a user created "
           f"before its group gets a group of its own name instead.",
        fr=f"Le groupe {GROUPE} n'existe pas. Il vient en premier : les trois "
           f"comptes le prennent comme groupe primaire, et un utilisateur créé "
           f"avant son groupe en reçoit un à son propre nom.",
    )


# === alice ===

def test_alice_exists(host):
    u = host.user("alice")
    assert u.exists, message(
        en="The alice account does not exist. ansible.builtin.user with "
           "name: alice and state: present.",
        fr="Le compte alice n'existe pas. ansible.builtin.user avec "
           "name: alice et state: present.",
    )
    assert u.shell == "/bin/bash", message(
        en=f"alice's shell is {u.shell}, expected /bin/bash. The module's "
           f"default is the system's, which is not always bash: declare it.",
        fr=f"Le shell d'alice est {u.shell}, attendu /bin/bash. Le défaut du "
           f"module est celui du système, qui n'est pas toujours bash : "
           f"déclare-le.",
    )
    assert u.group == GROUPE, message(
        en=f"alice's primary group is {u.group}, expected {GROUPE}. That is "
           f"the group: option, singular, not groups:.",
        fr=f"Le groupe primaire d'alice est {u.group}, attendu {GROUPE}. C'est "
           f"l'option group:, au singulier, et non groups:.",
    )


def test_alice_in_wheel(host):
    groupes = host.user("alice").groups
    assert "wheel" in groupes, message(
        en=f"alice is not in wheel (she is in: {', '.join(groupes)}). That is "
           f"groups:, the secondary ones, with append: true so the primary "
           f"group is not replaced.",
        fr=f"alice n'est pas dans wheel (elle est dans : {', '.join(groupes)}). "
           f"C'est groups:, les secondaires, avec append: true pour ne pas "
           f"remplacer le groupe primaire.",
    )


# === bob ===

def test_bob_exists_with_uid_2001(host):
    u = host.user("bob")
    assert u.exists, message(
        en="The bob account does not exist.",
        fr="Le compte bob n'existe pas.",
    )
    assert u.uid == 2001, message(
        en=f"bob's UID is {u.uid}, expected 2001. Without uid:, the system "
           f"picks the next free one, which is never the same twice.",
        fr=f"L'UID de bob est {u.uid}, attendu 2001. Sans uid:, le système "
           f"prend le premier libre, qui n'est jamais le même deux fois.",
    )
    assert u.group == GROUPE, message(
        en=f"bob's primary group is {u.group}, expected {GROUPE}.",
        fr=f"Le groupe primaire de bob est {u.group}, attendu {GROUPE}.",
    )


# === deploy ===

def test_deploy_exists_with_uid_2000(host):
    u = host.user("deploy")
    assert u.exists, message(
        en="The deploy account does not exist.",
        fr="Le compte deploy n'existe pas.",
    )
    assert u.uid == 2000, message(
        en=f"deploy's UID is {u.uid}, expected 2000. An application account "
           f"gets a fixed UID so that file ownership survives a rebuild.",
        fr=f"L'UID de deploy est {u.uid}, attendu 2000. Un compte applicatif "
           f"porte un UID fixe, pour que la propriété des fichiers survive à "
           f"une reconstruction.",
    )
    assert u.group == GROUPE, message(
        en=f"deploy's primary group is {u.group}, expected {GROUPE}.",
        fr=f"Le groupe primaire de deploy est {u.group}, attendu {GROUPE}.",
    )


def test_deploy_home_in_opt(host):
    u = host.user("deploy")
    assert u.home == "/opt/deploy", message(
        en=f"deploy's home is {u.home}, expected /opt/deploy. The home: option "
           f"sets it; changing it after the fact also needs move_home: true.",
        fr=f"Le home de deploy est {u.home}, attendu /opt/deploy. C'est "
           f"l'option home: ; le changer après coup demande en plus "
           f"move_home: true.",
    )
    assert host.file("/opt/deploy").is_directory, message(
        en="/opt/deploy does not exist on disk. home: declares the path, "
           "create_home (true by default) creates it: check you did not turn "
           "it off.",
        fr="/opt/deploy n'existe pas sur le disque. home: déclare le chemin, "
           "create_home (vrai par défaut) le crée : vérifie que tu ne l'as pas "
           "désactivé.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
