"""Tests structure versionnement et publication (lab 76)."""

import re
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = LAB_ROOT / "CHANGELOG.md"
PUBLISH = LAB_ROOT / "PUBLISH.md"


def test_changelog_present():
    assert CHANGELOG.exists()


def test_publish_doc_present():
    assert PUBLISH.exists()


def test_changelog_has_semver_versions():
    """Le CHANGELOG suit semver (X.Y.Z)."""
    content = CHANGELOG.read_text()
    pattern = re.compile(r"\[(\d+\.\d+\.\d+)\]")
    versions = pattern.findall(content)
    assert len(versions) >= 2, "Au moins 2 versions semver attendues"


def test_changelog_uses_keepachangelog_sections():
    """CHANGELOG suit le format 'Keep a Changelog' (Added/Changed/Fixed)."""
    content = CHANGELOG.read_text()
    assert "### Added" in content
    assert "### Changed" in content or "### Fixed" in content


def test_publish_doc_covers_galaxy():
    content = PUBLISH.read_text()
    assert "ansible-galaxy" in content
    assert "Galaxy" in content


def test_publish_doc_covers_git_tag():
    content = PUBLISH.read_text()
    assert "git tag" in content
    assert "v1.2.0" in content or "vMAJOR" in content


def test_publish_doc_covers_pinning():
    content = PUBLISH.read_text()
    assert "version:" in content
    assert "1.2.0" in content
