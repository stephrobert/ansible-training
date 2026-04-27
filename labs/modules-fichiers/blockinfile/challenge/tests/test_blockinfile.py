"""Tests pytest+testinfra pour le challenge module blockinfile."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
TARGET_FILE = "/etc/profile.d/aliases-rhce.sh"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_aliases_file_exists(host):
    f = host.file(TARGET_FILE)
    assert f.exists
    assert f.mode == 0o644


def test_aliases_content(host):
    content = host.file(TARGET_FILE).content_string
    assert "alias ll='ls -lah'" in content
    assert "alias gs='git status'" in content
    assert "alias ports='ss -tulpn'" in content


def test_markers_present(host):
    content = host.file(TARGET_FILE).content_string
    assert "# BEGIN ALIASES RHCE" in content
    assert "# END ALIASES RHCE" in content


def test_idempotence_one_block(host):
    """Le marker BEGIN ne doit apparaitre qu une seule fois."""
    content = host.file(TARGET_FILE).content_string
    assert content.count("# BEGIN ALIASES RHCE") == 1
    assert content.count("# END ALIASES RHCE") == 1
