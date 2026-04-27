"""Tests pytest+testinfra pour le challenge filtres-jinja-essentiels."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/filtres-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_trim_lower(host):
    """raw_input | trim | lower."""
    content = host.file(RESULT_FILE).content_string
    assert "trimmed=hello world" in content


def test_union_pkgs(host):
    """(pkgs_a + pkgs_b) | unique | sort | join(',')."""
    content = host.file(RESULT_FILE).content_string
    assert "union=memcached,nginx,postgres,redis" in content


def test_selectattr_map(host):
    """services | selectattr env=prod | map name | sort | join."""
    content = host.file(RESULT_FILE).content_string
    assert "prod_services=api,cache" in content


def test_combine_dicts(host):
    """base_config | combine(tls_overrides)."""
    content = host.file(RESULT_FILE).content_string
    # Le filtre combine surcharge port (80 → 443) et ajoute tls=True
    assert "app=api" in content
    assert "port=443" in content
    assert "tls=True" in content


def test_default_filter(host):
    """undefined_var | default('fallback-OK')."""
    content = host.file(RESULT_FILE).content_string
    assert "default_value=fallback-OK" in content
