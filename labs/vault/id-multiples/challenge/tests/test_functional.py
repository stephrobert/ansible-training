"""Tests lab 79 : vault-id multiples."""

import pytest
from conftest import lab_host, assert_idempotent


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


def test_dev_file_on_web1(web1):
    """web1.lab (groupe dev) reçoit son fichier déchiffré."""
    f = web1.file("/tmp/lab79-challenge-web1.lab.txt")
    assert f.exists


def test_prod_file_on_db1(db1):
    """db1.lab (groupe prod) reçoit son fichier déchiffré."""
    f = db1.file("/tmp/lab79-challenge-db1.lab.txt")
    assert f.exists


def _lines(host, path):
    """Lignes strippées d'un fichier distant.

    On teste ensuite l'appartenance de la LIGNE entière à cette liste, et non une
    sous-chaîne du contenu : le host attendu est prouvé par égalité de ligne, et
    CodeQL ne voit plus une sanitization d'URL incomplète
    (py/incomplete-url-substring-sanitization).
    """
    return [line.strip() for line in host.file(path).content_string.splitlines()]


def test_dev_db_host(web1):
    """web1 voit le db_host de dev (déchiffré avec vault-id dev)."""
    lines = _lines(web1, "/tmp/lab79-challenge-web1.lab.txt")
    assert "db_host: dev-db.example.com" in lines
    assert "Environnement: dev" in lines


def test_prod_db_host(db1):
    """db1 voit le db_host de prod (déchiffré avec vault-id prod)."""
    lines = _lines(db1, "/tmp/lab79-challenge-db1.lab.txt")
    assert "db_host: prod-db.example.com" in lines
    assert "Environnement: prod" in lines


def test_passwords_different_lengths(web1, db1):
    """Les 2 environnements ont des passwords de longueurs différentes (preuve dechiffrement séparé)."""
    dev_content = web1.file("/tmp/lab79-challenge-web1.lab.txt").content_string
    prod_content = db1.file("/tmp/lab79-challenge-db1.lab.txt").content_string
    # dev: "DevDBPass123" (12 chars), prod: "ProdDBPassUltraStrong!2026" (26 chars)
    assert "length: 12" in dev_content
    assert "length: 26" in prod_content


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
