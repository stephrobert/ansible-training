"""Tests pytest+testinfra pour le challenge module blockinfile.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
TARGET_FILE = "/etc/profile.d/aliases-rhce.sh"

DEBUT = "# BEGIN ALIASES RHCE"
FIN = "# END ALIASES RHCE"
ALIASES = ("alias ll='ls -lah'", "alias gs='git status'", "alias ports='ss -tulpn'")


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_aliases_file_exists(host):
    f = host.file(TARGET_FILE)
    assert f.exists, message(
        en=f"{TARGET_FILE} is missing. blockinfile does NOT create the file by "
           f"default: add create: true.",
        fr=f"{TARGET_FILE} est absent. blockinfile ne crée PAS le fichier par "
           f"défaut : ajoute create: true.",
    )
    assert f.mode == 0o644, message(
        en=f"{TARGET_FILE} is {oct(f.mode)}, expected 0644. A file under "
           f"/etc/profile.d is sourced by every login shell: it must be "
           f"readable by all, writable by root alone.",
        fr=f"{TARGET_FILE} est en {oct(f.mode)}, attendu 0644. Un fichier de "
           f"/etc/profile.d est lu par chaque shell de connexion : il doit "
           f"être lisible par tous, modifiable par root seul.",
    )


def test_aliases_content(host):
    content = host.file(TARGET_FILE).content_string
    for alias in ALIASES:
        assert alias in content, message(
            en=f"The block does not carry « {alias} ». The three aliases go in "
               f"a single block:, as a YAML block scalar (|), and not in three "
               f"separate tasks.",
            fr=f"Le bloc ne porte pas « {alias} ». Les trois aliases vont dans "
               f"un seul block:, en bloc YAML (|), et non en trois tâches.",
        )


def test_markers_present(host):
    content = host.file(TARGET_FILE).content_string
    assert DEBUT in content, message(
        en=f"The « {DEBUT} » marker is missing. marker: must contain {{mark}}, "
           f"which the module replaces with BEGIN then END: "
           f"marker: \"# {{mark}} ALIASES RHCE\".",
        fr=f"Le marker « {DEBUT} » manque. marker: doit contenir {{mark}}, que "
           f"le module remplace par BEGIN puis END : "
           f"marker: \"# {{mark}} ALIASES RHCE\".",
    )
    assert FIN in content, message(
        en=f"The « {FIN} » marker is missing. A single marker: produces both; "
           f"if only one shows, {{mark}} is probably absent from the format.",
        fr=f"Le marker « {FIN} » manque. Un seul marker: produit les deux ; "
           f"s'il n'y en a qu'un, c'est que {{mark}} manque au format.",
    )


def test_idempotence_one_block(host):
    """Le marker BEGIN ne doit apparaitre qu une seule fois."""
    content = host.file(TARGET_FILE).content_string
    debuts = content.count(DEBUT)
    assert debuts == 1, message(
        en=f"The block appears {debuts} times. That is what blockinfile is "
           f"for: with its markers it replaces its own block instead of "
           f"appending a copy. Duplication means the markers changed between "
           f"two runs, or that lineinfile was used instead.",
        fr=f"Le bloc apparaît {debuts} fois. C'est précisément ce que "
           f"blockinfile évite : grâce à ses markers, il remplace son propre "
           f"bloc au lieu d'en ajouter une copie. Une duplication signale des "
           f"markers qui changent d'un passage à l'autre, ou un lineinfile.",
    )
    assert content.count(FIN) == 1, message(
        en=f"The closing marker appears {content.count(FIN)} times, expected "
           f"once.",
        fr=f"Le marker de fin apparaît {content.count(FIN)} fois, attendu une "
           f"seule.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
