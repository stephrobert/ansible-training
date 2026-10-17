"""Tests pytest+testinfra pour le challenge tests-jinja.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/tests-jinja.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing. The four lines go into a single file, "
           f"written with copy and content:, each one rendering a Jinja test.",
        fr=f"{RESULT_FILE} est absent. Les quatre lignes vont dans un seul "
           f"fichier, écrit avec copy et content:, chacune rendant un test "
           f"Jinja.",
    )


@pytest.mark.parametrize("line", [
    "user_defined=yes",
    "config_mapping=yes",
    "ports_sequence=yes",
    "optional_undefined=yes",
])
def test_lines_present(host, line):
    content = host.file(RESULT_FILE).content_string
    assert line in content, message(
        en=f"The « {line} » line is missing or does not say yes. A Jinja test "
           f"is used with « is », never with a filter pipe: "
           f"{{% if var is defined %}}, {{% if var is mapping %}}, "
           f"{{% if var is sequence %}}, {{% if var is undefined %}}.",
        fr=f"La ligne « {line} » manque ou ne dit pas yes. Un test Jinja "
           f"s'emploie avec « is », jamais avec une barre de filtre : "
           f"{{% if var is defined %}}, {{% if var is mapping %}}, "
           f"{{% if var is sequence %}}, {{% if var is undefined %}}.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
