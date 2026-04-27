"""Tests pytest+testinfra pour le challenge block-rescue-always."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_rescue_executed(host):
    f = host.file("/tmp/challenge-rescue.txt")
    assert f.exists, "rescue: doit avoir posé le fichier (block en échec)"
    assert "rescue triggered" in f.content_string


def test_always_executed(host):
    f = host.file("/tmp/challenge-always.txt")
    assert f.exists, "always: doit avoir posé le fichier (toujours exécuté)"
    assert "always executed" in f.content_string
