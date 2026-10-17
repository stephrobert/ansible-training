"""Tests pytest+testinfra pour le challenge conditions-when.

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


def test_redhat_marker_exists(host):
    f = host.file("/tmp/cond-redhat.txt")
    assert f.exists, message(
        en="/tmp/cond-redhat.txt is missing. On AlmaLinux, ansible_os_family "
           "is RedHat: the condition should have fired. A fact used in a "
           "when: needs gather_facts, which a play can have turned off.",
        fr="/tmp/cond-redhat.txt est absent. Sur AlmaLinux, ansible_os_family "
           "vaut RedHat : la condition aurait dû se déclencher. Un fact "
           "utilisé dans un when: exige gather_facts, qu'un play peut avoir "
           "désactivé.",
    )
    assert "famille=redhat" in f.content_string, message(
        en="The file does not carry « famille=redhat ».",
        fr="Le fichier ne porte pas « famille=redhat ».",
    )


def test_alma9_marker_exists(host):
    f = host.file("/tmp/cond-alma9.txt")
    assert f.exists, message(
        en="/tmp/cond-alma9.txt is missing. This condition combines two "
           "facts, the distribution and its major version. Compare the "
           "version as an integer: \"9\" > \"10\" as strings.",
        fr="/tmp/cond-alma9.txt est absent. Cette condition combine deux "
           "facts, la distribution et sa version majeure. Compare la version "
           "en entier : \"9\" > \"10\" en chaînes de caractères.",
    )
    assert "os=AlmaLinux9" in f.content_string, message(
        en="The file does not carry « os=AlmaLinux9 ».",
        fr="Le fichier ne porte pas « os=AlmaLinux9 ».",
    )


def test_feature_marker_exists(host):
    """Avec --extra-vars enable_feature=true, le fichier est posé."""
    f = host.file("/tmp/cond-feature.txt")
    assert f.exists, message(
        en="With --extra-vars enable_feature=true, /tmp/cond-feature.txt must "
           "exist. Careful with the type: an extra-var arrives as the STRING "
           "\"true\", which | bool turns into a boolean.",
        fr="Avec --extra-vars enable_feature=true, /tmp/cond-feature.txt doit "
           "exister. Attention au type : une extra-var arrive en CHAÎNE "
           "\"true\", que | bool convertit en booléen.",
    )
    assert "feature=enabled" in f.content_string, message(
        en="The file does not carry « feature=enabled ».",
        fr="Le fichier ne porte pas « feature=enabled ».",
    )


def test_debian_marker_does_not_exist(host):
    """Sur AlmaLinux, ansible_os_family != Debian → fichier non posé."""
    f = host.file("/tmp/cond-debian.txt")
    assert not f.exists, message(
        en="On AlmaLinux the debian file must NOT exist. Its presence means "
           "the when: is missing, or that it tests a variable that is always "
           "true.",
        fr="Sur AlmaLinux, le fichier debian ne doit PAS exister. Sa présence "
           "signale un when: absent, ou qui teste une variable toujours vraie.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
