"""Tests structure requirements.yml."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
REQS = LAB_ROOT / "requirements.yml"


def test_requirements_present():
    assert REQS.exists()


def test_has_roles_and_collections():
    config = yaml.safe_load(REQS.read_text())
    assert "roles" in config
    assert "collections" in config


def test_roles_pinned_by_version():
    config = yaml.safe_load(REQS.read_text())
    for r in config["roles"]:
        assert "version" in r, f"Rôle {r.get('name')} doit pinner une version"


def test_at_least_one_git_role():
    config = yaml.safe_load(REQS.read_text())
    git_roles = [r for r in config["roles"] if "src" in r and "github.com" in r.get("src", "")]
    assert len(git_roles) >= 1


def test_at_least_one_galaxy_role():
    """Rôle sans 'src:' = depuis Galaxy."""
    config = yaml.safe_load(REQS.read_text())
    galaxy_roles = [r for r in config["roles"] if "src" not in r]
    assert len(galaxy_roles) >= 1


def test_collection_pinned_strict():
    """Au moins une collection pinnée par version exacte (production)."""
    config = yaml.safe_load(REQS.read_text())
    found_strict = False
    for c in config["collections"]:
        if not isinstance(c, dict):
            continue
        version = str(c.get("version", ""))
        if version.count(".") >= 2 and not any(op in version for op in [">", "<", "~", "*", " ", ","]):
            found_strict = True
            break
    assert found_strict, "Au moins une collection doit être pinnée strictement (version exacte)"
