"""Tests pytest+testinfra pour le challenge module-template.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/etc/banner.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, message(
        en=f"{RESULT_FILE} is missing. ansible.builtin.template renders a "
           f".j2 file from the control node; its src: is relative to the "
           f"playbook's templates/ directory.",
        fr=f"{RESULT_FILE} est absent. ansible.builtin.template rend un "
           f"fichier .j2 depuis le control node ; son src: est relatif au "
           f"répertoire templates/ du playbook.",
    )


def test_motd_text(host):
    content = host.file(RESULT_FILE).content_string
    assert "Bienvenue !" in content, message(
        en="The banner does not carry « Bienvenue ! ». That text comes from a "
           "variable, rendered by the template, not written into it.",
        fr="Le banner ne porte pas « Bienvenue ! ». Ce texte vient d'une "
           "variable, rendue par le template, et non écrite dedans.",
    )


def test_generated_metadata(host):
    content = host.file(RESULT_FILE).content_string
    assert "Generated: 2026-04-25" in content, message(
        en="The « Generated: » line is missing or has the wrong date. The "
           "date is a variable of the play: a template that hardcodes it "
           "renders the same file forever.",
        fr="La ligne « Generated: » manque ou porte une autre date. La date "
           "est une variable du play : un template qui l'écrit en dur rend "
           "toujours le même fichier.",
    )


def test_owner_metadata(host):
    content = host.file(RESULT_FILE).content_string
    assert "Owner: ops-team" in content, message(
        en="The « Owner: ops-team » line is missing.",
        fr="La ligne « Owner: ops-team » manque.",
    )


def test_file_mode(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, message(
        en=f"{RESULT_FILE} is {oct(f.mode)}, expected 0644. template takes "
           f"mode: exactly like copy.",
        fr=f"{RESULT_FILE} est en {oct(f.mode)}, attendu 0644. template "
           f"accepte mode: exactement comme copy.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
