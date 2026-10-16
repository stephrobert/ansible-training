"""Tests pytest+testinfra pour le challenge assert + fail."""

import re

import pytest

from conftest import assert_idempotent, lab_host, lab_solution_text, message

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_marker_exists(host):
    f = host.file("/tmp/lab-assert-validated.txt")
    assert f.exists, message(
        en="The marker must exist after a successful validation",
        fr="Le marker doit exister après validation réussie",
    )
    assert f.is_file, message(
        en="The marker exists but is not an ordinary file.",
        fr="Le marqueur existe mais n'est pas un fichier ordinaire.",
    )
    assert f.mode == 0o644, message(
        en=f"The marker is {oct(f.mode)}, expected 0644.",
        fr=f"Le marqueur est en {oct(f.mode)}, attendu 0644.",
    )


def test_marker_contains_validation_ok(host):
    content = host.file("/tmp/lab-assert-validated.txt").content_string
    assert "Validations OK" in content, message(
        en="The marker does not carry « Validations OK »: it must be written "
           "AFTER the assert, so that its presence proves the checks passed.",
        fr="Le marqueur ne porte pas « Validations OK » : il doit être écrit "
           "APRÈS l'assert, pour que sa présence prouve que les contrôles "
           "sont passés.",
    )


def test_marker_contains_os_info(host):
    content = host.file("/tmp/lab-assert-validated.txt").content_string
    # AlmaLinux 9.x ou similaire
    assert (
        "AlmaLinux" in content or "Rocky" in content or "RedHat" in content
    ), message(
        en=f"The marker does not name the target's distribution. Render a "
           f"real fact (ansible_distribution): a hardcoded value would prove "
           f"nothing.\nSeen: {content[:150]}",
        fr=f"Le marqueur ne nomme pas la distribution de la cible. Rends un "
           f"vrai fact (ansible_distribution) : une valeur écrite en dur ne "
           f"prouverait rien.\nVu : {content[:150]}",
    )


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

    assert re.search(r"\bfail:", text) or "ansible.builtin.fail" in text, message(
        en="The solution must refuse a wrong host with ansible.builtin.fail.",
        fr="La solution doit refuser un mauvais hôte avec ansible.builtin.fail.",
    )
    assert "when:" in text and "inventory_hostname" in text, message(
        en="The defensive fail must be guarded by a when: on inventory_hostname.",
        fr="Le fail défensif doit être gardé par un when: sur inventory_hostname.",
    )
    assert re.search(r"\bassert:", text) or "ansible.builtin.assert" in text, message(
        en="The solution must validate the prerequisites with ansible.builtin.assert.",
        fr="La solution doit valider les prérequis avec ansible.builtin.assert.",
    )
    assert "that:" in text, message(
        en="The assert module must carry a 'that:' list.",
        fr="Le module assert doit porter une liste 'that:'.",
    )
    assert "ansible_distribution" in text, message(
        en="The assert precondition must be about real facts of the target "
        "(ansible_distribution for instance), not a trivial condition.",
        fr="La précondition assert doit porter sur des facts réels de la cible "
        "(ex. ansible_distribution), pas sur une condition triviale.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
