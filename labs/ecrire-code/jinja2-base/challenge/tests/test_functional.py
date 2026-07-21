"""Tests pytest+testinfra pour le challenge jinja2-base."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
RESULT_FILE = "/etc/motd-challenge"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_contains_hostname(host):
    content = host.file(RESULT_FILE).content_string
    assert "Bienvenue sur db1.lab" in content


def test_if_branch_db(host):
    """Le {% if host_role == 'DB' %} doit s'évaluer vrai."""
    content = host.file(RESULT_FILE).content_string
    assert "Profil : DB" in content


@pytest.mark.parametrize("svc", ["postgresql", "chronyd", "firewalld"])
def test_for_loop_services(host, svc):
    content = host.file(RESULT_FILE).content_string
    assert f"- {svc}" in content


def test_whitespace_control_aucune_ligne_vide(host):
    """Le rendu ne doit contenir aucune ligne vide : c'est l'objectif du lab.

    Les autres tests cherchent des sous-chaînes (`"Profil : DB" in content`) et
    resteraient verts avec un fichier truffé de lignes vides. Or le challenge
    demande explicitement le contrôle des espaces : sans `{%- ... -%}` (ou sans
    `trim_blocks`/`lstrip_blocks` sur le module), chaque `{% if %}`,
    `{% endif %}`, `{% for %}` et `{% endfor %}` laisse sa propre ligne vide
    dans la sortie. L'objectif annoncé n'était donc prouvé nulle part.

    C'est bien l'état du système qui tranche ici : on lit le fichier rendu, pas
    le template.
    """
    content = host.file(RESULT_FILE).content_string
    vides = [n for n, ligne in enumerate(content.splitlines(), 1) if not ligne.strip()]

    assert not vides, (
        f"{RESULT_FILE} contient {len(vides)} ligne(s) vide(s), aux lignes "
        f"{vides}. Les balises Jinja laissent chacune une ligne derrière elles : "
        "utilisez `{%- ... -%}` pour les absorber, ou activez `trim_blocks: true` "
        "et `lstrip_blocks: true` sur le module template.\n"
        f"Rendu obtenu :\n{content}"
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
