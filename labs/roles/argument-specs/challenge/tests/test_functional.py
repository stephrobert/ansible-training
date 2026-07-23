"""Tests pytest+testinfra pour le challenge argument_specs."""

import os
import subprocess
from pathlib import Path

import pytest

from conftest import lab_host, lab_playbook, assert_idempotent, REPO_ROOT

LAB_ROOT = Path(__file__).resolve().parents[2]
TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_installed(host):
    assert host.package("nginx").is_installed


def test_nginx_ecoute_reellement_sur_8090(host):
    """Preuve d'état : nginx tourne ET écoute vraiment sur 8090.

    Un nginx.conf contenant « listen 8090 » ne prouve rien. Le port 8090 n'est
    pas couvert par http_port_t (80, 81, 443, 488, 8008, 8009, 8443, 9000) :
    tant que le rôle ne l'étiquette pas (community.general.seport), SELinux
    refuse le bind et nginx meurt sur « bind() to 0.0.0.0:8090 failed
    (13: Permission denied) », fichier de conf parfait à l'appui.
    C'est donc l'écoute effective qu'on vérifie, pas la configuration.
    """
    svc = host.service("nginx")
    assert svc.is_running, (
        "nginx n'est pas démarré. Cause la plus probable : le port d'écoute "
        "n'est pas étiqueté côté SELinux (le rôle doit poser seport avec "
        "setype http_port_t AVANT de démarrer le service)."
    )
    assert host.socket("tcp://0.0.0.0:8090").is_listening, (
        "nginx ne répond sur aucun socket 0.0.0.0:8090 : soit "
        "webserver_listen_port=8090 n'a pas été injecté dans le template, "
        "soit SELinux a refusé le bind sur ce port."
    )


def test_index_contains_validation_message(host):
    f = host.file("/usr/share/nginx/html/index.html")
    assert f.exists
    assert "argument_specs validés" in f.content_string


def test_argument_specs_file_present():
    """meta/argument_specs.yml existe dans le rôle (mandatory pour validation auto)."""
    spec_path = LAB_ROOT / "roles/webserver/meta/argument_specs.yml"
    assert spec_path.exists(), f"Fichier {spec_path} manquant"
    content = spec_path.read_text()
    assert "argument_specs:" in content
    assert "main:" in content


def test_invalid_choice_makes_play_fail():
    """Lancer la solution avec une valeur INVALIDE pour webserver_state doit échouer.

    Le playbook est résolu par lab_playbook (travail de l'apprenant s'il existe,
    sinon référence chiffrée du formateur). Coder en dur challenge/solution.yml
    ne tournait que chez l'apprenant : en mode formateur le fichier n'existe pas
    et le test « passait » son premier assert sur un « could not be found »,
    sans jamais exercer argument_specs.
    """
    playbook, vault_args = lab_playbook(__file__)
    # La référence vit dans solution/, loin des rôles du lab : sans ce chemin,
    # le play échouerait sur « the role 'webserver' was not found », ce qui
    # ferait passer le test pour une raison étrangère à argument_specs.
    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = str(LAB_ROOT / "roles")
    result = subprocess.run(
        [
            "ansible-playbook",
            *vault_args,
            str(playbook),
            "--extra-vars", "webserver_state=valeur_invalide",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    # On attend un échec (rc != 0) avec le message de validation
    assert result.returncode != 0, "argument_specs aurait dû rejeter la valeur invalide"
    combined = result.stdout + result.stderr
    assert "valeur_invalide" in combined or "argument_errors" in combined or "must be one of" in combined, (
        f"Message de validation argument_specs absent.\n"
        f"stdout: {result.stdout[-500:]}\nstderr: {result.stderr[-500:]}"
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
