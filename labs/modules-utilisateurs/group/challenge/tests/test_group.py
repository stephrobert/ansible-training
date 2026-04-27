"""Tests pytest+testinfra pour le challenge module group."""

import pytest

from conftest import lab_host

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
    assert g.exists, f"Le groupe {name} doit exister"
    assert g.gid == gid, f"Le groupe {name} doit avoir GID {gid}, pas {g.gid}"


def test_myapp_system_group_exists_with_low_gid(host):
    g = host.group("myapp-system")
    assert g.exists
    assert g.gid < 1000, f"Un groupe systeme doit avoir GID < 1000, ici {g.gid}"
