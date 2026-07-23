"""Tests du lab 73 : pratique réelle de la CLI ansible-galaxy.

Pytest exécute le script challenge/solution.sh écrit par l'apprenant
(après avoir vidé challenge/build/) puis vérifie les EFFETS des commandes
sur le disque : scaffolds, archive buildée, collection installée depuis
l'archive locale. Tout est hors ligne.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
SOLUTION = LAB_ROOT / "challenge" / "solution.sh"
BUILD = LAB_ROOT / "challenge" / "build"


def test_ansible_galaxy_available():
    assert shutil.which("ansible-galaxy"), (
        "ansible-galaxy est introuvable : installez ansible-core, c'est "
        "l'outil enseigné par ce lab"
    )


@pytest.fixture(scope="module")
def solution_executed():
    """Vide challenge/build/ puis exécute réellement le script de l'apprenant."""
    if not SOLUTION.is_file():
        pytest.skip(
            "challenge/solution.sh manquant : écrivez le script qui pilote "
            "ansible-galaxy (voir challenge/README.md)"
        )
    if BUILD.exists():
        shutil.rmtree(BUILD)
    result = subprocess.run(
        ["bash", str(SOLUTION)],
        cwd=LAB_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, (
        "challenge/solution.sh a échoué (le script doit être rejouable "
        f"depuis un challenge/build/ vide) :\n{result.stdout[-3000:]}{result.stderr[-3000:]}"
    )
    return result


def test_role_scaffolded(solution_executed):
    role = BUILD / "roles" / "demo_web"
    assert role.is_dir(), (
        "challenge/build/roles/demo_web absent : le rôle doit être créé par "
        "ansible-galaxy role init (option --init-path)"
    )
    for sub in ("tasks/main.yml", "meta/main.yml", "defaults/main.yml"):
        assert (role / sub).is_file(), (
            f"{sub} manquant dans le rôle : c'est role init qui pose cette "
            "structure, ne la créez pas à la main"
        )


def test_collection_scaffolded(solution_executed):
    galaxy_yml = BUILD / "collections" / "acme" / "tools" / "galaxy.yml"
    assert galaxy_yml.is_file(), (
        "galaxy.yml absent : la collection acme.tools doit être créée par "
        "ansible-galaxy collection init (option --init-path)"
    )
    meta = yaml.safe_load(galaxy_yml.read_text())
    assert meta.get("namespace") == "acme", "namespace attendu : acme"
    assert meta.get("name") == "tools", "name attendu : tools"


def test_collection_archive_built(solution_executed):
    dist = BUILD / "dist"
    archives = sorted(dist.glob("acme-tools-*.tar.gz")) if dist.is_dir() else []
    assert archives, (
        "Aucune archive acme-tools-*.tar.gz dans challenge/build/dist/ : "
        "buildez la collection (ansible-galaxy collection build --output-path)"
    )


def test_collection_installed_from_local_archive(solution_executed):
    manifest = (
        BUILD / "installed" / "ansible_collections" / "acme" / "tools" / "MANIFEST.json"
    )
    assert manifest.is_file(), (
        "Collection non installée dans challenge/build/installed/ : "
        "installez l'archive locale avec ansible-galaxy collection install "
        "<archive> -p challenge/build/installed"
    )
    data = json.loads(manifest.read_text())
    info = data.get("collection_info", {})
    assert info.get("namespace") == "acme" and info.get("name") == "tools", (
        "Le MANIFEST.json installé ne correspond pas à acme.tools"
    )


def test_collection_list_sees_installation(solution_executed):
    """Exécute réellement ansible-galaxy collection list sur votre install."""
    result = subprocess.run(
        [
            "ansible-galaxy",
            "collection",
            "list",
            "-p",
            str(BUILD / "installed"),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        f"ansible-galaxy collection list échoue :\n{result.stdout}{result.stderr}"
    )
    assert "acme.tools" in result.stdout, (
        "acme.tools n'apparaît pas dans la sortie de collection list : "
        "l'installation est-elle allée dans challenge/build/installed ?"
    )
