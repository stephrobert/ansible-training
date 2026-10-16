"""Tests pytest+testinfra pour le challenge jinja2-base.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/etc/motd-challenge"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing. ansible.builtin.template renders the "
           f".j2 file onto the target.",
        fr=f"{RESULT_FILE} est absent. ansible.builtin.template rend le "
           f"fichier .j2 sur la cible.",
    )


def test_contains_hostname(host):
    content = host.file(RESULT_FILE).content_string
    assert "Bienvenue sur db1.lab" in content, message(
        en="The hostname does not appear. It comes from inventory_hostname, "
           "rendered by the template: writing db1.lab by hand would give the "
           "same file on every host.",
        fr="Le nom d'hôte n'apparaît pas. Il vient d'inventory_hostname, "
           "rendu par le template : écrire db1.lab à la main donnerait le "
           "même fichier sur tous les hôtes.",
    )


def test_if_branch_db(host):
    """Le {% if host_role == 'DB' %} doit s'évaluer vrai."""
    content = host.file(RESULT_FILE).content_string
    assert "Profil : DB" in content, message(
        en="« Profil : DB » is missing: the {% if %} did not take the "
           "expected branch. Check how host_role is set, and that the "
           "comparison is on the same case.",
        fr="« Profil : DB » manque : le {% if %} n'a pas pris la branche "
           "attendue. Vérifie comment host_role est posé, et que la "
           "comparaison porte sur la même casse.",
    )


@pytest.mark.parametrize("svc", ["postgresql", "chronyd", "firewalld"])
def test_for_loop_services(host, svc):
    content = host.file(RESULT_FILE).content_string
    assert f"- {svc}" in content, message(
        en=f"« - {svc} » is missing from the list. The {{% for %}} walks the "
           f"services variable: if one is missing, the list is incomplete or "
           f"the loop filters it out.",
        fr=f"« - {svc} » manque de la liste. Le {{% for %}} parcourt la "
           f"variable des services : s'il en manque un, la liste est "
           f"incomplète ou la boucle le filtre.",
    )


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

    assert not vides, message(
        en=f"{RESULT_FILE} contains {len(vides)} empty line(s), at lines "
        f"{vides}. Each Jinja tag leaves a line behind it: use "
        "`{%- ... -%}` to absorb them, or enable `trim_blocks: true` and "
        "`lstrip_blocks: true` on the template module.\n"
        f"Rendering obtained:\n{content}",
        fr=f"{RESULT_FILE} contient {len(vides)} ligne(s) vide(s), aux lignes "
        f"{vides}. Les balises Jinja laissent chacune une ligne derrière elles : "
        "utilisez `{%- ... -%}` pour les absorber, ou activez `trim_blocks: true` "
        "et `lstrip_blocks: true` sur le module template.\n"
        f"Rendu obtenu :\n{content}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
