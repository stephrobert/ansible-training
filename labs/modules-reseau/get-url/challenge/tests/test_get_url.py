"""Tests pytest+testinfra pour le challenge module get_url."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("path", [
    "/opt/lab-gpl3.txt",
    "/opt/lab-lgpl3.txt",
])
def test_files_downloaded(host, path):
    f = host.file(path)
    assert f.exists, f"{path} doit exister"
    assert f.is_file
    assert f.mode == 0o644


def test_gpl3_content(host):
    """Verifier que le contenu correspond au texte GPL v3."""
    content = host.file("/opt/lab-gpl3.txt").content_string
    assert "GNU GENERAL PUBLIC LICENSE" in content
    assert "Version 3" in content
    # Le fichier GPL fait ~35K caracteres
    assert len(content) > 30000


def test_lgpl3_content(host):
    """Verifier que le contenu correspond au texte LGPL v3."""
    content = host.file("/opt/lab-lgpl3.txt").content_string
    assert "GNU LESSER GENERAL PUBLIC LICENSE" in content
    assert "Version 3" in content
