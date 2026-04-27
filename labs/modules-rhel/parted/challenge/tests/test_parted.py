"""Tests pytest+testinfra pour le challenge parted (2 partitions GPT sur loop0).

Pré-requis : /dev/loop10 doit être un loopback préparé via _PRE_CLEANUPS.
"""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_loop0_existe(host):
    result = host.run("sudo test -b /dev/loop10")
    assert result.rc == 0, (
        "/dev/loop10 doit être un block device (loopback préparé par _PRE_CLEANUPS)."
    )


def test_table_gpt(host):
    """parted doit avoir créé une table GPT."""
    result = host.run("sudo parted -s /dev/loop10 print")
    assert result.rc == 0, f"parted a échoué : {result.stderr}"
    assert "gpt" in result.stdout.lower(), (
        f"Table de partitions doit être en GPT. Sortie parted :\n{result.stdout}"
    )


def test_partition_1_existe(host):
    """La partition 1 (boot) doit exister sur /dev/loop10p1."""
    result = host.run("sudo test -b /dev/loop10p1")
    assert result.rc == 0, "/dev/loop10p1 doit exister (1re partition GPT)."


def test_partition_2_existe(host):
    """La partition 2 (data) doit exister sur /dev/loop10p2."""
    result = host.run("sudo test -b /dev/loop10p2")
    assert result.rc == 0, "/dev/loop10p2 doit exister (2e partition GPT)."


def test_2_partitions_au_total(host):
    """parted -m doit montrer exactement 2 partitions."""
    result = host.run("sudo parted -sm /dev/loop10 print")
    assert result.rc == 0
    # Format machine-readable : la 1re ligne est l'en-tête, les suivantes sont les
    # partitions. On compte les lignes qui commencent par un chiffre suivi de `:`.
    parts = [line for line in result.stdout.splitlines() if line and line[0].isdigit()]
    assert len(parts) == 2, (
        f"2 partitions attendues, trouvées {len(parts)}. Sortie parted -sm :\n{result.stdout}"
    )
