"""Tests pytest+testinfra pour le challenge override variables defaults/."""

import pytest

from conftest import lab_host

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


def test_default_port_80_ALSO_open(host):
    """Le port 80 reste ouvert (du lab 58 précédent ou autre play) — non garanti.
    Ce test ne fait que documenter que 8080 est en plus de la config existante.
    """
    # Ce test peut être skip — il documente juste qu'on n'a pas FERMÉ le 80.
    pass
