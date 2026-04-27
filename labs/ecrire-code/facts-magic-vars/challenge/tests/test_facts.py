"""Tests pytest+testinfra pour le challenge facts-magic-vars."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
SUMMARY_FILE = "/tmp/facts-summary.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_summary_file_exists(host):
    assert host.file(SUMMARY_FILE).exists


def test_inventory_hostname_resolved(host):
    content = host.file(SUMMARY_FILE).content_string
    assert "db1_hostname=db1.lab" in content


def test_os_fact(host):
    content = host.file(SUMMARY_FILE).content_string
    assert "db1_os=AlmaLinux" in content


def test_webservers_group_count(host):
    """Le groupe webservers contient 2 hôtes (web1 + web2)."""
    content = host.file(SUMMARY_FILE).content_string
    assert "webservers_count=2" in content


def test_hostvars_web1_ip(host):
    """hostvars['web1.lab'].ansible_default_ipv4.address = 10.10.20.21."""
    content = host.file(SUMMARY_FILE).content_string
    assert "web1_ip=10.10.20.21" in content, (
        "L'accès via hostvars['web1.lab'].ansible_default_ipv4.address "
        "doit retourner 10.10.20.21. Si vide, le pre-gather sur web1 "
        "n'a pas tourné."
    )
