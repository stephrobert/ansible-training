"""
Tests pytest+testinfra pour le challenge "Handlers" (httpd avec deux handlers).
"""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
HTTPD_CONF = "/etc/httpd/conf/httpd.conf"
JOURNAL = "/var/log/ansible-handlers.log"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_httpd_running(host):
    assert host.package("httpd").is_installed
    svc = host.service("httpd")
    assert svc.is_running, "httpd doit être running"
    assert svc.is_enabled, "httpd doit être enabled"


def test_servertokens_configured(host):
    """httpd.conf doit contenir 'ServerTokens Prod'."""
    f = host.file(HTTPD_CONF)
    assert f.exists
    assert "ServerTokens Prod" in f.content_string, (
        f"{HTTPD_CONF} doit contenir 'ServerTokens Prod'"
    )


def test_serversignature_off(host):
    """httpd.conf doit contenir 'ServerSignature Off'."""
    f = host.file(HTTPD_CONF)
    assert "ServerSignature Off" in f.content_string, (
        f"{HTTPD_CONF} doit contenir 'ServerSignature Off'"
    )


def test_journal_exists_with_entry(host):
    """Le second handler 'Notifier journal local' a posé une entrée dans le journal."""
    f = host.file(JOURNAL)
    assert f.exists, (
        f"{JOURNAL} n'existe pas — le handler 'Notifier journal local' "
        f"ne s'est pas déclenché"
    )
    assert "Config httpd modifiée" in f.content_string, (
        f"{JOURNAL} ne contient pas l'entrée attendue"
    )


def test_http_response_200(host):
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost")
    assert cmd.stdout == "200", f"Code HTTP attendu 200, reçu {cmd.stdout}"


def test_server_header_is_apache_only(host):
    """Le header Server doit être 'Apache' uniquement (preuve ServerTokens Prod)."""
    cmd = host.run("curl -sI http://localhost")
    assert cmd.rc == 0
    server_lines = [
        line for line in cmd.stdout.splitlines() if line.lower().startswith("server:")
    ]
    assert server_lines, f"Aucun header Server reçu. Sortie : {cmd.stdout}"
    server_value = server_lines[0].split(":", 1)[1].strip()
    assert server_value == "Apache", (
        f"Le header Server doit être exactement 'Apache' (sans version), "
        f"reçu : '{server_value}'. Le handler 'Reload httpd' n'a peut-être "
        f"pas tourné après la modification de ServerTokens."
    )
