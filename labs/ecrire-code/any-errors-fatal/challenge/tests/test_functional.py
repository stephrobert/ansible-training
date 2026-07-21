"""Tests pytest+testinfra pour le challenge any_errors_fatal.

Ce test désactive le replay automatique du conftest : il joue lui-même le
playbook deux fois. D'abord un run "incident" où web1 échoue sur le
contrôle de santé : any_errors_fatal doit arrêter le play PARTOUT, et la
preuve est un état négatif (la release n'est posée sur AUCUN hôte, pas
même web2 qui n'a pourtant pas planté). Puis un run nominal qui converge.
"""

import subprocess

import pytest

# REPO_ROOT vient de conftest : le compter en parents[] depuis ce fichier donnait
# labs/ (un cran trop bas), donc un cwd sans ansible.cfg (ni inventaire, ni clé).
from conftest import REPO_ROOT, lab_host, lab_playbook, assert_idempotent

# Ce module orchestre lui-même ses runs : le marqueur désactive le replay
# POUR CE MODULE. Poser os.environ["LAB_NO_REPLAY"] ici le désactivait pour
# toute la session, dès la collecte, y compris pour les labs voisins.
pytestmark = pytest.mark.no_replay


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


def _reset_markers():
    """Supprime les marqueurs du lab sur les 2 webservers."""
    subprocess.run(
        [
            "ansible", "webservers", "-b",
            "-m", "ansible.builtin.shell",
            "-a", "rm -f /tmp/anyfatal-*.txt",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )


def _run_solution(extra_args=None):
    """Joue la solution (apprenant, sinon référence) et retourne le
    CompletedProcess (sans lever).

    La référence du formateur est chiffrée : sans vault_args, ansible-playbook
    ne lit que du $ANSIBLE_VAULT.
    """
    playbook, vault_args = lab_playbook(__file__)
    cmd = ["ansible-playbook", *vault_args, str(playbook)]
    cmd += extra_args or []
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def _step1(host):
    return f"/tmp/anyfatal-step1-{host}.txt"


def _release(host):
    return f"/tmp/anyfatal-release-{host}.txt"


def test_incident_arrete_le_play_partout(web1, web2):
    """web1 échoue au contrôle de santé → aucun hôte ne pose la release.

    C'est LA preuve d'any_errors_fatal : web2 n'a échoué sur rien, mais le
    play s'est arrêté avant sa tâche d'activation. Sans le mot-clé, web2
    aurait posé sa release et ce test échouerait.
    """
    _reset_markers()
    result = _run_solution(["-e", "fail_host=web1.lab"])

    assert result.returncode != 0, (
        "Le run incident (-e fail_host=web1.lab) doit sortir en erreur : le "
        "contrôle de santé est censé échouer sur web1. S'il réussit, la tâche "
        "command /bin/false ou son when: manque.\n"
        f"stdout: {result.stdout[-1500:]}"
    )

    assert web1.file(_step1("web1.lab")).exists, (
        "L'étape 1 doit être posée sur web1 AVANT le contrôle de santé."
    )
    assert web2.file(_step1("web2.lab")).exists, (
        "L'étape 1 doit être posée sur web2 AVANT le contrôle de santé."
    )

    assert not web1.file(_release("web1.lab")).exists, (
        "web1 a échoué au contrôle de santé : il ne doit PAS avoir activé la release."
    )
    assert not web2.file(_release("web2.lab")).exists, (
        "web2 a posé sa release alors que web1 a échoué : le play a continué "
        "au lieu de s'arrêter partout. C'est le comportement par défaut "
        "d'Ansible : il manque any_errors_fatal: true au niveau du play."
    )


def test_run_nominal_converge(web1, web2):
    """Sans hôte en échec, les 2 webservers reçoivent étape 1 + release."""
    _reset_markers()
    result = _run_solution()

    assert result.returncode == 0, (
        "Le run nominal (sans -e) doit réussir : fail_host vaut 'none' par "
        "défaut et ne doit matcher aucun hôte.\n"
        f"stdout: {result.stdout[-1500:]}\nstderr: {result.stderr[-500:]}"
    )

    for host, target in (("web1.lab", web1), ("web2.lab", web2)):
        step1 = target.file(_step1(host))
        assert step1.exists, f"{_step1(host)} absent sur {host}"
        assert f"step1 OK on {host}" in step1.content_string
        assert step1.mode == 0o644, (
            f"L'étape 1 doit être posée en mode 0644 sur {host} "
            f"(mode actuel : {oct(step1.mode)})."
        )

        release = target.file(_release(host))
        assert release.exists, f"{_release(host)} absent sur {host}"
        assert f"release OK on {host}" in release.content_string
        assert release.mode == 0o644


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
