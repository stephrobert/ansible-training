"""Tests pytest+testinfra pour le challenge lineinfile (sshd hardening)."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def _sshd_config(host) -> str:
    return host.file("/etc/ssh/sshd_config").content_string


def test_ipv4_forwarding_enabled(host):
    sysctl = host.file("/etc/sysctl.conf").content_string
    assert "net.ipv4.ip_forward=1" in sysctl, (
        "/etc/sysctl.conf doit contenir 'net.ipv4.ip_forward=1' (lineinfile state=present)."
    )


def test_permit_root_login_disabled(host):
    content = _sshd_config(host)
    assert "PermitRootLogin no" in content, (
        "sshd_config doit contenir 'PermitRootLogin no' (lineinfile + regexp + validate)."
    )
    # La ligne commentée d'origine ne doit plus être active
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("PermitRootLogin"):
            assert stripped == "PermitRootLogin no", (
                f"Une seule ligne PermitRootLogin attendue, trouvé : {stripped}"
            )


def test_max_auth_tries_3(host):
    content = _sshd_config(host)
    assert "MaxAuthTries 3" in content, (
        "sshd_config doit contenir 'MaxAuthTries 3' (lineinfile avec backrefs)."
    )


def test_allow_users_ansible(host):
    content = _sshd_config(host)
    assert "AllowUsers ansible" in content, (
        "sshd_config doit contenir 'AllowUsers ansible'."
    )


def test_sshd_config_valide(host):
    """sshd -t doit retourner 0 (config syntactiquement valide)."""
    cmd = host.run("sudo sshd -t")
    assert cmd.rc == 0, (
        f"sshd_config invalide après modifs : {cmd.stderr}. "
        f"Ajoutez `validate: 'sshd -t -f %s'` à chaque tâche lineinfile."
    )


def test_sshd_running(host):
    svc = host.service("sshd")
    assert svc.is_running, "Le service sshd doit être actif après les modifs."
