"""Tests pytest+testinfra pour le challenge parallélisme (serial: 1)."""

import pytest

from conftest import lab_host

WEB1_FILE = "/tmp/serial-web1.lab.txt"
WEB2_FILE = "/tmp/serial-web2.lab.txt"


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


def test_marker_web1_exists(web1):
    assert web1.file(WEB1_FILE).exists, (
        f"{WEB1_FILE} doit exister sur web1.lab"
    )


def test_marker_web2_exists(web2):
    assert web2.file(WEB2_FILE).exists, (
        f"{WEB2_FILE} doit exister sur web2.lab"
    )


def test_web1_timestamp_before_web2(web1, web2):
    """serial:1 doit traiter web1 AVANT web2 (mtime croissant)."""
    mt1 = web1.file(WEB1_FILE).mtime
    mt2 = web2.file(WEB2_FILE).mtime
    assert mt1 < mt2, (
        f"web1 ({mt1}) doit être traité AVANT web2 ({mt2}) avec serial: 1. "
        f"Si les deux mtimes sont égaux, augmentez le sleep dans le challenge."
    )
