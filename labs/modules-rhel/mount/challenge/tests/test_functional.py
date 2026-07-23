"""Tests pytest+testinfra pour le challenge module mount."""

import pytest

from conftest import lab_host, assert_idempotent, reboot_and_wait

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


@pytest.mark.slow
def test_loop_device_survit_vraiment_au_reboot():
    """Prouve la persistance en REDÉMARRANT db1, au lieu de lire /etc/fstab.

    Le titre du lab est « monter un loop device PERSISTANT ». C'est le cas le
    plus piégeux : un `losetup /dev/loop0 fichier` puis un montage de /dev/loop0
    donne un runtime correct et ne survit PAS au reboot (l'association loop
    disparaît). La forme persistante monte le FICHIER avec l'option `loop`, et
    c'est systemd qui recrée le loop au démarrage. Seul un reboot le distingue.

    Marqué `slow` (redémarrage ~90 s), désélectionnable avec `pytest -m 'not slow'`.
    """
    host = reboot_and_wait(TARGET_HOST)

    mp = host.mount_point("/mnt/lab-data")
    assert mp.exists, (
        "Après reboot, /mnt/lab-data n'est PAS remonté. Un loop device monté via "
        "`losetup` + /dev/loopN ne survit pas : l'association loop est perdue. Il "
        "faut monter le FICHIER avec l'option `loop` dans fstab, systemd s'occupe "
        "du reste."
    )
    options = host.check_output("findmnt -no OPTIONS /mnt/lab-data")
    for opt in ("noatime", "nodev", "nosuid"):
        assert opt in options, (
            f"Après reboot, l'option {opt} a disparu (vu : '{options}'). Le "
            "remontage automatique doit rejouer toutes les options de fstab."
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
