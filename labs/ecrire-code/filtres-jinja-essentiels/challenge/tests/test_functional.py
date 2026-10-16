"""Tests pytest+testinfra pour le challenge filtres-jinja-essentiels.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/filtres-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing. The six lines go into a single file, "
           f"written with ansible.builtin.copy and content:, each line "
           f"rendering one filter.",
        fr=f"{RESULT_FILE} est absent. Les six lignes vont dans un seul "
           f"fichier, écrit avec ansible.builtin.copy et content:, chaque "
           f"ligne rendant un filtre.",
    )


def test_trim_lower(host):
    """raw_input | trim | lower."""
    content = host.file(RESULT_FILE).content_string
    assert "trimmed=hello world" in content, message(
        en="The « trimmed=hello world » line is missing or wrong. Two filters "
           "chained on raw_input: trim removes the surrounding spaces, lower "
           "lowercases. Order does not matter here, but both are needed.",
        fr="La ligne « trimmed=hello world » manque ou est fausse. Deux "
           "filtres enchaînés sur raw_input : trim retire les espaces autour, "
           "lower met en minuscules. L'ordre importe peu ici, les deux sont "
           "nécessaires.",
    )


def test_union_pkgs(host):
    """(pkgs_a + pkgs_b) | unique | sort | join(',')."""
    content = host.file(RESULT_FILE).content_string
    assert "union=memcached,nginx,postgres,redis" in content, message(
        en="The « union=... » line is missing or wrong. Expected "
           "memcached,nginx,postgres,redis: concatenate the two lists with +, "
           "then unique (redis appears twice), then sort, then join(','). "
           "Without sort the order comes from the lists, and differs.",
        fr="La ligne « union=... » manque ou est fausse. Attendu "
           "memcached,nginx,postgres,redis : concatène les deux listes avec +, "
           "puis unique (redis y est deux fois), puis sort, puis join(','). "
           "Sans sort, l'ordre est celui des listes, et il diffère.",
    )


def test_selectattr_map(host):
    """services | selectattr env=prod | map name | sort | join."""
    content = host.file(RESULT_FILE).content_string
    assert "prod_services=api,cache" in content, message(
        en="The « prod_services=api,cache » line is missing or wrong. "
           "selectattr('env', 'equalto', 'prod') filters the dicts, "
           "map(attribute='name') keeps only the name: selectattr alone "
           "returns whole dicts.",
        fr="La ligne « prod_services=api,cache » manque ou est fausse. "
           "selectattr('env', 'equalto', 'prod') filtre les dictionnaires, "
           "map(attribute='name') n'en garde que le nom : selectattr seul rend "
           "des dictionnaires entiers.",
    )


def test_combine_dicts(host):
    """base_config | combine(tls_overrides)."""
    content = host.file(RESULT_FILE).content_string
    # Le filtre combine surcharge port (80 → 443) et ajoute tls=True
    assert "app=api" in content, message(
        en="The merged line does not carry app=api. combine keeps the keys "
           "the overrides do not mention.",
        fr="La ligne fusionnée ne porte pas app=api. combine conserve les "
           "clés que la surcharge ne mentionne pas.",
    )
    assert "port=443" in content, message(
        en="The merged line does not carry port=443. That is the point of "
           "combine: tls_overrides wins over base_config, where port is 80. "
           "Seeing 80 means the two dicts were merged the other way round.",
        fr="La ligne fusionnée ne porte pas port=443. C'est tout l'intérêt de "
           "combine : tls_overrides l'emporte sur base_config, où port vaut "
           "80. Voir 80 signifie que les deux dictionnaires ont été fusionnés "
           "dans l'autre sens.",
    )
    assert "tls=True" in content, message(
        en="The merged line does not carry tls=True. combine also ADDS the "
           "keys that only the overrides have.",
        fr="La ligne fusionnée ne porte pas tls=True. combine AJOUTE aussi les "
           "clés que seule la surcharge possède.",
    )


def test_default_filter(host):
    """undefined_var | default('fallback-OK')."""
    content = host.file(RESULT_FILE).content_string
    assert "default_value=fallback-OK" in content, message(
        en="The « default_value=fallback-OK » line is missing. Apply default() "
           "to a variable that is NOT defined: on a defined one, the filter "
           "proves nothing.",
        fr="La ligne « default_value=fallback-OK » manque. Applique default() "
           "à une variable qui n'est PAS définie : sur une variable définie, "
           "le filtre ne prouve rien.",
    )


def test_to_yaml_inline(host):
    """{'hello': 'world'} | to_yaml | trim → la 6e ligne exigée par l'énoncé.

    to_yaml sérialise le mapping en flow style : `{hello: world}`.
    """
    content = host.file(RESULT_FILE).content_string
    assert "yaml_safe={hello: world}" in content, message(
        en="The « yaml_safe={hello: world} » line is missing or wrong. "
           "to_yaml serialises the mapping in flow style and adds a trailing "
           "newline: chain trim to remove it.",
        fr="La ligne « yaml_safe={hello: world} » manque ou est fausse. "
           "to_yaml sérialise le mapping en flow style et ajoute un retour à "
           "la ligne final : enchaîne trim pour le retirer.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
