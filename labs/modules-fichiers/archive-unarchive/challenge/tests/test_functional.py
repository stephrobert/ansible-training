"""Tests pytest+testinfra pour le challenge archive + unarchive.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"

SOURCE = "/opt/data-source"
ARCHIVE = "/opt/backup/data.tar.gz"
RESTAURE = "/opt/restored"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Preparation : 3 fichiers source ===

@pytest.mark.parametrize("n", [1, 2, 3])
def test_source_file_exists(host, n):
    f = host.file(f"{SOURCE}/file{n}.txt")
    assert f.exists, message(
        en=f"{SOURCE}/file{n}.txt is missing. The three source files are the "
           f"first step: create them with copy and content:, over a loop.",
        fr=f"{SOURCE}/file{n}.txt est absent. Les trois fichiers source sont "
           f"la première étape : crée-les avec copy et content:, sur une "
           f"boucle.",
    )
    assert f"Donnee {n}" in f.content_string, message(
        en=f"{SOURCE}/file{n}.txt does not hold « Donnee {n} ». In a loop, "
           f"the content depends on the item: content: \"Donnee {{{{ item }}}}\".",
        fr=f"{SOURCE}/file{n}.txt ne porte pas « Donnee {n} ». Dans une "
           f"boucle, le contenu dépend de l'item : "
           f"content: \"Donnee {{{{ item }}}}\".",
    )


# === Archive ===

def test_archive_exists(host):
    f = host.file(ARCHIVE)
    assert f.exists, message(
        en=f"{ARCHIVE} is missing. The archive module lives in "
           f"community.general, not in ansible.builtin: "
           f"community.general.archive with format: gz.",
        fr=f"{ARCHIVE} est absent. Le module archive vit dans "
           f"community.general, et non dans ansible.builtin : "
           f"community.general.archive avec format: gz.",
    )
    assert f.is_file, message(
        en=f"{ARCHIVE} is not an ordinary file.",
        fr=f"{ARCHIVE} n'est pas un fichier ordinaire.",
    )
    assert f.size > 100, message(
        en=f"{ARCHIVE} weighs only {f.size} bytes: it is empty. path: must "
           f"point at {SOURCE}, and the source files must exist BEFORE the "
           f"archive task runs.",
        fr=f"{ARCHIVE} ne pèse que {f.size} octets : il est vide. path: doit "
           f"viser {SOURCE}, et les fichiers source doivent exister AVANT que "
           f"la tâche d'archivage ne tourne.",
    )


# === Unarchive ===

def test_restored_dir_exists(host):
    assert host.file(RESTAURE).is_directory, message(
        en=f"{RESTAURE} is not a directory. unarchive does not create its "
           f"destination: create it first with ansible.builtin.file and "
           f"state: directory.",
        fr=f"{RESTAURE} n'est pas un répertoire. unarchive ne crée pas sa "
           f"destination : crée-la d'abord avec ansible.builtin.file et "
           f"state: directory.",
    )


def test_restored_file_content(host):
    f = host.file(f"{RESTAURE}/file1.txt")
    assert f.exists, message(
        en=f"{RESTAURE}/file1.txt is missing. The archive was not extracted, "
           f"or it was extracted with its full path: remote_src: true tells "
           f"unarchive the archive is already on the target, and creates: "
           f"keeps the task idempotent.",
        fr=f"{RESTAURE}/file1.txt est absent. L'archive n'a pas été extraite, "
           f"ou l'a été avec son chemin complet : remote_src: true dit à "
           f"unarchive que l'archive est déjà sur la cible, et creates: rend "
           f"la tâche idempotente.",
    )
    assert "Donnee 1" in f.content_string, message(
        en="The restored file does not hold « Donnee 1 »: the archive was "
           "built before the source files were written.",
        fr="Le fichier restauré ne porte pas « Donnee 1 » : l'archive a été "
           "construite avant que les fichiers source ne soient écrits.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
