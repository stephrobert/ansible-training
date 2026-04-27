"""Tests pytest+testinfra pour le challenge module sudoers."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("name", [
    "lab-rhce-alice",
    "lab-rhce-ops-team",
    "lab-rhce-alice-as-deploy",
])
def test_sudoers_file_exists_with_perms(host, name):
    f = host.file(f"/etc/sudoers.d/{name}")
    assert f.exists, f"{name} doit exister dans /etc/sudoers.d/"
    assert f.mode == 0o440, f"{name} doit etre en mode 0440 (sudo refuse sinon)"
    assert f.user == "root"


def test_alice_full_sudo(host):
    content = host.file("/etc/sudoers.d/lab-rhce-alice").content_string
    assert content.startswith("alice ALL=")
    assert "ALL" in content
    assert "NOPASSWD" not in content  # nopassword: false → password requis


def test_ops_team_nopasswd(host):
    content = host.file("/etc/sudoers.d/lab-rhce-ops-team").content_string
    assert content.startswith("%ops-team ALL=")
    assert "NOPASSWD" in content


def test_alice_runas_deploy(host):
    content = host.file("/etc/sudoers.d/lab-rhce-alice-as-deploy").content_string
    assert "alice ALL=(deploy)" in content
    assert "NOPASSWD" in content
    assert "/opt/myapp/bin/deploy.sh" in content


def test_visudo_global_validation(host):
    """visudo -cf doit retourner 0 — pas de regle cassee dans /etc/sudoers."""
    cmd = host.run("sudo visudo -cf /etc/sudoers")
    assert cmd.rc == 0, f"visudo a detecte une erreur : {cmd.stderr}"
