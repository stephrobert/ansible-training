"""Tests pytest+testinfra pour le challenge LVM storage (PV, VG, LV sur /dev/vdb).

Pré-requis : db1.lab possède un disque secondaire réel /dev/vdb de 5 GiB
(déclaré via extra_disk_gb dans meta.yml). Le setup.yaml du lab rend le
disque vierge : lancez le lab via dsoxlab avant de jouer votre solution.
"""

import re

import pytest

from conftest import assert_idempotent, lab_host, message, reboot_and_wait

TARGET_HOST = "db1.lab"
DEVICE = "/dev/vdb"
VG = "lab_vg"
LV = "lab_lv"
LV_PATH = f"/dev/{VG}/{LV}"
MOUNT_POINT = "/mnt/lvm-data"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def _realpath(host, path):
    """Résout un chemin de device vers sa cible canonique (/dev/dm-N)."""
    result = host.run(f"sudo readlink -f {path}")
    return result.stdout.strip()


def _fstab_entries(host):
    """Lignes utiles de /etc/fstab, découpées en champs."""
    entries = []
    for line in host.file("/etc/fstab").content_string.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) >= 4:
            entries.append(fields)
    return entries


def _device_matches(host, fstab_src, dev):
    """Le champ device de fstab peut être un chemin (/dev/lab_vg/lab_lv ou
    /dev/mapper/lab_vg-lab_lv) ou un UUID=<uuid>."""
    if fstab_src.startswith("UUID="):
        uuid = fstab_src.split("=", 1)[1].strip('"')
        result = host.run(f"sudo blkid -o value -s UUID {dev}")
        return result.rc == 0 and uuid == result.stdout.strip()
    return _realpath(host, fstab_src) == _realpath(host, dev)


def test_vdb_existe(host):
    result = host.run(f"sudo test -b {DEVICE}")
    assert result.rc == 0, message(
        en=f"{DEVICE} must be a block device: it is db1.lab's second disk, "
        f"provisioned by the lab's infrastructure. Replay the setup (dsoxlab).",
        fr=f"{DEVICE} doit être un block device : c'est le disque secondaire de "
        f"db1.lab, provisionné par l'infra du lab. Relancez le setup (dsoxlab).",
    )


def test_pv_sur_vdb(host):
    """Le disque doit être initialisé en Physical Volume et rattaché au VG."""
    result = host.run(f"sudo pvs --noheadings -o pv_name,vg_name {DEVICE}")
    assert result.rc == 0, message(
        en=f"{DEVICE} is not an LVM Physical Volume (pvs failed: "
        f"{result.stderr.strip()}). The module that manages the Volume Group "
        f"also initialises the PV: tell it which disk to use.",
        fr=f"{DEVICE} n'est pas un Physical Volume LVM (pvs a échoué : "
        f"{result.stderr.strip()}). Le module qui gère le Volume Group sait "
        f"aussi initialiser le PV : indiquez-lui le disque à utiliser.",
    )
    assert VG in result.stdout, message(
        en=f"The {DEVICE} PV must belong to the '{VG}' VG, seen: "
        f"'{result.stdout.strip()}'.",
        fr=f"Le PV {DEVICE} doit appartenir au VG '{VG}', vu : "
        f"'{result.stdout.strip()}'.",
    )


def test_vg_existe(host):
    result = host.run(f"sudo vgs --noheadings -o vg_name {VG}")
    assert result.rc == 0, message(
        en=f"The '{VG}' Volume Group must exist (vgs failed: "
        f"{result.stderr.strip()}).",
        fr=f"Le Volume Group '{VG}' doit exister (vgs a échoué : "
        f"{result.stderr.strip()}).",
    )
    assert VG in result.stdout, message(
        en=f"Volume Group '{VG}' expected, seen: '{result.stdout.strip()}'.",
        fr=f"Volume Group '{VG}' attendu, vu : '{result.stdout.strip()}'.",
    )


def test_lv_existe_avec_taille(host):
    """Le LV doit exister dans le VG et faire environ 1 GiB."""
    result = host.run(f"sudo lvs --noheadings --units m -o lv_name,lv_size {VG}/{LV}")
    assert result.rc == 0, message(
        en=f"The '{LV}' Logical Volume must exist in the '{VG}' VG "
        f"(lvs failed: {result.stderr.strip()}).",
        fr=f"Le Logical Volume '{LV}' doit exister dans le VG '{VG}' "
        f"(lvs a échoué : {result.stderr.strip()}).",
    )
    assert LV in result.stdout, message(
        en=f"Logical Volume '{LV}' expected, seen: '{result.stdout.strip()}'.",
        fr=f"Logical Volume '{LV}' attendu, vu : '{result.stdout.strip()}'.",
    )
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*m", result.stdout, re.IGNORECASE)
    assert match, message(
        en=f"LV size not found in: '{result.stdout.strip()}'",
        fr=f"Taille du LV introuvable dans : '{result.stdout.strip()}'",
    )
    size = float(match.group(1).replace(",", "."))
    # LVM arrondit au multiple de l'extent (4 MiB par défaut) : 1 GiB = 1024 MiB.
    assert 1000 <= size <= 1050, message(
        en=f"{LV} must be about 1 GiB (1024 MiB), seen: {size:.0f} MiB. "
        f"LVM rounds to a multiple of the extent, so a slight drift is normal.",
        fr=f"{LV} doit faire environ 1 GiB (1024 MiB), vu : {size:.0f} MiB. "
        f"LVM arrondit au multiple de l'extent, une légère dérive est normale.",
    )


def test_lv_est_xfs(host):
    result = host.run(f"sudo blkid -o value -s TYPE {LV_PATH}")
    assert result.rc == 0, message(
        en=f"blkid failed on {LV_PATH}: {result.stderr.strip()}. "
        f"Does the LV exist, and does it carry a filesystem?",
        fr=f"blkid a échoué sur {LV_PATH} : {result.stderr.strip()}. "
        f"Le LV existe-t-il et porte-t-il un système de fichiers ?",
    )
    fstype = result.stdout.strip()
    assert fstype == "xfs", message(
        en=f"{LV_PATH} must be formatted as xfs, seen: '{fstype}'.",
        fr=f"{LV_PATH} doit être formaté en xfs, vu : '{fstype}'.",
    )


def test_montage_actif(host):
    mount = host.mount_point(MOUNT_POINT)
    assert mount.exists, message(
        en=f"{MOUNT_POINT} must be an active mount point (seen: nothing mounted "
        f"here). The LV must be mounted now, not merely declared.",
        fr=f"{MOUNT_POINT} doit être un point de montage actif (vu : rien de monté "
        f"ici). Le LV doit être monté maintenant, pas seulement déclaré.",
    )
    assert mount.filesystem == "xfs", message(
        en=f"{MOUNT_POINT} must be mounted as xfs, seen: '{mount.filesystem}'.",
        fr=f"{MOUNT_POINT} doit être monté en xfs, vu : '{mount.filesystem}'.",
    )
    source = host.run(f"sudo findmnt -no SOURCE {MOUNT_POINT}").stdout.strip()
    assert _realpath(host, source) == _realpath(host, LV_PATH), message(
        en=f"{MOUNT_POINT} must be backed by the {LV_PATH} LV, seen: '{source}'. "
        f"Mount the logical volume, not the {DEVICE} disk directly.",
        fr=f"{MOUNT_POINT} doit être porté par le LV {LV_PATH}, vu : '{source}'. "
        f"Montez le volume logique, pas le disque {DEVICE} directement.",
    )


def test_montage_option_noatime(host):
    options = host.run(f"sudo findmnt -no OPTIONS {MOUNT_POINT}").stdout.strip()
    assert "noatime" in options, message(
        en=f"{MOUNT_POINT} must be mounted with the noatime option, options seen: "
        f"'{options}'. Pass the mount options you want to the module.",
        fr=f"{MOUNT_POINT} doit être monté avec l'option noatime, options vues : "
        f"'{options}'. Passez les options de montage voulues au module.",
    )


def test_fstab_montage_persistant(host):
    """Le montage doit survivre au reboot : entrée xfs dans /etc/fstab."""
    entries = _fstab_entries(host)
    matches = [e for e in entries if e[1] == MOUNT_POINT]
    assert matches, message(
        en=f"No entry for {MOUNT_POINT} in /etc/fstab: the mount would disappear "
        f"at reboot. A mounted AND persistent state is reached in a single "
        f"task, with the right state of the mount module.",
        fr=f"Aucune entrée pour {MOUNT_POINT} dans /etc/fstab : le montage "
        f"disparaîtrait au reboot. Un état monté ET persistant s'obtient en "
        f"une seule tâche, avec le bon état du module de montage.",
    )
    entry = matches[0]
    assert entry[2] == "xfs", message(
        en=f"The fstab entry for {MOUNT_POINT} must declare the xfs type, "
        f"seen: '{entry[2]}'.",
        fr=f"L'entrée fstab de {MOUNT_POINT} doit déclarer le type xfs, "
        f"vu : '{entry[2]}'.",
    )
    assert _device_matches(host, entry[0], LV_PATH), message(
        en=f"The fstab entry for {MOUNT_POINT} must point at the {LV_PATH} LV "
        f"(an equivalent /dev/mapper path or a UUID are fine), seen: '{entry[0]}'.",
        fr=f"L'entrée fstab de {MOUNT_POINT} doit pointer le LV {LV_PATH} "
        f"(chemin /dev/mapper équivalent ou UUID acceptés), vu : '{entry[0]}'.",
    )
    assert "noatime" in entry[3], message(
        en=f"The fstab entry for {MOUNT_POINT} must keep the noatime option, "
        f"seen: '{entry[3]}'. Without it, the remount at boot loses the option.",
        fr=f"L'entrée fstab de {MOUNT_POINT} doit conserver l'option noatime, "
        f"vu : '{entry[3]}'. Sans elle, le remontage au reboot perd l'option.",
    )


@pytest.mark.slow
def test_montage_survit_vraiment_au_reboot():
    """Prouve la persistance en REDÉMARRANT db1, au lieu de lire /etc/fstab.

    Le lab promet (README) « le montage doit revenir tout seul après un
    reboot ». `test_fstab_montage_persistant` vérifie que l'entrée existe :
    c'est un indice, pas une preuve. Une entrée fstab syntaxiquement valide peut
    pointer un mauvais UUID, ou faire échouer le boot, et le montage ne revient
    pas. La persistance est LE piège du RHCSA/RHCE : on la prouve en
    redémarrant.

    Marqué `slow` (redémarrage ~90 s), désélectionnable avec `pytest -m 'not slow'`.
    """
    host = reboot_and_wait(TARGET_HOST)

    mount = host.mount_point(MOUNT_POINT)
    assert mount.exists, message(
        en=f"After reboot, {MOUNT_POINT} is NOT mounted again. The fstab entry may "
        "have been there, but it was not enough: wrong device, stale UUID, or "
        "an LV not activated at boot. This is exactly the scenario persistence "
        "is supposed to prevent.",
        fr=f"Après reboot, {MOUNT_POINT} n'est PAS remonté. L'entrée fstab était "
        "peut-être présente, mais elle n'a pas suffi : mauvais device, UUID "
        "obsolète, ou LV non activé au démarrage. C'est exactement le scénario "
        "que la persistance est censée prévenir.",
    )
    assert mount.filesystem == "xfs", message(
        en=f"After reboot, {MOUNT_POINT} is mounted but not as xfs "
        f"(seen: '{mount.filesystem}').",
        fr=f"Après reboot, {MOUNT_POINT} est monté mais pas en xfs "
        f"(vu : '{mount.filesystem}').",
    )
    options = host.check_output(f"findmnt -no OPTIONS {MOUNT_POINT}")
    assert "noatime" in options, message(
        en=f"After reboot, the noatime option is gone from the mount (seen: '{options}'). "
        "The automatic remount must replay ALL the options from fstab.",
        fr=f"Après reboot, l'option noatime a disparu du montage (vu : '{options}'). "
        "Le remontage automatique doit rejouer TOUTES les options de fstab.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
