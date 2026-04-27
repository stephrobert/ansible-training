"""Tests pytest+testinfra pour le challenge module user."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Groupe rhce-team ===

def test_group_rhce_team_exists(host):
    assert host.group("rhce-team").exists


# === alice ===

def test_alice_exists(host):
    u = host.user("alice")
    assert u.exists
    assert u.shell == "/bin/bash"
    assert u.group == "rhce-team"


def test_alice_in_wheel(host):
    assert "wheel" in host.user("alice").groups


# === bob ===

def test_bob_exists_with_uid_2001(host):
    u = host.user("bob")
    assert u.exists
    assert u.uid == 2001
    assert u.group == "rhce-team"


# === deploy ===

def test_deploy_exists_with_uid_2000(host):
    u = host.user("deploy")
    assert u.exists
    assert u.uid == 2000
    assert u.group == "rhce-team"


def test_deploy_home_in_opt(host):
    u = host.user("deploy")
    assert u.home == "/opt/deploy"
    assert host.file("/opt/deploy").is_directory
