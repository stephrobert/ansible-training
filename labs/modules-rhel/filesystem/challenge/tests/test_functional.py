"""Tests pytest+testinfra pour le challenge filesystem (swap + xfs sur /dev/vdb).

Pré-requis : /dev/vdb1 et /dev/vdb2 existent (partitions posées par le
setup.yaml du lab sur le disque secondaire réel de db1.lab). Lancez le lab
via dsoxlab avant de jouer votre solution.
"""

import pytest

from conftest import assert_idempotent, lab_host, message, reboot_and_wait

TARGET_HOST = "db1.lab"
SWAP_PART = "/dev/vdb1"
XFS_PART = "/dev/vdb2"
MOUNT_POINT = "/mnt/data"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def _blkid_value(host, tag, dev):
    result = host.run(f"sudo blkid -o value -s {tag} {dev}")
    assert result.rc == 0, message(
        en=f"blkid failed on {dev}: {result.stderr}. "
        f"Does the device exist, and does it carry a filesystem?",
        fr=f"blkid a échoué sur {dev} : {result.stderr}. "
        f"Le device existe-t-il et porte-t-il un système de fichiers ?",
    )
    return result.stdout.strip()


def _fstab_entries(host):
    """Lignes utiles de /etc/fstab, découpées en champs."""
    content = host.file("/etc/fstab").content_string
    entries = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) >= 3:
            entries.append(fields)
    return entries


def _device_matches(host, fstab_src, dev):
    """Le champ device de fstab peut être le chemin ou UUID=<uuid du device>."""
    if fstab_src == dev:
        return True
    if fstab_src.startswith("UUID="):
        return fstab_src.split("=", 1)[1].strip('"') == _blkid_value(host, "UUID", dev)
    return False


def test_partitions_presentes(host):
    for part in (SWAP_PART, XFS_PART):
        result = host.run(f"sudo test -b {part}")
        assert result.rc == 0, message(
            en=f"{part} must be a block device: the 2 partitions of /dev/vdb are "
            f"laid down by the lab's setup. Replay the setup (dsoxlab).",
            fr=f"{part} doit être un block device : les 2 partitions de /dev/vdb "
            f"sont posées par le setup du lab. Relancez le setup (dsoxlab).",
        )


def test_vdb1_est_swap(host):
    fstype = _blkid_value(host, "TYPE", SWAP_PART)
    assert fstype == "swap", message(
        en=f"{SWAP_PART} must be formatted as swap, seen: '{fstype}'. "
        f"The filesystem module can run mkswap too.",
        fr=f"{SWAP_PART} doit être formaté en swap, vu : '{fstype}'. "
        f"Le module de création de systèmes de fichiers sait aussi faire mkswap.",
    )


def test_vdb2_est_xfs(host):
    fstype = _blkid_value(host, "TYPE", XFS_PART)
    assert fstype == "xfs", message(
        en=f"{XFS_PART} must be formatted as xfs, seen: '{fstype}'.",
        fr=f"{XFS_PART} doit être formaté en xfs, vu : '{fstype}'.",
    )


def test_swap_actif(host):
    result = host.run("sudo swapon --show=NAME --noheadings")
    active = result.stdout.split()
    assert SWAP_PART in active, message(
        en=f"{SWAP_PART} must appear in `swapon --show`, seen: {active or 'no active swap'}. "
        f"The swap must be enabled right away, not merely declared.",
        fr=f"{SWAP_PART} doit apparaître dans `swapon --show`, vu : {active or 'aucun swap actif'}. "
        f"Le swap doit être activé immédiatement, pas seulement déclaré.",
    )


def test_montage_actif(host):
    mount = host.mount_point(MOUNT_POINT)
    assert mount.exists, message(
        en=f"{MOUNT_POINT} must be an active mount point "
        f"(seen: nothing mounted here). Mount {XFS_PART} on it.",
        fr=f"{MOUNT_POINT} doit être un point de montage actif "
        f"(vu : rien de monté ici). Montez {XFS_PART} dessus.",
    )
    assert mount.filesystem == "xfs", message(
        en=f"{MOUNT_POINT} must be mounted as xfs, seen: '{mount.filesystem}'.",
        fr=f"{MOUNT_POINT} doit être monté en xfs, vu : '{mount.filesystem}'.",
    )
    assert mount.device == XFS_PART, message(
        en=f"{MOUNT_POINT} must be backed by {XFS_PART}, seen: '{mount.device}'.",
        fr=f"{MOUNT_POINT} doit être porté par {XFS_PART}, vu : '{mount.device}'.",
    )


def test_fstab_montage_persistant(host):
    """Le montage doit survivre au reboot : entrée xfs dans /etc/fstab."""
    entries = _fstab_entries(host)
    matches = [e for e in entries if e[1] == MOUNT_POINT]
    assert matches, message(
        en=f"No entry for {MOUNT_POINT} in /etc/fstab: the mount would disappear "
        f"at reboot. A mounted AND persistent state is reached in a single "
        f"task, with the right module.",
        fr=f"Aucune entrée pour {MOUNT_POINT} dans /etc/fstab : le montage "
        f"disparaîtrait au reboot. Un état monté ET persistant s'obtient en "
        f"une seule tâche avec le bon module.",
    )
    entry = matches[0]
    assert entry[2] == "xfs", message(
        en=f"The fstab entry for {MOUNT_POINT} must declare the xfs type, "
        f"seen: '{entry[2]}'.",
        fr=f"L'entrée fstab de {MOUNT_POINT} doit déclarer le type xfs, "
        f"vu : '{entry[2]}'.",
    )
    assert _device_matches(host, entry[0], XFS_PART), message(
        en=f"The fstab entry for {MOUNT_POINT} must point at {XFS_PART} "
        f"(or its UUID), seen: '{entry[0]}'.",
        fr=f"L'entrée fstab de {MOUNT_POINT} doit pointer {XFS_PART} "
        f"(ou son UUID), vu : '{entry[0]}'.",
    )


def test_fstab_swap_persistant(host):
    """Le swap doit survivre au reboot : entrée swap dans /etc/fstab."""
    entries = _fstab_entries(host)
    swap_entries = [e for e in entries if e[2] == "swap"]
    assert swap_entries, message(
        en="No swap entry in /etc/fstab: the swap would disappear at reboot. "
        "Declare it with 'none' as its mount point.",
        fr="Aucune entrée de type swap dans /etc/fstab : le swap disparaîtrait "
        "au reboot. Déclarez-le avec un point de montage 'none'.",
    )
    assert any(_device_matches(host, e[0], SWAP_PART) for e in swap_entries), message(
        en=f"The swap entry in /etc/fstab must point at {SWAP_PART} (or its UUID), "
        f"seen: {[e[0] for e in swap_entries]}.",
        fr=f"L'entrée swap de /etc/fstab doit pointer {SWAP_PART} (ou son UUID), "
        f"vu : {[e[0] for e in swap_entries]}.",
    )


@pytest.mark.slow
def test_montage_et_swap_survivent_vraiment_au_reboot():
    """Prouve la persistance en REDÉMARRANT db1, au lieu de lire /etc/fstab.

    Le lab promet (README) que le montage ET le swap « survivent au reboot ».
    `test_fstab_montage_persistant` et `test_fstab_swap_persistant` vérifient que
    les entrées existent : c'est un indice, pas une preuve. Une entrée peut
    pointer un mauvais UUID, ou le swap ne pas être réactivé au démarrage. La
    persistance est LE piège du RHCSA : on la prouve en redémarrant.

    Marqué `slow` (redémarrage ~90 s), désélectionnable avec `pytest -m 'not slow'`.
    """
    host = reboot_and_wait(TARGET_HOST)

    # Le montage xfs doit être revenu tout seul.
    mount = host.mount_point(MOUNT_POINT)
    assert mount.exists, message(
        en=f"After reboot, {MOUNT_POINT} is NOT mounted again. The fstab entry may "
        "have been there, but it was not enough (wrong device or stale UUID). "
        "This is the scenario persistence is supposed to prevent.",
        fr=f"Après reboot, {MOUNT_POINT} n'est PAS remonté. L'entrée fstab était "
        "peut-être présente, mais elle n'a pas suffi (mauvais device ou UUID "
        "obsolète). C'est le scénario que la persistance est censée prévenir.",
    )
    assert mount.filesystem == "xfs", message(
        en=f"After reboot, {MOUNT_POINT} is mounted but not as xfs "
        f"(seen: '{mount.filesystem}').",
        fr=f"Après reboot, {MOUNT_POINT} est monté mais pas en xfs "
        f"(vu : '{mount.filesystem}').",
    )

    # Le swap doit être réactivé tout seul.
    swaps = host.check_output("swapon --show=NAME --noheadings")
    reel = host.check_output(f"readlink -f {SWAP_PART}")
    actifs = [host.check_output(f"readlink -f {s}") for s in swaps.split() if s]
    assert reel in actifs, message(
        en=f"After reboot, {SWAP_PART} is NOT re-enabled as swap (active swaps: "
        f"{swaps or 'none'}). A swap entry in fstab is not enough if it points "
        "at the wrong device: swapon claims it at boot.",
        fr=f"Après reboot, {SWAP_PART} n'est PAS réactivé comme swap (swaps actifs "
        f": {swaps or 'aucun'}). Une entrée swap dans fstab ne suffit pas si "
        "elle pointe le mauvais device : swapon la réclame au démarrage.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
