"""Tests pytest+testinfra pour le challenge argument_specs."""

import subprocess
from pathlib import Path

import pytest

from conftest import lab_host

REPO_ROOT = Path(__file__).resolve().parents[4]
LAB_ROOT = Path(__file__).resolve().parents[2]
TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_installed(host):
    assert host.package("nginx").is_installed


def test_nginx_config_has_port_8090(host):
    """Avec argument_specs validé, nginx.conf contient 'listen 8090;'.

    Note : sur RHEL/Alma, SELinux peut bloquer le bind effectif sur 8090
    sans semanage. Pour tester l'écoute réelle, il faudrait :
      semanage port -a -t http_port_t -p tcp 8090
    Le test valide donc la CONFIG (preuve que webserver_listen_port=8090
    est bien injecté dans le template), pas le bind.
    """
    f = host.file("/etc/nginx/nginx.conf")
    assert f.exists
    assert "listen       8090" in f.content_string or "listen 8090" in f.content_string, (
        "nginx.conf doit contenir 'listen 8090' (preuve override webserver_listen_port)"
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
    """Lancer la solution avec une valeur INVALIDE pour webserver_state doit échouer."""
    result = subprocess.run(
        [
            "ansible-playbook",
            str(LAB_ROOT / "challenge/solution.yml"),
            "--extra-vars", "webserver_state=valeur_invalide",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # On attend un échec (rc != 0) avec le message de validation
    assert result.returncode != 0, "argument_specs aurait dû rejeter la valeur invalide"
    combined = result.stdout + result.stderr
    assert "valeur_invalide" in combined or "argument_errors" in combined or "must be one of" in combined, (
        f"Message de validation argument_specs absent.\n"
        f"stdout: {result.stdout[-500:]}\nstderr: {result.stderr[-500:]}"
    )
