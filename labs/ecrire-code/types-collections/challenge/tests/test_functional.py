"""Tests pytest+testinfra pour le challenge types-collections (selectattr).

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/services-production.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_result_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing. One task writes the filtered list, "
           f"with copy and content:.",
        fr=f"{RESULT_FILE} est absent. Une tâche écrit la liste filtrée, avec "
           f"copy et content:.",
    )


def test_contains_api(host):
    assert "api:8080" in host.file(RESULT_FILE).content_string, message(
        en="« api:8080 » is missing. selectattr('tier', 'equalto', "
           "'production') keeps the production services, and the rendering "
           "pairs the name with the port.",
        fr="« api:8080 » manque. selectattr('tier', 'equalto', 'production') "
           "garde les services de production, et le rendu associe le nom au "
           "port.",
    )


def test_contains_cache(host):
    assert "cache:6379" in host.file(RESULT_FILE).content_string, message(
        en="« cache:6379 » is missing: the filter keeps only part of the "
           "production services.",
        fr="« cache:6379 » manque : le filtre ne retient qu'une partie des "
           "services de production.",
    )


def test_excludes_staging(host):
    """Les services tier=staging ne doivent PAS apparaître."""
    content = host.file(RESULT_FILE).content_string
    assert "web:80" not in content, message(
        en="web (tier=staging) must not appear in the production file. "
           "Without selectattr, the whole list is rendered: a filter that "
           "excludes nothing is not a filter.",
        fr="web (tier=staging) ne doit pas apparaître dans le fichier "
           "production. Sans selectattr, c'est toute la liste qui est rendue : "
           "un filtre qui n'exclut rien n'est pas un filtre.",
    )


def test_excludes_dev(host):
    """Les services tier=dev ne doivent PAS apparaître."""
    content = host.file(RESULT_FILE).content_string
    assert "dev-db:5432" not in content, message(
        en="dev-db (tier=dev) must not appear in the production file.",
        fr="dev-db (tier=dev) ne doit pas apparaître dans le fichier "
           "production.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
