"""Tests pytest+testinfra pour le challenge group_vars/host_vars.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


def test_web1_marker_exists(web1):
    f = web1.file("/tmp/lab55-port-web1.lab.txt")
    assert f.exists, message(
        en="/tmp/lab55-port-web1.lab.txt is missing on web1.lab. Each host "
           "writes its own marker: the name depends on inventory_hostname.",
        fr="/tmp/lab55-port-web1.lab.txt est absent de web1.lab. Chaque hôte "
           "écrit son propre marqueur : le nom dépend d'inventory_hostname.",
    )
    assert f.mode == 0o644, message(
        en=f"The marker is {oct(f.mode)}, expected 0644.",
        fr=f"Le marqueur est en {oct(f.mode)}, attendu 0644.",
    )


def test_web1_host_vars_wins(web1):
    """host_vars/web1.lab.yml a la priorité sur group_vars."""
    content = web1.file("/tmp/lab55-port-web1.lab.txt").content_string
    assert "9090" in content, message(
        en=f"Expected 9090, from host_vars/web1.lab.yml, received: {content}. "
           f"host_vars beats every group_vars: it is the most specific "
           f"source, so it wins.",
        fr=f"Attendu 9090, qui vient de host_vars/web1.lab.yml, reçu : "
           f"{content}. host_vars l'emporte sur tous les group_vars : c'est "
           f"la source la plus spécifique, donc la gagnante.",
    )


def test_web2_group_vars_webservers_wins(web2):
    """group_vars/webservers.yml gagne sur group_vars/all.yml."""
    content = web2.file("/tmp/lab55-port-web2.lab.txt").content_string
    assert "8080" in content, message(
        en=f"Expected 8080, from group_vars/webservers.yml, received: "
           f"{content}. web2 has no host_vars: the group it belongs to beats "
           f"group_vars/all.",
        fr=f"Attendu 8080, qui vient de group_vars/webservers.yml, reçu : "
           f"{content}. web2 n'a pas de host_vars : le groupe auquel il "
           f"appartient l'emporte sur group_vars/all.",
    )


def test_db1_group_vars_all_fallback(db1):
    """db1 hérite de group_vars/all.yml — pas de surcharge."""
    content = db1.file("/tmp/lab55-port-db1.lab.txt").content_string
    assert "80" in content, message(
        en=f"Expected 80, from group_vars/all.yml, received: {content}. db1 "
           f"is not a webserver and has no host_vars: nothing overrides the "
           f"default.",
        fr=f"Attendu 80, qui vient de group_vars/all.yml, reçu : {content}. "
           f"db1 n'est pas un webserver et n'a pas de host_vars : rien ne "
           f"surcharge le défaut.",
    )


def test_resolved_value_format(web1):
    """Le format du marqueur correspond au pattern attendu."""
    content = web1.file("/tmp/lab55-port-web1.lab.txt").content_string
    assert content.startswith("port resolu pour web1.lab : "), message(
        en=f"The marker does not start with « port resolu pour web1.lab : » "
           f"(seen: {content[:60]}). The mission fixes the format so the "
           f"three hosts can be compared.",
        fr=f"Le marqueur ne commence pas par « port resolu pour web1.lab : » "
           f"(vu : {content[:60]}). La mission fixe le format pour que les "
           f"trois hôtes soient comparables.",
    )
    assert content.rstrip().endswith("9090"), message(
        en=f"The marker does not end with the resolved port (seen: "
           f"{content.rstrip()[-40:]}).",
        fr=f"Le marqueur ne finit pas par le port résolu (vu : "
           f"{content.rstrip()[-40:]}).",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
