"""Tests pytest+testinfra pour le challenge lineinfile (sshd hardening)."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def _sshd_effectif(host) -> dict:
    """La configuration que sshd CHARGE réellement, via `sshd -T`.

    Les tests lisaient /etc/ssh/sshd_config en cherchant une sous-chaîne. Une
    ligne restée COMMENTÉE les satisfaisait donc : `#MaxAuthTries 3` contient
    « MaxAuthTries 3 ». Le fichier peut aussi être syntaxiquement valide et
    ignoré (Include, Match, dernière occurrence qui gagne).

    `sshd -T` est le critère que le challenge/README annonce depuis toujours
    (ligne 18) sans que rien ne l'exécute. Il rend la config effective, en
    minuscules, une directive par ligne.
    """
    sortie = host.check_output("sshd -T")
    conf = {}
    for ligne in sortie.splitlines():
        if " " in ligne:
            cle, _, valeur = ligne.partition(" ")
            conf.setdefault(cle.lower(), []).append(valeur.strip())
    return conf


def _sshd_config(host) -> str:
    return host.file("/etc/ssh/sshd_config").content_string




def test_permit_root_login_disabled(host):
    content = _sshd_config(host)
    assert "PermitRootLogin no" in content, (
        "sshd_config doit contenir 'PermitRootLogin no' (lineinfile + regexp + validate)."
    )
    # La ligne commentée d'origine ne doit plus être active
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("PermitRootLogin"):
            assert stripped == "PermitRootLogin no", (
                f"Une seule ligne PermitRootLogin attendue, trouvé : {stripped}"
            )


def test_max_auth_tries_3(host):
    """MaxAuthTries doit valoir 3 dans la config EFFECTIVE, pas dans un commentaire."""
    conf = _sshd_effectif(host)
    assert conf.get("maxauthtries") == ["3"], (
        "sshd doit charger « MaxAuthTries 3 ». Vu dans `sshd -T` : "
        f"{conf.get('maxauthtries', 'directive absente')}.\n"
        "Une ligne commentée ne compte pas : c'est la config chargée qui fait foi."
    )


def test_allow_users_ansible(host):
    """AllowUsers doit être EFFECTIF et porter le compte du lab."""
    conf = _sshd_effectif(host)
    autorises = " ".join(conf.get("allowusers", [])).split()
    assert autorises == ["ansible"], (
        "sshd doit charger « AllowUsers ansible » : le compte de service par "
        f"lequel l'automatisation se connecte. Vu dans `sshd -T` : "
        f"{autorises or 'directive absente'}.\n"
        "Attention : restreindre à un autre compte (p. ex. « student ») VERROUILLE "
        "la connexion Ansible, plus personne ne peut piloter la VM."
    )


def test_sshd_config_valide(host):
    """sshd -t doit retourner 0 (config syntactiquement valide)."""
    cmd = host.run("sudo sshd -t")
    assert cmd.rc == 0, (
        f"sshd_config invalide après modifs : {cmd.stderr}. "
        f"Ajoutez `validate: 'sshd -t -f %s'` à chaque tâche lineinfile."
    )


def test_sshd_running(host):
    svc = host.service("sshd")
    assert svc.is_running, "Le service sshd doit être actif après les modifs."


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
