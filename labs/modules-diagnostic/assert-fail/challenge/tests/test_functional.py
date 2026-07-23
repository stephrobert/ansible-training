"""Tests pytest+testinfra pour le challenge assert + fail."""

import re

import pytest

from conftest import lab_host, assert_idempotent, lab_solution_text

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_marker_exists(host):
    f = host.file("/tmp/lab-assert-validated.txt")
    assert f.exists, "Le marker doit exister apres validation reussie"
    assert f.is_file
    assert f.mode == 0o644


def test_marker_contains_validation_ok(host):
    content = host.file("/tmp/lab-assert-validated.txt").content_string
    assert "Validations OK" in content


def test_marker_contains_os_info(host):
    content = host.file("/tmp/lab-assert-validated.txt").content_string
    # AlmaLinux 9.x ou similaire
    assert "AlmaLinux" in content or "Rocky" in content or "RedHat" in content


def test_solution_defends_with_fail_and_assert():
    """Le cœur du lab : la garde défensive doit exister AVANT l'écriture.

    Le marqueur seul ne prouve rien : un simple `copy` sur db1 (l'hôte sain qui
    passe pytest) le pose sans aucune garde. Or le lab enseigne deux mécanismes
    qui empêchent de configurer un hôte non conforme à moitié :
      - `fail` + `when: inventory_hostname != 'db1.lab'` (branche d'erreur),
      - `assert` + `that:` portant sur des facts réels (précondition).
    On inspecte la solution car ces gardes ne laissent, par nature, aucun état
    système observable quand elles ne se déclenchent pas.
    """
    text = lab_solution_text(__file__)

    assert re.search(r"\bfail:", text) or "ansible.builtin.fail" in text, (
        "La solution doit refuser un mauvais hôte avec ansible.builtin.fail."
    )
    assert "when:" in text and "inventory_hostname" in text, (
        "Le fail défensif doit être gardé par un when: sur inventory_hostname."
    )
    assert re.search(r"\bassert:", text) or "ansible.builtin.assert" in text, (
        "La solution doit valider les prérequis avec ansible.builtin.assert."
    )
    assert "that:" in text, "Le module assert doit porter une liste 'that:'."
    assert "ansible_distribution" in text, (
        "La précondition assert doit porter sur des facts réels de la cible "
        "(ex. ansible_distribution), pas sur une condition triviale."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
