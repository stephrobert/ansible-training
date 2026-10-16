"""Tests du lab 74 : requirements.yml écrit ET réellement installé.

Le requirements.yml est livré en squelette : l'apprenant l'écrit puis
l'installe dans challenge/deps/ (ansible-galaxy role/collection install
-p ...). Les tests contrôlent la sémantique du manifeste ET l'état du
disque après installation ; ils n'ont eux-mêmes pas besoin du réseau
(c'est l'installation, faite par l'apprenant, qui en a besoin).
"""

import json
from pathlib import Path
from urllib.parse import urlparse

import yaml

from conftest import message

LAB_ROOT = Path(__file__).resolve().parents[2]
REQS = LAB_ROOT / "requirements.yml"
DEPS = LAB_ROOT / "challenge" / "deps"


def _config():
    return yaml.safe_load(REQS.read_text())


def test_requirements_present():
    assert REQS.exists(), message(
        en="requirements.yml missing: was the skeleton deleted?",
        fr="requirements.yml manquant : le squelette a-t-il été supprimé ?",
    )


def test_has_roles_and_collections():
    config = _config()
    assert config.get("roles"), message(
        en="The roles: section must declare at least 2 roles (Galaxy + Git)",
        fr="La section roles: doit déclarer au moins 2 rôles (Galaxy + Git)",
    )
    assert len(config["roles"]) >= 2, message(
        en="At least 2 roles expected (mixed sources)",
        fr="Au moins 2 rôles attendus (sources mixtes)",
    )
    assert config.get("collections"), message(
        en="The collections: section must declare at least one collection",
        fr="La section collections: doit déclarer au moins une collection",
    )


def test_roles_pinned_by_version():
    """Chaque rôle doit épingler sa version, et il doit y avoir des rôles.

    Le test était VACANT : `for r in []` ne fait aucune itération, donc aucune
    assertion, donc vert. Il passait sur le squelette livré (`roles: []`), et
    n abritait aucune preuve. Seul son voisin le sauvait.
    """
    roles = _config()["roles"]
    assert roles, message(
        en="No role in requirements.yml: you need at least one from Galaxy and "
        "one from Git (see challenge/README.md).",
        fr="Aucun rôle dans requirements.yml : il en faut au moins un depuis "
        "Galaxy et un depuis Git (cf. challenge/README.md).",
    )
    for r in roles:
        assert "version" in r, message(
            en=f"The {r.get('name') or r.get('src')} role must pin a version: "
            "without pinning, two installs give two different results",
            fr=f"Le rôle {r.get('name') or r.get('src')} doit épingler une "
            "version : sans épinglage, deux installs donnent deux résultats",
        )


def _is_github_src(src: str) -> bool:
    """Rôle hébergé sur github.com, comparé sur le HOST exact.

    `"github.com" in src` matcherait `evil-github.com` ou un chemin qui contient
    la chaîne : on extrait le netloc de l'URL et on le compare, ce que demande
    CodeQL (py/incomplete-url-substring-sanitization).
    """
    netloc = urlparse(src.replace("git+", "")).netloc.rsplit("@", 1)[-1].split(":")[0]
    return netloc == "github.com" or netloc.endswith(".github.com")


def test_at_least_one_git_role():
    git_roles = [
        r for r in _config()["roles"] if _is_github_src(str(r.get("src", "")))
    ]
    assert git_roles, message(
        en="At least one role must come from Git (src: https://github.com/...): "
        "that is the pattern for internal or forked roles",
        fr="Au moins un rôle doit venir de Git (src: https://github.com/...) : "
        "c'est le pattern pour les rôles internes ou forkés",
    )


def test_at_least_one_galaxy_role():
    galaxy_roles = [r for r in _config()["roles"] if "src" not in r]
    assert galaxy_roles, message(
        en="At least one role must come from Galaxy (declared by name: alone, "
        "with no src:)",
        fr="Au moins un rôle doit venir de Galaxy (déclaré par name: seul, "
        "sans src:)",
    )


def _strict_collections():
    strict = []
    for c in _config()["collections"]:
        if not isinstance(c, dict):
            continue
        version = str(c.get("version", ""))
        if version.count(".") >= 2 and not any(
            op in version for op in (">", "<", "~", "*", " ", ",")
        ):
            strict.append((c["name"], version))
    return strict


def test_collection_pinned_strict():
    assert _strict_collections(), message(
        en="At least one collection must be pinned to an exact version (X.Y.Z): "
        "production reproducibility is not negotiable",
        fr="Au moins une collection doit être épinglée en version exacte "
        "(X.Y.Z) : la reproductibilité production ne se négocie pas",
    )


def test_roles_actually_installed():
    """L'état du disque prouve que l'installation a été faite."""
    roles_dir = DEPS / "roles"
    assert roles_dir.is_dir(), message(
        en="challenge/deps/roles missing: run ansible-galaxy role install "
        "-r requirements.yml -p challenge/deps/roles",
        fr="challenge/deps/roles absent : lancez ansible-galaxy role install "
        "-r requirements.yml -p challenge/deps/roles",
    )
    for r in _config()["roles"]:
        name = r.get("name") or str(r.get("src", "")).rsplit("/", 1)[-1]
        installed = roles_dir / name
        assert installed.is_dir(), message(
            en=f"The declared role {name!r} is not installed in "
            "challenge/deps/roles: the manifest must actually be applied",
            fr=f"Le rôle déclaré {name!r} n'est pas installé dans "
            "challenge/deps/roles : le manifeste doit être réellement appliqué",
        )
        assert (installed / "meta" / "main.yml").is_file() or (
            installed / "tasks"
        ).is_dir(), message(
            en=f"{name} installed but with no role structure: incomplete install?",
            fr=f"{name} installé mais sans structure de rôle : install incomplet ?",
        )


def test_pinned_collection_installed_in_exact_version():
    """La collection épinglée est installée dans la version exacte demandée."""
    col_root = DEPS / "collections" / "ansible_collections"
    assert col_root.is_dir(), message(
        en="challenge/deps/collections missing: run ansible-galaxy collection "
        "install -r requirements.yml -p challenge/deps/collections",
        fr="challenge/deps/collections absent : lancez ansible-galaxy "
        "collection install -r requirements.yml -p challenge/deps/collections",
    )
    for name, version in _strict_collections():
        namespace, colname = name.split(".", 1)
        manifest = col_root / namespace / colname / "MANIFEST.json"
        assert manifest.is_file(), message(
            en=f"The {name} collection is not installed in challenge/deps/collections",
            fr=f"La collection {name} n'est pas installée dans challenge/deps/collections",
        )
        installed_version = json.loads(manifest.read_text())["collection_info"]["version"]
        assert installed_version == version, message(
            en=f"{name} installed as {installed_version}, while the manifest pins "
            f"{version}: the exact pin must be found on disk",
            fr=f"{name} installée en {installed_version}, or le manifeste "
            f"épingle {version} : l'épinglage exact doit se retrouver sur le disque",
        )
