"""Tests pytest+testinfra pour le challenge boucles-with-deprecated.

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


@pytest.mark.parametrize("fruit", ["apple", "banana", "cherry"])
def test_withitems_files(host, fruit):
    f = host.file(f"/tmp/withitems-{fruit}.txt")
    assert f.exists, message(
        en=f"/tmp/withitems-{fruit}.txt is missing. with_items walks a flat "
           f"list and exposes each element as item; loop: does the same "
           f"thing, and is the form to prefer today.",
        fr=f"/tmp/withitems-{fruit}.txt manque. with_items parcourt une liste "
           f"plate et expose chaque élément en item ; loop: fait la même "
           f"chose, et c'est la forme à préférer aujourd'hui.",
    )


def test_withdict_nginx(host):
    f = host.file("/tmp/withdict-nginx.txt")
    assert f.exists, message(
        en="/tmp/withdict-nginx.txt is missing. with_dict walks a mapping and "
           "exposes item.key and item.value, where with_items would hand over "
           "the whole dictionary.",
        fr="/tmp/withdict-nginx.txt manque. with_dict parcourt un "
           "dictionnaire et expose item.key et item.value, là où with_items "
           "rendrait le dictionnaire entier.",
    )
    assert "80" in f.content_string, message(
        en="The file does not carry the port 80: that is item.value, the "
           "name of the file being item.key.",
        fr="Le fichier ne porte pas le port 80 : c'est item.value, le nom du "
           "fichier étant item.key.",
    )


def test_withdict_redis(host):
    f = host.file("/tmp/withdict-redis.txt")
    assert f.exists, message(
        en="/tmp/withdict-redis.txt is missing: the loop only produced part "
           "of the mapping's entries.",
        fr="/tmp/withdict-redis.txt manque : la boucle n'a produit qu'une "
           "partie des entrées du dictionnaire.",
    )
    assert "6379" in f.content_string, message(
        en="The file does not carry the port 6379.",
        fr="Le fichier ne porte pas le port 6379.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
