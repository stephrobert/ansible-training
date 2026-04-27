"""Tests pytest+testinfra pour le challenge LVM storage."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_image_file_exists(host):
    f = host.file("/opt/lab-lvm.img")
    assert f.exists
    assert f.size > 490 * 1024 * 1024


def test_loop_device_active(host):
    cmd = host.run("losetup /dev/loop10")
    assert cmd.rc == 0, "loop10 doit etre associe"
    assert "lab-lvm.img" in cmd.stdout


def test_vg_exists(host):
    cmd = host.run("vgs --noheadings -o vg_name lab_vg")
    assert cmd.rc == 0
    assert "lab_vg" in cmd.stdout


def test_lv_exists_with_size(host):
    cmd = host.run("lvs --noheadings -o lv_name,lv_size --units M lab_vg/lab_lv")
    assert cmd.rc == 0
    assert "lab_lv" in cmd.stdout
    # LVM arrondit a des multiples du PE size (4MB par defaut) — accepte ~300-320M
    import re
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*[Mm]', cmd.stdout)
    assert m, f"Taille non trouvee : {cmd.stdout}"
    size = float(m.group(1).replace(',', '.'))
    assert 295 < size < 325, f"Taille {size}M hors plage 295-325M"


def test_lv_is_xfs(host):
    cmd = host.run("blkid -s TYPE -o value /dev/lab_vg/lab_lv")
    assert cmd.rc == 0
    assert cmd.stdout.strip() == "xfs"


def test_mountpoint_active_with_noatime(host):
    mp = host.mount_point("/mnt/lvm-data")
    assert mp.exists
    assert mp.filesystem == "xfs"

    cmd = host.run("findmnt -no OPTIONS /mnt/lvm-data")
    assert "noatime" in cmd.stdout


def test_fstab_entry_present(host):
    content = host.file("/etc/fstab").content_string
    assert "lab_vg" in content or "lab_lv" in content
    assert "/mnt/lvm-data" in content
