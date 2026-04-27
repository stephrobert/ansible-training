"""Tests pytest+testinfra pour le challenge rôle httpd-server."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_httpd_package_installed(host):
    """Le paquet httpd est installé."""
    assert host.package("httpd").is_installed


def test_httpd_service_running(host):
    """Le service httpd est démarré et activé au boot."""
    svc = host.service("httpd")
    assert svc.is_running, "httpd doit être running"
    assert svc.is_enabled, "httpd doit être enabled (démarrage auto)"


def test_port_80_listening(host):
    """Le port 80 est en listening."""
    assert host.socket("tcp://0.0.0.0:80").is_listening or host.socket("tcp://:::80").is_listening


def test_firewalld_http_open(host):
    """Le service HTTP est ouvert dans firewalld zone publique."""
    cmd = host.run("firewall-cmd --zone=public --query-service=http")
    assert cmd.rc == 0, f"firewalld http non ouvert: {cmd.stdout} {cmd.stderr}"


def test_http_returns_200(host):
    """Une requête HTTP locale retourne 200."""
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost/")
    assert cmd.stdout.strip() == "200", f"Code HTTP attendu 200, reçu: {cmd.stdout}"
