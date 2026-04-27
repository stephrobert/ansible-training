"""Tests pytest+testinfra pour le challenge jinja2-base."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/etc/motd-challenge"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_contains_hostname(host):
    content = host.file(RESULT_FILE).content_string
    assert "Bienvenue sur db1.lab" in content


def test_if_branch_db(host):
    """Le {% if host_role == 'DB' %} doit s'évaluer vrai."""
    content = host.file(RESULT_FILE).content_string
    assert "Profil : DB" in content


@pytest.mark.parametrize("svc", ["postgresql", "chronyd", "firewalld"])
def test_for_loop_services(host, svc):
    content = host.file(RESULT_FILE).content_string
    assert f"- {svc}" in content
