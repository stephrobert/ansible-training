"""Tests pytest+testinfra pour le challenge lineinfile-vs-template.

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


# === lineinfile : 1 ligne dans /etc/hosts ===

def test_etc_hosts_contains_custom_entry(host):
    content = host.file("/etc/hosts").content_string
    assert "192.168.99.99 mon-host.lab" in content, message(
        en="lineinfile must have added '192.168.99.99 mon-host.lab' to "
           "/etc/hosts. This is the case lineinfile is FOR: one line inside a "
           "file you do not own, and must not rewrite whole.",
        fr="lineinfile doit avoir ajouté '192.168.99.99 mon-host.lab' à "
           "/etc/hosts. C'est le cas POUR lequel lineinfile existe : une "
           "ligne dans un fichier qu'on ne possède pas, et qu'on ne doit pas "
           "réécrire en entier.",
    )


# === template : fichier complet /etc/myapp.conf ===

def test_myapp_conf_exists(host):
    assert host.file("/etc/myapp.conf").exists, message(
        en="/etc/myapp.conf is missing. This file belongs to the application: "
           "it is generated whole, with template, and not patched line by "
           "line. That is the other half of the lab.",
        fr="/etc/myapp.conf est absent. Ce fichier appartient à "
           "l'application : il se génère en entier, avec template, et ne se "
           "rafistole pas ligne à ligne. C'est l'autre moitié du lab.",
    )


def test_myapp_conf_server_host(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "host = 0.0.0.0" in content, message(
        en="« host = 0.0.0.0 » is missing: the template did not interpolate "
           "server.host.",
        fr="« host = 0.0.0.0 » manque : le template n'a pas interpolé "
           "server.host.",
    )


def test_myapp_conf_server_port(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "port = 8080" in content, message(
        en="« port = 8080 » is missing: the template did not interpolate "
           "server.port.",
        fr="« port = 8080 » manque : le template n'a pas interpolé "
           "server.port.",
    )


def test_myapp_conf_server_workers(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "workers = 4" in content, message(
        en="The template must interpolate server.workers into "
           "'workers = 4'.",
        fr="Le template doit interpoler server.workers en 'workers = 4'.",
    )


def test_myapp_conf_db_url(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "url = postgres://db1.lab/myapp" in content, message(
        en="The template must interpolate database.url into "
           "'url = postgres://db1.lab/myapp'.",
        fr="Le template doit interpoler database.url en "
           "'url = postgres://db1.lab/myapp'.",
    )


def test_myapp_conf_db_pool_size(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "pool_size = 10" in content, message(
        en="« pool_size = 10 » is missing: the template did not interpolate "
           "database.pool_size.",
        fr="« pool_size = 10 » manque : le template n'a pas interpolé "
           "database.pool_size.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
