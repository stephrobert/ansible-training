"""Tests pytest+testinfra pour le challenge module sysctl.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message, reboot_and_wait

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
    assert f.exists, message(
        en=f"{SYSCTL_FILE} is missing. The module's sysctl_file: option says "
           f"where to write; without it, the parameter goes into "
           f"/etc/sysctl.conf, which the mission does not ask for.",
        fr=f"{SYSCTL_FILE} est absent. L'option sysctl_file: du module dit où "
           f"écrire ; sans elle, le paramètre va dans /etc/sysctl.conf, que "
           f"la mission ne demande pas.",
    )
    assert f.is_file, message(
        en=f"{SYSCTL_FILE} is not an ordinary file.",
        fr=f"{SYSCTL_FILE} n'est pas un fichier ordinaire.",
    )


@pytest.mark.parametrize("name,value", PARAMS)
def test_param_in_file(host, name, value):
    """Le parametre est ecrit dans le fichier dedie."""
    content = host.file(SYSCTL_FILE).content_string
    assert f"{name} = {value}" in content or f"{name}={value}" in content, message(
        en=f"{name} is not written in {SYSCTL_FILE}. A value set with "
           f"sysctl -w is active now and lost at the next reboot: only the "
           f"file makes it persistent.",
        fr=f"{name} n'est pas écrit dans {SYSCTL_FILE}. Une valeur posée avec "
           f"sysctl -w est active maintenant et perdue au prochain "
           f"redémarrage : seul le fichier la rend persistante.",
    )


@pytest.mark.parametrize("name,value", PARAMS)
def test_param_runtime_value(host, name, value):
    """La valeur effective via sysctl -n correspond."""
    cmd = host.run(f"sysctl -n {name}")
    assert cmd.rc == 0, message(
        en=f"sysctl does not know the {name} parameter: {cmd.stderr.strip()}",
        fr=f"sysctl ne connaît pas le paramètre {name} : {cmd.stderr.strip()}",
    )
    assert cmd.stdout.strip() == value, message(
        en=f"{name} is {cmd.stdout.strip()} at runtime, expected {value}. "
           f"Written in the file but not active means the module wrote "
           f"without reloading: reload: true is its default, so check it was "
           f"not turned off.",
        fr=f"{name} vaut {cmd.stdout.strip()} à l'exécution, attendu {value}. "
           f"Écrit dans le fichier mais inactif signale un module qui a écrit "
           f"sans recharger : reload: true est son défaut, vérifie qu'il n'a "
           f"pas été désactivé.",
    )


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
        assert actuel == value, message(
            en=f"After reboot, {name} is '{actuel}', expected '{value}'. The "
               f"value was not reloaded: it is not in /etc/sysctl.d/, or the "
               f"file is not read at boot. A sysctl -w does not survive.",
            fr=f"Après reboot, {name} vaut '{actuel}', attendu '{value}'. La "
               f"valeur n'a pas été rechargée : elle n'est pas dans "
               f"/etc/sysctl.d/, ou le fichier n'y est pas lu au démarrage. "
               f"Un sysctl -w ne survit pas.",
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
