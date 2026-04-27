"""Tests pytest+testinfra pour le challenge replace."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
TARGET_FILE = "/etc/myapp.conf"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def _content(host) -> str:
    return host.file(TARGET_FILE).content_string


def test_file_existe(host):
    assert host.file(TARGET_FILE).exists, (
        f"{TARGET_FILE} doit exister (créé par la tâche `copy:` au début de la solution)."
    )


def test_url_https(host):
    content = _content(host)
    assert "https://api.example.com" in content, (
        "L'URL doit avoir été remplacée par https://api.example.com (replace simple)."
    )
    assert "api-old.example.com" not in content, (
        "L'ancienne URL api-old.example.com doit avoir disparu."
    )


def test_ssl_serveur_active(host):
    """Dans la section [server], ssl_enabled doit être true (replace avec after/before)."""
    content = _content(host)
    # On extrait la section [server] jusqu'à [client]
    try:
        server_section = content.split("[server]", 1)[1].split("[client]", 1)[0]
    except IndexError:
        pytest.fail("Section [server] ou [client] absente du fichier.")
    assert "ssl_enabled = true" in server_section, (
        f"Dans [server], ssl_enabled doit être 'true'. Section vue : {server_section[:200]}"
    )


def test_ssl_client_intact(host):
    """Dans la section [client], ssl_enabled doit rester false (limitation before)."""
    content = _content(host)
    client_section = content.split("[client]", 1)[1] if "[client]" in content else ""
    assert "ssl_enabled=false" in client_section, (
        f"Dans [client], ssl_enabled doit rester 'false' (replace borné par before/after). "
        f"Section vue : {client_section[:200]}"
    )


def test_port_8443(host):
    content = _content(host)
    assert "port=8443" in content, (
        "Le port doit avoir été bumpé à 8443 (replace avec backref `\\g<1>8443`)."
    )
    assert "port=8080" not in content, "L'ancien port 8080 doit avoir disparu."
