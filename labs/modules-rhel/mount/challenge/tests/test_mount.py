"""Tests pytest+testinfra pour le challenge module mount."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_image_file_exists(host):
    f = host.file("/opt/lab-disk.img")
    assert f.exists
    assert f.is_file
    # 100Mo = environ 104857600 bytes
    assert f.size > 90 * 1024 * 1024
    assert f.size < 110 * 1024 * 1024


def test_mountpoint_is_mounted(host):
    """/mnt/lab-data doit etre un point de montage actif."""
    mp = host.mount_point("/mnt/lab-data")
    assert mp.exists, "/mnt/lab-data doit etre monte"
    assert mp.filesystem == "ext4"


def test_fstab_contains_entry(host):
    content = host.file("/etc/fstab").content_string
    assert "lab-disk.img" in content
    assert "/mnt/lab-data" in content
    assert "ext4" in content
    assert "noatime" in content


def test_mount_options_active(host):
    """Verifier que les options sont actives (pas seulement dans fstab)."""
    cmd = host.run("findmnt -no OPTIONS /mnt/lab-data")
    assert cmd.rc == 0, "findmnt doit trouver /mnt/lab-data"
    assert "noatime" in cmd.stdout
    assert "nodev" in cmd.stdout
    assert "nosuid" in cmd.stdout
