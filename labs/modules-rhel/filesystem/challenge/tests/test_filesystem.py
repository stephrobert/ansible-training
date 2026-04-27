"""Tests pytest+testinfra pour le challenge filesystem (ext4 + xfs sur loop0).

Pré-requis : un loopback /dev/loop10 partitionné en 2 (loop0p1, loop0p2),
préparé via _PRE_CLEANUPS dans conftest.py.
"""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_loopback_partitions_present(host):
    """Vérifie que /dev/loop10p1 et /dev/loop10p2 existent."""
    for part in ["/dev/loop10p1", "/dev/loop10p2"]:
        result = host.run(f"sudo test -b {part}")
        assert result.rc == 0, (
            f"{part} doit être un block device (loopback préparé en amont). "
            f"Le _PRE_CLEANUPS du conftest doit créer le loopback."
        )


def test_p1_est_ext4(host):
    """La 1re partition doit être en ext4 (community.general.filesystem)."""
    result = host.run("sudo blkid -o value -s TYPE /dev/loop10p1")
    assert result.rc == 0, f"blkid a échoué sur /dev/loop10p1 : {result.stderr}"
    assert result.stdout.strip() == "ext4", (
        f"/dev/loop10p1 doit être en ext4, trouvé : '{result.stdout.strip()}'"
    )


def test_p2_est_xfs(host):
    """La 2e partition doit être en xfs."""
    result = host.run("sudo blkid -o value -s TYPE /dev/loop10p2")
    assert result.rc == 0, f"blkid a échoué sur /dev/loop10p2 : {result.stderr}"
    assert result.stdout.strip() == "xfs", (
        f"/dev/loop10p2 doit être en xfs, trouvé : '{result.stdout.strip()}'"
    )
