"""Tests pytest+testinfra pour le challenge delegation."""

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


def test_marker_on_web1(web1):
    assert web1.file("/tmp/delegation-on-web1.lab.txt").exists, message(
        en="The marker is missing on web1: the ordinary task, without "
           "delegate_to, must run on each host of the play.",
        fr="Le marqueur manque sur web1 : la tâche ordinaire, sans "
           "delegate_to, doit tourner sur chaque hôte du play.",
    )


def test_marker_on_web2(web2):
    assert web2.file("/tmp/delegation-on-web2.lab.txt").exists, message(
        en="The marker is missing on web2: it was laid down on web1 but not "
           "here, so the play targets only one host.",
        fr="Le marqueur manque sur web2 : il a été posé sur web1 mais pas "
           "ici, donc le play ne vise qu'un seul hôte.",
    )


def test_marker_on_db1(db1):
    """delegate_to: db1.lab doit poser le fichier sur db1, pas sur les webservers."""
    assert db1.file("/tmp/delegation-on-db1.txt").exists, message(
        en="/tmp/delegation-on-db1.txt must exist on db1.lab "
        "(the proof of delegate_to: db1.lab).",
        fr="/tmp/delegation-on-db1.txt doit exister sur db1.lab "
        "(preuve delegate_to: db1.lab).",
    )


def test_no_db_marker_on_web1(web1):
    """Le marqueur db ne doit PAS apparaître sur les webservers."""
    assert not web1.file("/tmp/delegation-on-db1.txt").exists, message(
        en="The delegation-on-db1.txt file must NOT appear on web1.",
        fr="Le fichier delegation-on-db1.txt ne doit PAS apparaître sur web1.",
    )


def test_no_db_marker_on_web2(web2):
    assert not web2.file("/tmp/delegation-on-db1.txt").exists, message(
        en="The delegation-on-db1.txt file must NOT appear on web2.",
        fr="Le fichier delegation-on-db1.txt ne doit PAS apparaître sur web2.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
