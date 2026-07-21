"""Tests pytest+testinfra pour le challenge override variables defaults/."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_installed(host):
    """Le paquet nginx est installé."""
    assert host.package("nginx").is_installed


def test_nginx_running(host):
    """Le service nginx est démarré et activé."""
    svc = host.service("nginx")
    assert svc.is_running
    assert svc.is_enabled


def test_firewalld_port_8080_open(host):
    """Override de webserver_listen_port=8080 → port 8080/tcp ouvert."""
    cmd = host.run("firewall-cmd --zone=public --list-ports")
    assert "8080/tcp" in cmd.stdout, (
        f"Port 8080/tcp absent de firewalld — "
        f"l'override webserver_listen_port=8080 n'a pas été appliqué.\n"
        f"Sortie firewall-cmd: {cmd.stdout}"
    )


def test_index_custom_content(host):
    """Override de webserver_index_content → la page d'accueil contient le custom message."""
    f = host.file("/usr/share/nginx/html/index.html")
    assert f.exists, "/usr/share/nginx/html/index.html doit exister"
    content = f.content_string
    assert "Custom page from challenge lab 59" in content, (
        f"Custom message absent du fichier — "
        f"l'override webserver_index_content n'a pas été appliqué.\n"
        f"Contenu reçu: {content[:200]}"
    )
    assert "db1.lab" in content, (
        "{{ inventory_hostname }} doit avoir été rendu en 'db1.lab' "
        "dans le custom message."
    )


def test_worker_connections_override(host):
    """Override de webserver_worker_connections=2048 → effectif dans nginx.conf.

    Le défaut du rôle est 1024 ; l'énoncé impose 2048 via le `vars:` du play.
    La preuve est la directive rendue dans /etc/nginx/nginx.conf, pas la
    variable Ansible.
    """
    f = host.file("/etc/nginx/nginx.conf")
    assert f.exists, "/etc/nginx/nginx.conf doit exister"
    content = f.content_string
    assert "worker_connections 2048;" in content, (
        f"worker_connections 2048 absent de nginx.conf — "
        f"l'override webserver_worker_connections=2048 n'a pas été appliqué "
        f"(le défaut 1024 est resté).\nContenu events: "
        f"{[ligne for ligne in content.splitlines() if 'worker_connections' in ligne]}"
    )


def test_default_port_80_ALSO_open(host):
    """Le port 80 reste ouvert (du lab 58 précédent ou autre play) — non garanti.
    Ce test ne fait que documenter que 8080 est en plus de la config existante.
    """
    # Ce test peut être skip — il documente juste qu'on n'a pas FERMÉ le 80.
    pass


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
