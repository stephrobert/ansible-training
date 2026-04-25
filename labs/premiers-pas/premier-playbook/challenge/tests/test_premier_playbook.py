"""
Tests pytest+testinfra pour le challenge "Premier playbook" (Apache sur db1.lab:8080).

Valide la solution écrite par l'apprenant dans
labs/premiers-pas/premier-playbook/challenge/solution.yml

Lancement (depuis la racine du repo) :
    pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
"""

import pytest
import testinfra

TARGET_HOST = "db1.lab"
HTTP_PORT = 8080
EXPECTED_CONTENT = "Hello from db1.lab — Ansible RHCE 2026"


@pytest.fixture(scope="module")
def host():
    """Connexion testinfra à db1.lab via l'inventaire Ansible du lab."""
    return testinfra.get_host(
        f"ansible://{TARGET_HOST}?ansible_inventory=inventory/hosts.yml"
    )


def test_httpd_package_installed(host):
    """Le paquet httpd doit être installé sur db1.lab."""
    pkg = host.package("httpd")
    assert pkg.is_installed, "httpd n'est pas installé sur db1.lab"


def test_httpd_service_running_and_enabled(host):
    """Le service httpd doit être actif et activé au boot."""
    svc = host.service("httpd")
    assert svc.is_running, "httpd n'est pas démarré sur db1.lab"
    assert svc.is_enabled, "httpd n'est pas activé au boot sur db1.lab"


def test_port_8080_listening(host):
    """Le port 8080 doit être en listening sur 0.0.0.0."""
    sockets = host.socket.get_listening_sockets()
    listening = [s for s in sockets if f":{HTTP_PORT}" in s]
    assert listening, (
        f"Aucun service n'écoute sur le port {HTTP_PORT}. "
        f"Vérifie 'Listen {HTTP_PORT}' dans /etc/httpd/conf/httpd.conf "
        f"et le paramètre seport pour SELinux."
    )


def test_firewalld_port_8080_open(host):
    """Le port 8080 doit être autorisé dans firewalld (zone publique)."""
    cmd = host.run("firewall-cmd --list-ports --zone=public")
    assert cmd.rc == 0, f"firewall-cmd a échoué: {cmd.stderr}"
    # Le port peut être listé en "8080/tcp" ou via un service custom
    has_port = "8080/tcp" in cmd.stdout
    cmd_services = host.run("firewall-cmd --list-services --zone=public")
    has_service = any(
        f"{svc}" in cmd_services.stdout
        for svc in ["http-alt"]  # http-alt = port 8080 en service nommé
    )
    assert has_port or has_service, (
        f"Le port {HTTP_PORT} n'est pas ouvert dans firewalld. "
        f"Ports listés : {cmd.stdout.strip()}. "
        f"Services listés : {cmd_services.stdout.strip()}."
    )


def test_http_response_code_200(host):
    """La requête HTTP sur localhost:8080 doit retourner 200."""
    cmd = host.run(f"curl -sI http://localhost:{HTTP_PORT}")
    assert cmd.rc == 0, f"curl a échoué : {cmd.stderr}"
    assert "200" in cmd.stdout.split("\n")[0], (
        f"Le code HTTP retourné n'est pas 200 : {cmd.stdout.split(chr(10))[0]}"
    )


def test_homepage_content(host):
    """Le contenu de la page d'accueil doit correspondre exactement."""
    cmd = host.run(f"curl -s http://localhost:{HTTP_PORT}")
    assert cmd.rc == 0, f"curl a échoué : {cmd.stderr}"
    assert EXPECTED_CONTENT in cmd.stdout, (
        f"Le contenu de la page ne contient pas '{EXPECTED_CONTENT}'. "
        f"Contenu reçu : {cmd.stdout[:200]}"
    )
