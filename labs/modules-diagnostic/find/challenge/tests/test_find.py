"""Tests pytest+testinfra pour le challenge module find."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_dossier_existe(host):
    f = host.file("/tmp/lab-find-cleanup")
    assert f.is_directory


@pytest.mark.parametrize("name", ["small1.log", "small2.log"])
def test_petits_logs_conserves(host, name):
    f = host.file(f"/tmp/lab-find-cleanup/{name}")
    assert f.exists, f"{name} doit etre conserve (taille < 5Mo)"


@pytest.mark.parametrize("name", ["big1.log", "big2.log", "big3.log"])
def test_gros_logs_supprimes(host, name):
    f = host.file(f"/tmp/lab-find-cleanup/{name}")
    assert not f.exists, f"{name} doit etre supprime (taille > 5Mo)"
