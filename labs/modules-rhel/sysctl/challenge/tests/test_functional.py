"""Tests pytest+testinfra pour le challenge module sysctl."""

import pytest

from conftest import lab_host, assert_idempotent, reboot_and_wait

TARGET_HOST = "db1.lab"
SYSCTL_FILE = "/etc/sysctl.d/99-rhce-lab.conf"

PARAMS = [
    ("net.ipv4.ip_forward", "1"),
    ("net.ipv4.tcp_syncookies", "1"),
    ("kernel.kptr_restrict", "2"),
    ("vm.swappiness", "10"),
]


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_sysctl_file_exists(host):
    f = host.file(SYSCTL_FILE)
    assert f.exists
    assert f.is_file


@pytest.mark.parametrize("name,value", PARAMS)
def test_param_in_file(host, name, value):
    """Le parametre est ecrit dans le fichier dedie."""
    content = host.file(SYSCTL_FILE).content_string
    assert f"{name} = {value}" in content or f"{name}={value}" in content


@pytest.mark.parametrize("name,value", PARAMS)
def test_param_runtime_value(host, name, value):
    """La valeur effective via sysctl -n correspond."""
    cmd = host.run(f"sysctl -n {name}")
    assert cmd.rc == 0
    assert cmd.stdout.strip() == value, \
        f"{name} attendu {value}, runtime : {cmd.stdout.strip()}"


@pytest.mark.slow
def test_parametres_survivent_vraiment_au_reboot():
    """Prouve la persistance en REDÉMARRANT db1, au lieu de lire le fichier.

    `test_param_runtime_value` prouve que la valeur est active APRÈS avoir posé
    le fichier ET rechargé (`sysctl -p`). Mais un apprenant peut poser la valeur
    à la main (`sysctl -w`) sans l'écrire dans /etc/sysctl.d/ : le runtime est
    bon, et tout est perdu au reboot. La persistance d'un paramètre noyau se
    prouve en redémarrant et en relisant `sysctl -n`.

    Marqué `slow` (redémarrage ~90 s), désélectionnable avec `pytest -m 'not slow'`.
    """
    host = reboot_and_wait(TARGET_HOST)
    for name, value in PARAMS:
        actuel = host.check_output(f"sysctl -n {name}")
        assert actuel == value, (
            f"Après reboot, {name} vaut '{actuel}', attendu '{value}'. La valeur "
            f"n'a pas été rechargée : elle n'est pas dans /etc/sysctl.d/, ou le "
            "fichier n'y est pas lu au démarrage. Un `sysctl -w` ne survit pas."
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
