"""
Tests pytest+testinfra pour le challenge "Plays et tasks" (httpd sur db1.lab).

Valide la solution écrite par l'apprenant dans
labs/05-ecrire-code-plays-et-tasks/challenge/solution.yml

Lancement (depuis la racine du repo) :
    pytest -v labs/05-ecrire-code-plays-et-tasks/challenge/tests/
"""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
EXPECTED_CONTENT = "Challenge OK from db1.lab"
PREDEPLOY_FILE = "/tmp/challenge-predeploy-db1.txt"
POSTDEPLOY_FILE = "/tmp/challenge-postdeploy-db1.txt"


@pytest.fixture(scope="module")
def host():
    """Connexion testinfra à db1.lab via SSH direct (cf. conftest.py racine)."""
    return lab_host(TARGET_HOST)


def test_predeploy_marker_exists(host):
    """Le fichier marqueur pre_tasks doit exister et contenir le hostname."""
    f = host.file(PREDEPLOY_FILE)
    assert f.exists, f"Le fichier {PREDEPLOY_FILE} n'existe pas (pre_tasks pas exécuté)."
    assert "db1" in f.content_string, (
        f"{PREDEPLOY_FILE} ne contient pas le hostname (le pre_tasks "
        f"doit interpoler {{ inventory_hostname }})."
    )


def test_httpd_package_installed(host):
    """Le paquet httpd doit être installé."""
    assert host.package("httpd").is_installed, "httpd n'est pas installé"


def test_httpd_running_and_enabled(host):
    """Le service httpd doit être actif et enabled au boot."""
    svc = host.service("httpd")
    assert svc.is_running, "httpd n'est pas démarré"
    assert svc.is_enabled, "httpd n'est pas enabled au boot"


def test_port_80_listening(host):
    """Le port 80 doit être en listening."""
    sockets = host.socket.get_listening_sockets()
    assert any(":80" in s for s in sockets), (
        f"Aucun service n'écoute sur le port 80. Sockets : {sockets}"
    )


def test_firewalld_http_open(host):
    """Le service http doit être autorisé dans firewalld."""
    cmd = host.run("firewall-cmd --list-services --zone=public")
    assert cmd.rc == 0, f"firewall-cmd échec : {cmd.stderr}"
    assert "http" in cmd.stdout, (
        f"Le service http n'est pas ouvert dans firewalld. "
        f"Services listés : {cmd.stdout.strip()}"
    )


def test_http_response_200_with_expected_content(host):
    """curl http://localhost retourne 200 avec le contenu attendu."""
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost")
    assert cmd.stdout == "200", f"Code HTTP attendu 200, reçu : {cmd.stdout}"

    cmd_content = host.run("curl -s http://localhost")
    assert EXPECTED_CONTENT in cmd_content.stdout, (
        f"Le contenu de la page ne contient pas '{EXPECTED_CONTENT}'. "
        f"Reçu : {cmd_content.stdout[:300]}"
    )


def test_postdeploy_marker_exists(host):
    """Le fichier marqueur post_tasks doit exister et contenir le hostname."""
    f = host.file(POSTDEPLOY_FILE)
    assert f.exists, f"Le fichier {POSTDEPLOY_FILE} n'existe pas (post_tasks pas exécuté)."
    assert "db1" in f.content_string, (
        f"{POSTDEPLOY_FILE} ne contient pas le hostname (le post_tasks "
        f"doit interpoler {{ inventory_hostname }})."
    )


def test_predeploy_before_postdeploy(host):
    """L'ordre pre_tasks → post_tasks doit être respecté (mtime croissant)."""
    pre = host.file(PREDEPLOY_FILE)
    post = host.file(POSTDEPLOY_FILE)
    assert pre.mtime < post.mtime, (
        f"Le fichier predeploy ({pre.mtime}) doit être antérieur "
        f"au fichier postdeploy ({post.mtime}). pre_tasks doit s'exécuter "
        f"AVANT post_tasks."
    )
