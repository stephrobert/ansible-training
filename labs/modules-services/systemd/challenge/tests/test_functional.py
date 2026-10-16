"""Tests pytest+testinfra pour le challenge module systemd_service.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "web1.lab"

UNIT = "/etc/systemd/system/lab-marker.service"
FLAG = "/var/run/lab-marker.flag"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === chronyd (NTP, evite les conflits de port avec le nginx des autres labs) ===

def test_chrony_installed(host):
    assert host.package("chrony").is_installed, message(
        en="The chrony package is not installed. First step: "
           "ansible.builtin.dnf with state: present. A service cannot be "
           "started before its package is there.",
        fr="Le paquet chrony n'est pas installé. Première étape : "
           "ansible.builtin.dnf avec state: present. Un service ne se démarre "
           "pas avant que son paquet soit là.",
    )


def test_chronyd_running(host):
    svc = host.service("chronyd")
    assert svc.is_running, message(
        en="chronyd is not running. state: started starts it now.",
        fr="chronyd ne tourne pas. state: started le démarre maintenant.",
    )
    assert svc.is_enabled, message(
        en="chronyd is running but not enabled at boot. These are two "
           "distinct options: state: started for now, enabled: true for the "
           "next reboot. Only the second survives a restart.",
        fr="chronyd tourne mais n'est pas activé au démarrage. Ce sont deux "
           "options distinctes : state: started pour maintenant, "
           "enabled: true pour le prochain redémarrage. Seule la seconde "
           "survit à un reboot.",
    )


# === Custom unit file ===

def test_lab_marker_unit_file_exists(host):
    f = host.file(UNIT)
    assert f.exists, message(
        en=f"{UNIT} is missing. The unit file is written like any other "
           f"file, with copy and content:, before systemd can be told about "
           f"it.",
        fr=f"{UNIT} est absent. Le fichier d'unité s'écrit comme n'importe "
           f"quel fichier, avec copy et content:, avant que systemd puisse en "
           f"entendre parler.",
    )
    assert "Description=Lab Marker Service" in f.content_string, message(
        en="The unit file does not carry « Description=Lab Marker Service ». "
           "Copy the [Unit] section from the mission as it is written.",
        fr="Le fichier d'unité ne porte pas "
           "« Description=Lab Marker Service ». Recopie la section [Unit] de "
           "la mission telle qu'elle y figure.",
    )


def test_lab_marker_enabled(host):
    assert host.service("lab-marker").is_enabled, message(
        en="lab-marker is not enabled. A unit file dropped on disk is unknown "
           "to systemd until a daemon_reload: true: without it, the enable "
           "fails on « unit not found ».",
        fr="lab-marker n'est pas activé. Un fichier d'unité posé sur le "
           "disque reste inconnu de systemd jusqu'à un daemon_reload: true : "
           "sans lui, l'activation échoue sur « unit not found ».",
    )


def test_lab_marker_flag_exists(host):
    """Le service est de type oneshot RemainAfterExit — il a touch le fichier."""
    assert host.file(FLAG).exists, message(
        en=f"{FLAG} does not exist, so the service was enabled but never "
           f"started. enabled: true only arms it for the next boot: "
           f"state: started is what runs it now, and a oneshot runs its "
           f"command once then stays « active » thanks to RemainAfterExit.",
        fr=f"{FLAG} n'existe pas : le service a donc été activé mais jamais "
           f"démarré. enabled: true ne fait que l'armer pour le prochain "
           f"démarrage ; c'est state: started qui le lance maintenant, et un "
           f"oneshot exécute sa commande une fois puis reste « actif » grâce "
           f"à RemainAfterExit.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
