"""Tests pytest+testinfra pour le challenge parted (3 partitions GPT sur /dev/vdb).

Pré-requis : db1.lab possède un disque secondaire réel /dev/vdb de 5 GiB
(déclaré via extra_disk_gb dans meta.yml). Le setup.yaml du lab remet le
disque à zéro : lancez le lab via dsoxlab avant de jouer votre solution.
"""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
DEVICE = "/dev/vdb"

MIB = 1024 * 1024
GIB = 1024 * MIB


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def parted_output(host):
    """Sortie machine-readable de parted : en-têtes + une ligne par partition."""
    result = host.run(f"sudo parted -sm {DEVICE} unit MiB print")
    assert result.rc == 0, (
        f"parted a échoué sur {DEVICE} : {result.stderr}. "
        f"Le disque secondaire existe-t-il ? Relancez le setup du lab (dsoxlab)."
    )
    return result.stdout


@pytest.fixture(scope="module")
def partition_lines(parted_output):
    """Lignes de partitions : elles commencent par leur numéro suivi de ':'."""
    return [
        line for line in parted_output.splitlines() if line and line[0].isdigit()
    ]


def _size_bytes(host, dev):
    result = host.run(f"sudo blockdev --getsize64 {dev}")
    assert result.rc == 0, f"blockdev a échoué sur {dev} : {result.stderr}"
    return int(result.stdout.strip())


def test_vdb_existe(host):
    result = host.run(f"sudo test -b {DEVICE}")
    assert result.rc == 0, (
        f"{DEVICE} doit être un block device : c'est le disque secondaire de "
        f"db1.lab, provisionné par l'infra du lab. Relancez le setup (dsoxlab)."
    )


def test_table_gpt(host):
    result = host.run(f"sudo parted -s {DEVICE} print")
    assert result.rc == 0, f"parted a échoué : {result.stderr}"
    assert "gpt" in result.stdout.lower(), (
        f"Table de partitions attendue : gpt, vu :\n{result.stdout}\n"
        f"Posez le label GPT via le paramètre label du module de partitionnement."
    )


def test_3_partitions(partition_lines, parted_output):
    assert len(partition_lines) == 3, (
        f"3 partitions attendues sur {DEVICE}, vu : {len(partition_lines)}. "
        f"Sortie parted -sm :\n{parted_output}"
    )


@pytest.mark.parametrize("part_number", [1, 2, 3])
def test_partition_est_block_device(host, part_number):
    part = f"{DEVICE}{part_number}"
    result = host.run(f"sudo test -b {part}")
    assert result.rc == 0, (
        f"{part} doit exister en tant que block device. "
        f"Vérifiez le découpage de {DEVICE} (numéro, part_start, part_end)."
    )


def test_vdb1_taille_500mib(host):
    size = _size_bytes(host, f"{DEVICE}1")
    assert 450 * MIB <= size <= 550 * MIB, (
        f"{DEVICE}1 doit faire environ 500 MiB (partition EFI), "
        f"vu : {size / MIB:.0f} MiB. Bornes attendues : 1MiB à 501MiB."
    )


def test_vdb2_taille_4gib(host):
    size = _size_bytes(host, f"{DEVICE}2")
    assert 3.8 * GIB <= size <= 4.2 * GIB, (
        f"{DEVICE}2 doit faire environ 4 GiB (future partition de données), "
        f"vu : {size / GIB:.2f} GiB. Elle démarre là où finit {DEVICE}1."
    )


def test_vdb3_prend_le_reste(parted_output, partition_lines):
    """La partition 3 doit s'étendre jusqu'à la fin du disque (part_end 100%)."""
    # Ligne du disque, ex. "/dev/vdb:5120MiB:virtblk:512:512:gpt:...".
    disk_line = next(
        line for line in parted_output.splitlines() if line.startswith(DEVICE)
    )
    disk_end = float(disk_line.split(":")[1].rstrip("MiB"))
    p3_end = float(partition_lines[2].split(":")[2].rstrip("MiB"))
    assert p3_end >= disk_end * 0.98, (
        f"{DEVICE}3 doit occuper tout le reste du disque : fin attendue vers "
        f"{disk_end:.0f} MiB, vu {p3_end:.0f} MiB. Utilisez une borne de fin "
        f"relative (100%) plutôt qu'une taille figée."
    )


def test_vdb1_flags_boot_esp(partition_lines):
    """La partition 1 porte les flags d'une partition EFI (boot, esp)."""
    flags = partition_lines[0].split(":")[-1].rstrip(";")
    assert "esp" in flags, (
        f"{DEVICE}1 doit porter le flag esp (partition EFI), flags vus : "
        f"'{flags}'. Posez les flags boot et esp sur la partition 1."
    )


def test_vdb3_flag_lvm(partition_lines):
    """La partition 3 porte le flag lvm (futur PV)."""
    flags = partition_lines[2].split(":")[-1].rstrip(";")
    assert "lvm" in flags, (
        f"{DEVICE}3 doit porter le flag lvm, flags vus : '{flags}'. "
        f"Posez le flag lvm sur la partition 3."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
