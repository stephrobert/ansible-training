"""Tests pytest+testinfra pour le challenge parallélisme (serial: 1)."""

import pytest

from conftest import lab_host, lab_solution_text, assert_idempotent

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


def test_solution_declares_max_fail_percentage():
    """L'énoncé impose max_fail_percentage au niveau du play.

    Ce keyword est une tolérance d'échec : le prouver dynamiquement exigerait
    de provoquer un vrai échec de host. On vérifie donc structurellement qu'il
    est bien déclaré dans la solution, comme l'exige l'énoncé.
    """
    content = lab_solution_text(__file__)
    assert "max_fail_percentage" in content, (
        "Le solution.yml doit déclarer max_fail_percentage au niveau du play "
        "(mot-clé imposé par l'énoncé, à côté de serial: 1)."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
