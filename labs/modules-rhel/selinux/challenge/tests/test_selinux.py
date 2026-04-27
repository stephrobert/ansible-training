"""Tests pytest+testinfra pour le challenge module selinux."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_selinux_enforcing(host):
    cmd = host.run("getenforce")
    assert cmd.rc == 0
    assert cmd.stdout.strip() == "Enforcing"


def test_httpd_network_connect_boolean_on(host):
    cmd = host.run("getsebool httpd_can_network_connect")
    assert cmd.rc == 0
    assert "--> on" in cmd.stdout, f"Boolean doit etre on, sortie : {cmd.stdout}"


def test_myapp_dir_exists(host):
    f = host.file("/var/www/myapp")
    assert f.is_directory
    assert f.mode == 0o755


def test_myapp_dir_selinux_context(host):
    """Le contexte SELinux du dossier doit inclure httpd_sys_content_t."""
    cmd = host.run("ls -dZ /var/www/myapp")
    assert cmd.rc == 0
    assert "httpd_sys_content_t" in cmd.stdout, \
        f"Contexte attendu, sortie : {cmd.stdout}"
