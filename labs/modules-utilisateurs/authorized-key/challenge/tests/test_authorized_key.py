"""Tests pytest+testinfra pour le challenge module authorized_key."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Permissions strictes ===

def test_alice_authorized_keys_perms(host):
    f = host.file("/home/alice/.ssh/authorized_keys")
    assert f.exists
    assert f.mode == 0o600
    assert f.user == "alice"


def test_alice_ssh_dir_perms(host):
    d = host.file("/home/alice/.ssh")
    assert d.is_directory
    assert d.mode == 0o700


def test_bob_authorized_keys_perms(host):
    f = host.file("/home/bob/.ssh/authorized_keys")
    assert f.exists
    assert f.mode == 0o600
    assert f.user == "bob"


# === Cle libre d alice ===

def test_alice_has_personal_key(host):
    content = host.file("/home/alice/.ssh/authorized_keys").content_string
    assert "alice@laptop" in content


# === Cle service d alice ===

def test_alice_has_service_key_with_command(host):
    content = host.file("/home/alice/.ssh/authorized_keys").content_string
    assert "backup@service" in content
    assert 'command="/usr/local/bin/backup.sh"' in content
    assert "no-pty" in content


# === Cle restreinte de bob ===

def test_bob_has_restricted_key(host):
    content = host.file("/home/bob/.ssh/authorized_keys").content_string
    assert "bob@laptop" in content
    assert 'from="10.10.20.0/24"' in content
    assert "no-pty" in content
