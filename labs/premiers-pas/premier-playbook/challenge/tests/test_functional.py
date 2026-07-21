"""
Tests pytest+testinfra pour le challenge "Premier playbook" (nginx sur db1.lab:8888).

Valide la solution écrite par l'apprenant dans
labs/premiers-pas/premier-playbook/challenge/solution.yml

Lancement (depuis la racine du repo) :
    pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
"""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
HTTP_PORT = 8888
EXPECTED_CONTENT = "Hello from db1.lab — Ansible RHCE 2026"


@pytest.fixture(scope="module")
def host():
    """Connexion testinfra à db1.lab via SSH direct (cf. conftest.py racine)."""
    return lab_host(TARGET_HOST)


def test_nginx_package_installed(host):
    """Le paquet nginx doit être installé sur db1.lab."""
    pkg = host.package("nginx")
    assert pkg.is_installed, "nginx n'est pas installé sur db1.lab"


def test_nginx_service_running_and_enabled(host):
    """Le service nginx doit être actif et activé au boot."""
    svc = host.service("nginx")
    assert svc.is_running, "nginx n'est pas démarré sur db1.lab"
    assert svc.is_enabled, "nginx n'est pas activé au boot sur db1.lab"


def test_port_8888_listening(host):
    """Le port 8888 doit être en listening."""
    sockets = host.socket.get_listening_sockets()
    listening = [s for s in sockets if f":{HTTP_PORT}" in s]
    assert listening, (
        f"Aucun service n'écoute sur le port {HTTP_PORT}. "
        f"Vérifie 'listen {HTTP_PORT};' dans /etc/nginx/nginx.conf "
        f"et le paramètre seport pour SELinux."
    )


def test_selinux_port_8888_labelled(host):
    """Le port 8888 doit porter l'étiquette SELinux http_port_t.

    C'est la preuve directe de la tâche seport. Sur RHEL, nginx tourne dans le
    domaine SELinux httpd_t, que la politique n'autorise à se lier qu'aux
    types http_port_t et http_cache_port_t. 8888 n'est ni l'un ni l'autre par
    défaut : sans étiquette, le bind échoue.

    L'étiquette est PERSISTANTE : le setup.yaml du lab la retire avant chaque
    passage, sinon un run précédent suffirait à faire passer un playbook qui
    aurait oublié la tâche seport.
    """
    cmd = host.run("semanage port -l | grep '^http_port_t'")
    assert cmd.rc == 0, "Impossible de lire les ports http_port_t (semanage)."
    assert str(HTTP_PORT) in cmd.stdout, (
        f"Le port {HTTP_PORT} n'est pas étiqueté http_port_t.\n"
        f"Vu : {cmd.stdout.strip()}\n"
        "SELinux étant en Enforcing, nginx ne peut pas se lier à un port qui "
        "n'est pas couvert par la politique HTTP : utilisez "
        "community.general.seport."
    )


def test_firewalld_port_8888_open(host):
    """Le port 8888 doit être autorisé dans firewalld (zone publique)."""
    cmd = host.run("firewall-cmd --list-ports --zone=public")
    assert cmd.rc == 0, f"firewall-cmd a échoué: {cmd.stderr}"
    assert f"{HTTP_PORT}/tcp" in cmd.stdout, (
        f"Le port {HTTP_PORT} n'est pas ouvert dans firewalld. "
        f"Ports listés : {cmd.stdout.strip()}."
    )


def test_http_response_code_200(host):
    """La requête HTTP sur localhost:8888 doit retourner 200."""
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


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
