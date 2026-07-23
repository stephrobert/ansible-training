"""Tests du lab 76 : versionnement et préparation de publication réels.

Pytest exécute le script challenge/solution.sh de l'apprenant (après
avoir vidé challenge/work/) puis vérifie l'état produit en interrogeant
réellement Git (tag annoté, commits) et l'archive de collection buildée.
La cohérence tag / CHANGELOG / galaxy.yml est le coeur du contrôle.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

LAB_ROOT = Path(__file__).resolve().parents[2]
SOLUTION = LAB_ROOT / "challenge" / "solution.sh"
WORK = LAB_ROOT / "challenge" / "work"
REPO = WORK / "repo"

SEMVER_HEADING = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]", re.MULTILINE)


def _git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.fixture(scope="module")
def solution_executed():
    """Vide challenge/work/ puis exécute réellement le script de l'apprenant."""
    if not SOLUTION.is_file():
        pytest.skip(
            "challenge/solution.sh manquant : écrivez le script de release "
            "(voir challenge/README.md)"
        )
    if WORK.exists():
        shutil.rmtree(WORK)
    result = subprocess.run(
        ["bash", str(SOLUTION)],
        cwd=LAB_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, (
        "challenge/solution.sh a échoué (il doit être rejouable depuis un "
        f"challenge/work/ vide) :\n{result.stdout[-3000:]}{result.stderr[-3000:]}"
    )
    return result


def _semver_tag():
    result = _git("tag", "-l")
    tags = [t for t in result.stdout.split() if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    return tags


def test_repo_initialized_with_role_and_changelog(solution_executed):
    assert (REPO / ".git").is_dir(), (
        "challenge/work/repo n'est pas un dépôt Git : git init manquant"
    )
    tracked = _git("ls-files").stdout
    assert "CHANGELOG.md" in tracked, (
        "CHANGELOG.md doit être commité dans le dépôt (git add + commit)"
    )
    assert "webserver" in tracked, (
        "Le rôle webserver doit être copié dans le dépôt et commité : on "
        "release un contenu, pas un dossier vide"
    )
    log = _git("log", "--oneline")
    assert log.returncode == 0 and log.stdout.strip(), (
        "Au moins un commit attendu dans le dépôt de release"
    )


def test_changelog_follows_keepachangelog(solution_executed):
    content = (REPO / "CHANGELOG.md").read_text()
    versions = SEMVER_HEADING.findall(content)
    assert len(versions) >= 2, (
        f"Au moins 2 versions [X.Y.Z] attendues dans le CHANGELOG, vu : {versions}"
    )
    assert "### Added" in content, (
        "Le CHANGELOG doit suivre Keep a Changelog : section ### Added"
    )
    assert "### Changed" in content or "### Fixed" in content, (
        "Il manque une section ### Changed ou ### Fixed"
    )


def test_annotated_semver_tag_exists(solution_executed):
    tags = _semver_tag()
    assert tags, (
        "Aucun tag vX.Y.Z dans le dépôt : taggez la release "
        "(git tag -a vX.Y.Z -m ...)"
    )
    for tag in tags:
        obj_type = _git("cat-file", "-t", tag).stdout.strip()
        assert obj_type == "tag", (
            f"Le tag {tag} est un tag léger : utilisez git tag -a "
            "(un tag annoté porte auteur, date et message de release)"
        )


def test_tag_matches_latest_changelog_version(solution_executed):
    content = (REPO / "CHANGELOG.md").read_text()
    versions = SEMVER_HEADING.findall(content)
    assert versions, "Aucune version [X.Y.Z] dans le CHANGELOG"
    latest = versions[0]
    tags = _semver_tag()
    assert f"v{latest}" in tags, (
        f"La dernière entrée du CHANGELOG est {latest} mais aucun tag "
        f"v{latest} n'existe : tag et CHANGELOG doivent raconter la même histoire"
    )


def test_collection_built_with_matching_version(solution_executed):
    content = (REPO / "CHANGELOG.md").read_text()
    latest = SEMVER_HEADING.findall(content)[0]
    dist = WORK / "dist"
    archives = sorted(dist.glob("acme-webstack-*.tar.gz")) if dist.is_dir() else []
    assert archives, (
        "Aucune archive acme-webstack-*.tar.gz dans challenge/work/dist/ : "
        "buildez la collection (ansible-galaxy collection build)"
    )
    expected = f"acme-webstack-{latest}.tar.gz"
    names = [a.name for a in archives]
    assert expected in names, (
        f"L'archive doit porter la version de la release ({expected}), "
        f"vu : {names}. Alignez galaxy.yml sur le tag"
    )
