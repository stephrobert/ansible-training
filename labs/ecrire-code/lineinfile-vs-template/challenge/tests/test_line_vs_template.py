"""Tests pytest+testinfra pour le challenge lineinfile-vs-template."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === lineinfile : 1 ligne dans /etc/hosts ===

def test_etc_hosts_contains_custom_entry(host):
    content = host.file("/etc/hosts").content_string
    assert "192.168.99.99 mon-host.lab" in content, (
        "lineinfile doit avoir ajouté '192.168.99.99 mon-host.lab' à /etc/hosts"
    )


# === template : fichier complet /etc/myapp.conf ===

def test_myapp_conf_exists(host):
    assert host.file("/etc/myapp.conf").exists


def test_myapp_conf_server_host(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "host = 0.0.0.0" in content


def test_myapp_conf_server_port(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "port = 8080" in content


def test_myapp_conf_db_pool_size(host):
    content = host.file("/etc/myapp.conf").content_string
    assert "pool_size = 10" in content
