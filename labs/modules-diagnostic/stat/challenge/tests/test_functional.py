"""Tests pytest+testinfra pour le challenge module stat.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import re

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RAPPORT = "/tmp/lab-stat-report.txt"

#: Un SHA256 rendu en hexadécimal, quelle que soit la mise en forme autour.
SHA256 = re.compile(r"[a-f0-9]{64}")


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_report_exists(host):
    f = host.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. stat collects, it writes nothing: a last "
           f"task has to assemble the registered results, with "
           f"ansible.builtin.copy and content:.",
        fr=f"{RAPPORT} est absent. stat collecte, il n'écrit rien : c'est une "
           f"dernière tâche qui assemble les résultats enregistrés, avec "
           f"ansible.builtin.copy et content:.",
    )
    assert f.is_file, message(
        en=f"{RAPPORT} exists but is not an ordinary file.",
        fr=f"{RAPPORT} existe mais n'est pas un fichier ordinaire.",
    )
    assert f.mode == 0o644, message(
        en=f"{RAPPORT} is {oct(f.mode)}, expected 0644.",
        fr=f"{RAPPORT} est en {oct(f.mode)}, attendu 0644.",
    )


def test_report_contains_passwd(host):
    content = host.file(RAPPORT).content_string
    assert "/etc/passwd" in content, message(
        en="The report does not mention /etc/passwd. Write the path itself in "
           "the text: a report that only carries values says nothing about "
           "what they describe.",
        fr="Le rapport ne mentionne pas /etc/passwd. Écris le chemin dans le "
           "texte : un rapport qui ne porte que des valeurs ne dit pas de quoi "
           "elles parlent.",
    )
    assert "exists: True" in content, message(
        en="The report does not carry « exists: True ». That is "
           "passwd_stat.stat.exists, rendered by Jinja in the content:.",
        fr="Le rapport ne porte pas « exists: True ». C'est "
           "passwd_stat.stat.exists, rendu par Jinja dans le content:.",
    )
    assert SHA256.search(content), message(
        en="No SHA256 checksum in the report. stat computes none by default: "
           "ask for it with get_checksum: true and "
           "checksum_algorithm: sha256, then render stat.checksum.",
        fr="Aucun checksum SHA256 dans le rapport. stat n'en calcule pas par "
           "défaut : demande-le avec get_checksum: true et "
           "checksum_algorithm: sha256, puis rends stat.checksum.",
    )


def test_report_contains_shadow_uid_0(host):
    content = host.file(RAPPORT).content_string
    assert "/etc/shadow" in content, message(
        en="The report does not mention /etc/shadow.",
        fr="Le rapport ne mentionne pas /etc/shadow.",
    )
    assert "uid: 0" in content, message(
        en="The report does not carry « uid: 0 » for /etc/shadow. That is "
           "stat.uid, the numeric owner: on this file it must be root, and "
           "that is the point of the check.",
        fr="Le rapport ne porte pas « uid: 0 » pour /etc/shadow. C'est "
           "stat.uid, le propriétaire numérique : sur ce fichier il doit être "
           "root, et c'est tout l'intérêt du contrôle.",
    )


def test_report_contains_sudoers(host):
    content = host.file(RAPPORT).content_string
    assert "/etc/sudoers" in content, message(
        en="The report does not mention /etc/sudoers. Three stat tasks, three "
           "entries: the third is missing.",
        fr="Le rapport ne mentionne pas /etc/sudoers. Trois tâches stat, trois "
           "entrées : la troisième manque.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
