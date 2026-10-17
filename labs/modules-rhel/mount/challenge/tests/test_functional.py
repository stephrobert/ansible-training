"""Tests pytest+testinfra pour le challenge module mount.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message, reboot_and_wait

TARGET_HOST = "db1.lab"

IMAGE = "/opt/lab-disk.img"
POINT = "/mnt/lab-data"
DURCISSEMENT = ("noatime", "nodev", "nosuid")


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_image_file_exists(host):
    f = host.file(IMAGE)
    assert f.exists, message(
        en=f"{IMAGE} is missing. First step: create a 100 MB image, with dd "
           f"and creates: so the task stays idempotent.",
        fr=f"{IMAGE} est absent. Première étape : créer une image de 100 Mo, "
           f"avec dd et creates: pour que la tâche reste idempotente.",
    )
    assert f.is_file, message(
        en=f"{IMAGE} is not an ordinary file.",
        fr=f"{IMAGE} n'est pas un fichier ordinaire.",
    )
    # 100Mo = environ 104857600 bytes
    assert 90 * 1024 * 1024 < f.size < 110 * 1024 * 1024, message(
        en=f"{IMAGE} weighs {f.size // (1024 * 1024)} MB, expected about 100. "
           f"With dd, that is bs=1M count=100, or bs=1024 count=102400.",
        fr=f"{IMAGE} pèse {f.size // (1024 * 1024)} Mo, attendu environ 100. "
           f"Avec dd, c'est bs=1M count=100, ou bs=1024 count=102400.",
    )


def test_mountpoint_is_mounted(host):
    """/mnt/lab-data doit etre un point de montage actif."""
    mp = host.mount_point(POINT)
    assert mp.exists, message(
        en=f"{POINT} is not mounted. state: present only writes to fstab; it "
           f"is state: mounted that writes AND mounts right away.",
        fr=f"{POINT} n'est pas monté. state: present se contente d'écrire dans "
           f"fstab ; c'est state: mounted qui écrit ET monte tout de suite.",
    )
    assert mp.filesystem == "ext4", message(
        en=f"{POINT} carries a {mp.filesystem} filesystem, expected ext4. The "
           f"image has to be formatted before being mounted, with "
           f"community.general.filesystem.",
        fr=f"{POINT} porte un système de fichiers {mp.filesystem}, attendu "
           f"ext4. L'image doit être formatée avant d'être montée, avec "
           f"community.general.filesystem.",
    )


def test_fstab_contains_entry(host):
    content = host.file("/etc/fstab").content_string
    assert "lab-disk.img" in content, message(
        en="/etc/fstab does not mention the image. Mount the FILE, not a "
           "/dev/loopN: a loop association made by losetup disappears at "
           "reboot, and that is exactly what this lab is about.",
        fr="/etc/fstab ne mentionne pas l'image. Monte le FICHIER, pas un "
           "/dev/loopN : une association loop faite par losetup disparaît au "
           "redémarrage, et c'est précisément le sujet de ce lab.",
    )
    assert POINT in content, message(
        en=f"/etc/fstab has no entry for {POINT}.",
        fr=f"/etc/fstab n'a aucune entrée pour {POINT}.",
    )
    assert "ext4" in content, message(
        en="The fstab entry does not state the ext4 type. The module's fstype: "
           "option writes it.",
        fr="L'entrée fstab n'annonce pas le type ext4. C'est l'option fstype: "
           "du module qui l'écrit.",
    )
    assert "noatime" in content, message(
        en="The fstab entry carries none of the required options. All of them "
           "go into a single opts:, comma-separated: "
           "loop,defaults,noatime,nodev,nosuid.",
        fr="L'entrée fstab ne porte aucune des options demandées. Elles vont "
           "toutes dans un seul opts:, séparées par des virgules : "
           "loop,defaults,noatime,nodev,nosuid.",
    )


def test_mount_options_active(host):
    """Verifier que les options sont actives (pas seulement dans fstab)."""
    cmd = host.run(f"findmnt -no OPTIONS {POINT}")
    assert cmd.rc == 0, message(
        en=f"findmnt does not find {POINT}: nothing is mounted there right "
           f"now, whatever fstab says.",
        fr=f"findmnt ne trouve pas {POINT} : rien n'y est monté à cet instant, "
           f"quoi qu'en dise fstab.",
    )
    for option in DURCISSEMENT:
        assert option in cmd.stdout, message(
            en=f"The {option} option is not active on the live mount (seen: "
               f"'{cmd.stdout.strip()}'). Written in fstab but missing here "
               f"means the filesystem was mounted before the entry, and never "
               f"remounted: state: mounted does both in the right order.",
            fr=f"L'option {option} n'est pas active sur le montage courant "
               f"(vu : '{cmd.stdout.strip()}'). Écrite dans fstab mais absente "
               f"ici, cela signale un système de fichiers monté avant "
               f"l'entrée, et jamais remonté : state: mounted fait les deux "
               f"dans le bon ordre.",
        )


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

    mp = host.mount_point(POINT)
    assert mp.exists, message(
        en=f"After reboot, {POINT} is NOT mounted again. A loop device mounted "
           f"through losetup + /dev/loopN does not survive: the loop "
           f"association is lost. Mount the FILE with the loop option in "
           f"fstab, and systemd takes care of the rest.",
        fr=f"Après reboot, {POINT} n'est PAS remonté. Un loop device monté via "
           f"losetup + /dev/loopN ne survit pas : l'association loop est "
           f"perdue. Il faut monter le FICHIER avec l'option loop dans fstab, "
           f"systemd s'occupe du reste.",
    )
    options = host.check_output(f"findmnt -no OPTIONS {POINT}")
    for opt in DURCISSEMENT:
        assert opt in options, message(
            en=f"After reboot, the {opt} option is gone (seen: '{options}'). "
               f"The automatic remount replays fstab: an option missing here "
               f"was never written there.",
            fr=f"Après reboot, l'option {opt} a disparu (vu : '{options}'). Le "
               f"remontage automatique rejoue fstab : une option absente ici "
               f"n'y a jamais été écrite.",
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
