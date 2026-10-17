"""Tests pytest+testinfra pour le challenge replace."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
TARGET_FILE = "/etc/myapp.conf"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def _content(host) -> str:
    return host.file(TARGET_FILE).content_string


def test_file_existe(host):
    assert host.file(TARGET_FILE).exists, message(
        en=f"{TARGET_FILE} must exist: the lab's setup lays it down (replay it "
        f"through dsoxlab if needed), and your solution then transforms it.",
        fr=f"{TARGET_FILE} doit exister : il est posé par le setup du lab "
        f"(relancez-le via dsoxlab si besoin), puis transformé par votre solution.",
    )


def test_url_https(host):
    content = _content(host)
    # Membership de la LIGNE entière (pas une sous-chaîne d'URL) : on prouve que
    # le remplacement a produit la nouvelle URL, et CodeQL ne voit plus une
    # sanitization d'URL incomplète (py/incomplete-url-substring-sanitization).
    lines = [line.strip() for line in content.splitlines()]
    assert "url=https://api.example.com/v1" in lines, message(
        en="The URL must have been replaced with https://api.example.com (a plain replace).",
        fr="L'URL doit avoir été remplacée par https://api.example.com (replace simple).",
    )
    assert "api-old.example.com" not in content, message(
        en="The old api-old.example.com URL must be gone.",
        fr="L'ancienne URL api-old.example.com doit avoir disparu.",
    )


def test_ssl_serveur_active(host):
    """Dans la section [server], ssl_enabled doit être true (replace avec after/before)."""
    content = _content(host)
    # On extrait la section [server] jusqu'à [client]
    try:
        server_section = content.split("[server]", 1)[1].split("[client]", 1)[0]
    except IndexError:
        pytest.fail(message(
            en="Section [server] or [client] missing from the file.",
            fr="Section [server] ou [client] absente du fichier.",
        ))
    assert "ssl_enabled = true" in server_section, message(
        en=f"Inside [server], ssl_enabled must be 'true'. Section seen: {server_section[:200]}",
        fr=f"Dans [server], ssl_enabled doit être 'true'. Section vue : {server_section[:200]}",
    )


def test_ssl_client_intact(host):
    """Dans la section [client], ssl_enabled doit rester false (limitation before)."""
    content = _content(host)
    client_section = content.split("[client]", 1)[1] if "[client]" in content else ""
    assert "ssl_enabled=false" in client_section, message(
        en=f"Inside [client], ssl_enabled must stay 'false' (a replace bounded by "
        f"before/after). Section seen: {client_section[:200]}",
        fr=f"Dans [client], ssl_enabled doit rester 'false' (replace borné par before/after). "
        f"Section vue : {client_section[:200]}",
    )


def test_port_8443(host):
    content = _content(host)
    assert "port=8443" in content, message(
        en="The port must have been bumped to 8443 (a replace with the `\\g<1>8443` backref).",
        fr="Le port doit avoir été bumpé à 8443 (replace avec backref `\\g<1>8443`).",
    )
    assert "port=8080" not in content, message(
        en="The old port 8080 must be gone.",
        fr="L'ancien port 8080 doit avoir disparu.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
