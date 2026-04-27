"""Tests pytest+testinfra pour le challenge group_vars/host_vars."""

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


def test_web1_marker_exists(web1):
    f = web1.file("/tmp/lab55-port-web1.lab.txt")
    assert f.exists
    assert f.mode == 0o644


def test_web1_host_vars_wins(web1):
    """host_vars/web1.lab.yml a la priorité sur group_vars."""
    content = web1.file("/tmp/lab55-port-web1.lab.txt").content_string
    assert "9090" in content, f"Attendu 9090 (host_vars), reçu: {content}"


def test_web2_group_vars_webservers_wins(web2):
    """group_vars/webservers.yml gagne sur group_vars/all.yml."""
    content = web2.file("/tmp/lab55-port-web2.lab.txt").content_string
    assert "8080" in content, f"Attendu 8080 (group_vars/webservers), reçu: {content}"


def test_db1_group_vars_all_fallback(db1):
    """db1 hérite de group_vars/all.yml — pas de surcharge."""
    content = db1.file("/tmp/lab55-port-db1.lab.txt").content_string
    assert "80" in content, f"Attendu 80 (group_vars/all), reçu: {content}"


def test_resolved_value_format(web1):
    """Le format du marqueur correspond au pattern attendu."""
    content = web1.file("/tmp/lab55-port-web1.lab.txt").content_string
    assert content.startswith("port resolu pour web1.lab : ")
    assert content.rstrip().endswith("9090")
