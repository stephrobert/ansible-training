"""Tests pytest+testinfra pour le challenge filtres-jinja-avances.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/filtres-avances.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists, message(
        en=f"{RESULT_FILE} is missing. The four lines go into a single file, "
           f"each one rendering one advanced filter.",
        fr=f"{RESULT_FILE} est absent. Les quatre lignes vont dans un seul "
           f"fichier, chacune rendant un filtre avancé.",
    )


def test_regex_search(host):
    """regex_search('^([a-z]+)') retourne 'web'."""
    content = host.file(RESULT_FILE).content_string
    assert "prefix=web" in content, message(
        en="« prefix=web » is missing. regex_search returns the FIRST match, "
           "or the first capture group when the pattern has one: "
           "regex_search('^([a-z]+)').",
        fr="« prefix=web » manque. regex_search rend la PREMIÈRE "
           "correspondance, ou le premier groupe capturant quand le motif en "
           "a un : regex_search('^([a-z]+)').",
    )


def test_b64encode(host):
    """b64encode('admin:secret') = 'YWRtaW46c2VjcmV0'."""
    content = host.file(RESULT_FILE).content_string
    assert "b64=YWRtaW46c2VjcmV0" in content, message(
        en="« b64=YWRtaW46c2VjcmV0 » is missing. b64encode encodes "
           "« admin:secret »; a different result usually means a trailing "
           "space or newline slipped into the source string.",
        fr="« b64=YWRtaW46c2VjcmV0 » manque. b64encode encode "
           "« admin:secret » ; un autre résultat signale en général une "
           "espace ou un retour à la ligne glissé dans la chaîne source.",
    )


def test_flatten(host):
    """flatten([[1,2], [3, [4,5]]]) = [1, 2, 3, 4, 5]."""
    content = host.file(RESULT_FILE).content_string
    assert "flat=[1, 2, 3, 4, 5]" in content, message(
        en="« flat=[1, 2, 3, 4, 5] » is missing. flatten goes all the way "
           "down by default; flatten(levels=1) would leave [1, 2, 3, [4, 5]].",
        fr="« flat=[1, 2, 3, 4, 5] » manque. flatten descend jusqu'au bout "
           "par défaut ; flatten(levels=1) laisserait [1, 2, 3, [4, 5]].",
    )


def test_sha256(host):
    """hash('sha256') sur 'foobar' = c3ab8ff13720..."""
    content = host.file(RESULT_FILE).content_string
    # SHA256 de 'foobar' = c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2
    assert "sha256=c3ab8ff13720" in content, message(
        en="The sha256 of « foobar » does not appear. The filter is "
           "hash('sha256'); without an argument, hash defaults to sha1 and "
           "gives something else entirely.",
        fr="Le sha256 de « foobar » n'apparaît pas. Le filtre est "
           "hash('sha256') ; sans argument, hash retombe sur sha1 et rend "
           "tout autre chose.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
