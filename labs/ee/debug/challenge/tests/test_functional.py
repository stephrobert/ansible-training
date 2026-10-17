"""Tests du lab 88 : debug d'un EE cassé.

Les fichiers buggy livrés à la racine ne doivent pas bouger (pièces du
diagnostic). L'apprenant dépose sa version corrigée dans challenge/ : ces
tests vérifient que chacun des 4 défauts a bien été identifié et corrigé.
Si ansible-builder est présent sur le poste, la définition corrigée est en
plus soumise à `ansible-builder create` (génération du Containerfile, sans
build long).
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import message

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE = LAB_DIR / "challenge"


def test_buggy_files_present_for_diagnosis():
    """Les fichiers buggy doivent rester en place pour le diagnostic."""
    for name in (
        "execution-environment-buggy.yml",
        "requirements-buggy.yml",
        "requirements-buggy.txt",
    ):
        assert (LAB_DIR / name).is_file(), message(
            en=f"{name} missing: the buggy files are the pieces of the diagnosis, "
            "do not delete them (dsoxlab clean restores them)",
            fr=f"{name} manquant : les fichiers buggy sont les pièces du "
            "diagnostic, ne les supprimez pas (dsoxlab clean les restaure)",
        )


def test_buggy_yaml_still_broken():
    """Le fichier buggy n'est pas corrigé en place (bug volontaire conservé)."""
    data = yaml.safe_load((LAB_DIR / "execution-environment-buggy.yml").read_text())
    assert "version" not in data, message(
        en="Do not fix the buggy files: put your corrected version in "
        "challenge/ (the buggy one is the reference for the diagnosis)",
        fr="Ne corrigez pas les fichiers buggy : déposez votre version corrigée "
        "dans challenge/ (le buggy sert de référence au diagnostic)",
    )


def test_corrected_yaml_has_version_3():
    """Défaut n°1 : le schéma du fichier corrigé doit être explicite."""
    f = CHALLENGE / "execution-environment.yml"
    assert f.is_file(), message(
        en="challenge/execution-environment.yml missing: write your corrected "
        "version of the EE definition",
        fr="challenge/execution-environment.yml manquant : écrivez votre "
        "version corrigée de la définition d'EE",
    )
    data = yaml.safe_load(f.read_text())
    assert data.get("version") == 3, message(
        en="Without an explicit schema declaration, ansible-builder falls back "
        "to a legacy mode that silently ignores your dependencies: read the "
        "build's first warning again",
        fr="Sans déclaration de schéma explicite, ansible-builder retombe sur "
        "un mode hérité qui ignore silencieusement vos dépendances : "
        "relisez le premier warning du build",
    )


def test_corrected_yaml_declares_all_dependency_kinds():
    """Défaut n°4 : les trois familles de dépendances doivent être branchées."""
    data = yaml.safe_load((CHALLENGE / "execution-environment.yml").read_text())
    deps = data.get("dependencies", {})
    for kind in ("galaxy", "python", "system"):
        assert kind in deps, message(
            en=f"dependencies.{kind} absent: the corrected EE must declare its "
            "collections (galaxy), its Python packages (python) and its "
            "system packages (system, through bindep.txt)",
            fr=f"dependencies.{kind} absent : l'EE corrigé doit déclarer ses "
            "collections (galaxy), ses paquets Python (python) et ses "
            "paquets système (system, via bindep.txt)",
        )


def test_corrected_requirements_uses_valid_collection():
    """Défaut n°2 : plus de collection introuvable sur Galaxy."""
    f = CHALLENGE / "requirements.yml"
    assert f.is_file(), message(
        en="challenge/requirements.yml missing",
        fr="challenge/requirements.yml manquant",
    )
    data = yaml.safe_load(f.read_text())
    names = [c["name"] for c in data.get("collections", [])]
    assert names, message(
        en="At least one collection must remain declared in the corrected EE",
        fr="Au moins une collection doit rester déclarée dans l'EE corrigé",
    )
    assert "community.does-not-exist" not in names, message(
        en="One declared collection does not exist on Galaxy: check each entry "
        "with ansible-galaxy collection install <name>:<version>",
        fr="Une collection déclarée n'existe pas sur Galaxy : vérifiez chaque "
        "entrée avec ansible-galaxy collection install <nom>:<version>",
    )
    assert all("." in name for name in names), message(
        en="Every collection must use its FQCN (namespace.collection)",
        fr="Toutes les collections doivent être en FQCN (namespace.collection)",
    )


def test_corrected_python_deps_use_real_version():
    """Défaut n°3 : plus de version PyPI introuvable."""
    f = CHALLENGE / "requirements.txt"
    assert f.is_file(), message(
        en="challenge/requirements.txt missing",
        fr="challenge/requirements.txt manquant",
    )
    content = f.read_text()
    assert "9999.0.0" not in content, message(
        en="One declared Python version does not exist on PyPI: check with "
        "pip index versions <package>",
        fr="Une version Python déclarée n'existe pas sur PyPI : vérifiez avec "
        "pip index versions <paquet>",
    )
    pinned = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert pinned, message(
        en="The corrected requirements.txt must not be empty",
        fr="requirements.txt corrigé ne doit pas être vide",
    )


def test_corrected_has_bindep():
    """Défaut n°4 : les dépendances système doivent exister."""
    f = CHALLENGE / "bindep.txt"
    assert f.is_file(), message(
        en="challenge/bindep.txt missing: the collections need system packages "
        "(git, ssh clients...) declared in the bindep format",
        fr="challenge/bindep.txt manquant : les collections ont besoin de "
        "paquets système (git, clients ssh...) déclarés au format bindep",
    )
    assert "[platform:rpm]" in f.read_text(), message(
        en="bindep.txt must target the [platform:rpm] profile (UBI/RHEL base)",
        fr="bindep.txt doit cibler le profil [platform:rpm] (base UBI/RHEL)",
    )


def test_corrected_definition_accepted_by_ansible_builder(tmp_path):
    """Exécute réellement ansible-builder sur la définition corrigée.

    `ansible-builder create` génère le Containerfile sans lancer le build
    d'image (long, réseau) : suffisant pour prouver que la définition est
    acceptée par l'outil. Skip honnête si le binaire n'est pas installé.
    """
    if shutil.which("ansible-builder") is None:
        pytest.skip(
            "ansible-builder absent du poste : pipx install ansible-builder "
            "pour valider ce point (le build complet reste manuel)"
        )
    result = subprocess.run(
        [
            "ansible-builder",
            "create",
            "--file",
            "execution-environment.yml",
            "--context",
            str(tmp_path / "context"),
        ],
        cwd=CHALLENGE,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, message(
        en=f"ansible-builder refuses the corrected definition:\n{result.stdout}{result.stderr}",
        fr=f"ansible-builder refuse la définition corrigée :\n{result.stdout}{result.stderr}",
    )
    assert (tmp_path / "context" / "Containerfile").is_file(), message(
        en="The Containerfile was not generated: the definition cannot be used",
        fr="Le Containerfile n'a pas été généré : la définition n'est pas exploitable",
    )
