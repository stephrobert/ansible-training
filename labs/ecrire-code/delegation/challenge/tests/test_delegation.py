"""Tests pytest+testinfra pour le challenge delegation."""

import pytest

from conftest import lab_host


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
    assert web1.file("/tmp/delegation-on-web1.lab.txt").exists


def test_marker_on_web2(web2):
    assert web2.file("/tmp/delegation-on-web2.lab.txt").exists


def test_marker_on_db1(db1):
    """delegate_to: db1.lab doit poser le fichier sur db1, pas sur les webservers."""
    assert db1.file("/tmp/delegation-on-db1.txt").exists, (
        "/tmp/delegation-on-db1.txt doit exister sur db1.lab "
        "(preuve delegate_to: db1.lab)."
    )


def test_no_db_marker_on_web1(web1):
    """Le marqueur db ne doit PAS apparaître sur les webservers."""
    assert not web1.file("/tmp/delegation-on-db1.txt").exists, (
        "Le fichier delegation-on-db1.txt ne doit PAS apparaître sur web1."
    )


def test_no_db_marker_on_web2(web2):
    assert not web2.file("/tmp/delegation-on-db1.txt").exists, (
        "Le fichier delegation-on-db1.txt ne doit PAS apparaître sur web2."
    )
