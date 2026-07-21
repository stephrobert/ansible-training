"""Tests pytest+testinfra pour le challenge lab 94 — requirements.yml multi-sources."""

import re

import pytest
import yaml

from pathlib import Path

from conftest import (
    lab_host,
    assert_idempotent,
    lab_solution_text,
    lab_playbook,
)

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab94-collections.txt"
FQCN_RE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


def _requirements_collections():
    """Liste `collections:` du requirements.yml RÉELLEMENT en jeu.

    `lab_solution_text` rend `challenge/requirements.yml` (le travail de
    l'apprenant) s'il existe, sinon la référence chiffrée déchiffrée. On inspecte
    donc bien le fichier qui prétend satisfaire l'énoncé, pas le seul fichier
    preuve déposé sur l'hôte (qui, lui, ne dit rien des SOURCES ni du pinning).
    """
    text = lab_solution_text(__file__, name="requirements.yml")
    data = yaml.safe_load(text) or {}
    return data.get("collections", []) or []


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent — solution.yml a-t-elle installé puis déposé ?"
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root"


def test_file_lists_at_least_three_collections(host):
    """L'inventaire contient au moins 3 collections."""
    content = host.file(RESULT_FILE).content_string
    # Filtrer pour ne compter que les vraies lignes (pas les en-têtes)
    fqcn_lines = [
        line for line in content.splitlines()
        if line.strip()
        and "." in line.split()[0]
        and not line.startswith(("#", "Collection", "---", "Path"))
    ]
    assert len(fqcn_lines) >= 3, (
        f"{RESULT_FILE} doit lister au moins 3 collections au format FQCN, "
        f"vu : {len(fqcn_lines)}.\nContenu : {content[:300]}"
    )


def test_requirements_mixes_galaxy_and_git_sources():
    """Le requirements.yml agrège bien une source Galaxy ET une source Git.

    Le fichier preuve sur l'hôte compte des collections, mais trois collections
    Galaxy sans dépôt Git y passeraient — c'est l'anti-pattern même que le lab
    combat. On exige donc, dans le requirements.yml, au moins une source Galaxy
    (FQCN nu `namespace.name`) ET au moins une source Git (`type: git`,
    `git+...` ou URL en `.git`).
    """
    collections = _requirements_collections()
    galaxy, git = [], []
    for entry in collections:
        if isinstance(entry, str):
            name, typ = entry, ""
        else:
            name = str(entry.get("name", ""))
            typ = str(entry.get("type", "")).lower()
        if typ == "git" or name.startswith("git+") or name.endswith(".git"):
            git.append(name)
        elif "://" not in name and FQCN_RE.match(name):
            galaxy.append(name)
    assert galaxy, (
        "requirements.yml doit déclarer au moins une source Galaxy "
        f"(FQCN nu namespace.name). Collections vues : {collections}"
    )
    assert git, (
        "requirements.yml doit déclarer au moins une source Git (type: git, "
        f"git+... ou URL .git) EN PLUS de Galaxy. Collections vues : {collections}"
    )


def test_requirements_pins_a_strict_version():
    """Au moins un épinglage STRICT de version (semver `X.Y.Z` ou tag Git).

    Sans version, un `major` amont casse le build : le lab impose le pinning.
    Strict = aucune plage (`>=`, `<`, `*`, `,`), une valeur figée.
    """
    collections = _requirements_collections()
    pinned = []
    for entry in collections:
        if not isinstance(entry, dict):
            continue
        version = entry.get("version")
        if version is None:
            continue
        version = str(version).strip()
        if version and not any(op in version for op in (">", "<", "*", ",", " ")):
            pinned.append((entry.get("name"), version))
    assert pinned, (
        "requirements.yml doit épingler au moins une version stricte "
        f'(version: "X.Y.Z" ou tag Git). Collections vues : {collections}'
    )


def test_les_collections_sont_reellement_installees():
    """L'installation dans `local_collections/` doit avoir eu lieu.

    Tous les autres tests lisent /tmp/lab94-collections.txt sur db1. Or ce
    fichier peut être écrit à la main : un apprenant qui le fabriquerait sans
    jamais lancer `ansible-galaxy collection install` passerait l'intégralité du
    challenge. L'énoncé demande pourtant d'INSTALLER les collections dans
    `local_collections/`, ce que rien ne vérifiait.

    On regarde donc l'arborescence réellement produite, à côté du playbook joué
    (`{{ playbook_dir }}/../local_collections` dans l'énoncé). Le chemin est
    dérivé de `lab_playbook` et non codé en dur, pour valoir aussi bien en mode
    apprenant qu'en mode formateur, où le playbook joué n'est pas au même
    endroit.
    """
    playbook, _ = lab_playbook(__file__)
    racine = Path(playbook).parent.parent / "local_collections" / "ansible_collections"

    assert racine.is_dir(), (
        f"{racine} est introuvable : les collections n'ont pas été installées. "
        "Le fichier déposé sur db1 ne suffit pas, l'énoncé demande de les "
        "installer avec `ansible-galaxy collection install -r requirements.yml "
        "-p <...>/local_collections`."
    )

    # Une collection installée, c'est <namespace>/<nom>/ : on compte les feuilles.
    installees = sorted(
        f"{ns.name}.{col.name}"
        for ns in racine.iterdir()
        if ns.is_dir()
        for col in ns.iterdir()
        if col.is_dir()
    )

    assert len(installees) >= 3, (
        f"{len(installees)} collection(s) installée(s) dans {racine} "
        f"({', '.join(installees) or 'aucune'}), alors que l'énoncé en demande "
        "au moins 3, depuis 3 sources différentes."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
