"""Tests lab 79 — vault-id multiples."""

import pytest
from conftest import lab_host


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


def test_dev_db_host(web1):
    """web1 voit le db_host de dev (déchiffré avec vault-id dev)."""
    content = web1.file("/tmp/lab79-challenge-web1.lab.txt").content_string
    assert "dev-db.example.com" in content
    assert "Environnement: dev" in content


def test_prod_db_host(db1):
    """db1 voit le db_host de prod (déchiffré avec vault-id prod)."""
    content = db1.file("/tmp/lab79-challenge-db1.lab.txt").content_string
    assert "prod-db.example.com" in content
    assert "Environnement: prod" in content


def test_passwords_different_lengths(web1, db1):
    """Les 2 environnements ont des passwords de longueurs différentes (preuve dechiffrement séparé)."""
    dev_content = web1.file("/tmp/lab79-challenge-web1.lab.txt").content_string
    prod_content = db1.file("/tmp/lab79-challenge-db1.lab.txt").content_string
    # dev: "DevDBPass123" (12 chars), prod: "ProdDBPassUltraStrong!2026" (26 chars)
    assert "length: 12" in dev_content
    assert "length: 26" in prod_content
