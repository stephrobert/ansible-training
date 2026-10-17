"""Tests pytest+testinfra pour le challenge module group."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("name,gid", [
    ("rhce-shared", 4000),
    ("rhce-admins", 4001),
    ("rhce-readonly", 4002),
])
def test_group_with_forced_gid(host, name, gid):
    g = host.group(name)
    assert g.exists, message(
        en=f"The {name} group must exist",
        fr=f"Le groupe {name} doit exister",
    )
    assert g.gid == gid, message(
        en=f"The {name} group must have GID {gid}, not {g.gid}",
        fr=f"Le groupe {name} doit avoir GID {gid}, pas {g.gid}",
    )


def test_myapp_system_group_exists_with_low_gid(host):
    g = host.group("myapp-system")
    assert g.exists, message(
        en="The myapp-system group does not exist. ansible.builtin.group "
           "with system: true, which picks a GID below 1000.",
        fr="Le groupe myapp-system n'existe pas. ansible.builtin.group avec "
           "system: true, qui prend un GID inférieur à 1000.",
    )
    assert g.gid < 1000, message(
        en=f"A system group must have a GID below 1000, here {g.gid}",
        fr=f"Un groupe système doit avoir GID < 1000, ici {g.gid}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
