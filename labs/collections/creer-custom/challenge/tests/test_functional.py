"""Tests structurels lab 95 — créer une collection custom.

Valide la structure générée par l'apprenant : galaxy.yml conforme,
module Python avec DOCUMENTATION/EXAMPLES/RETURN, tarball buildé.
"""

import re
import json
import tarfile
import yaml
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = LAB_DIR / "challenge"
COLL_ROOT = CHALLENGE_DIR / "collection_root" / "ansible_collections" / "student" / "lab95"
BUILD_DIR = CHALLENGE_DIR / "build"


def test_collection_root_exists():
    assert COLL_ROOT.is_dir(), (
        f"{COLL_ROOT} absent — vous devez exécuter "
        "`ansible-galaxy collection init student.lab95 --init-path collection_root/`."
    )


def test_galaxy_yml_namespace_and_name():
    f = COLL_ROOT / "galaxy.yml"
    assert f.is_file(), "galaxy.yml absent"
    data = yaml.safe_load(f.read_text())
    assert data["namespace"] == "student"
    assert data["name"] == "lab95"
    assert data["version"] == "1.0.0"


def test_galaxy_yml_has_tags():
    data = yaml.safe_load((COLL_ROOT / "galaxy.yml").read_text())
    tags = data.get("tags", [])
    assert isinstance(tags, list) and len(tags) >= 2, (
        f"galaxy.yml doit avoir au moins 2 tags (obligatoire pour Galaxy), vu : {tags}"
    )


def test_runtime_yml_requires_ansible():
    f = COLL_ROOT / "meta" / "runtime.yml"
    assert f.is_file(), "meta/runtime.yml absent"
    data = yaml.safe_load(f.read_text())
    assert "requires_ansible" in data, (
        "meta/runtime.yml doit déclarer requires_ansible: '>=2.18.0'"
    )


def test_module_python_exists():
    f = COLL_ROOT / "plugins" / "modules" / "lab95_hello.py"
    assert f.is_file(), (
        f"{f} absent — créez le module Python en suivant le squelette."
    )


def test_module_has_documentation_examples_return():
    """Le module Python contient les 3 sections obligatoires."""
    content = (COLL_ROOT / "plugins" / "modules" / "lab95_hello.py").read_text()
    for section in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
        assert section in content, f"Section {section} absente du module Python"


def test_module_returns_hello_message():
    content = (COLL_ROOT / "plugins" / "modules" / "lab95_hello.py").read_text()
    assert re.search(r"Hello.*lab95", content), (
        "Le module doit retourner un msg contenant 'Hello' et 'lab95'."
    )


def test_tarball_built():
    tarballs = list(BUILD_DIR.glob("student-lab95-*.tar.gz")) if BUILD_DIR.exists() else []
    assert tarballs, (
        f"{BUILD_DIR}/student-lab95-1.0.0.tar.gz absent — exécutez "
        "`ansible-galaxy collection build --output-path ../../../../build/`."
    )


def test_tarball_contains_galaxy_yml():
    """L'archive doit porter les métadonnées de la collection et le module.

    Le test exigeait `galaxy.yml` DANS l'archive : c'était infaisable.
    `ansible-galaxy collection build` consomme galaxy.yml et le transforme en
    MANIFEST.json, il ne l'embarque jamais. Vérifié sur une collection vierge
    (`collection init` seul, aucun build_ignore) : l'archive contient
    MANIFEST.json et FILES.json, jamais galaxy.yml.

    Personne ne pouvait donc réussir ce test, sauf à glisser dans l'archive un
    leurre nommé galaxy.yml, ce qui n'aurait rien prouvé. On vérifie le VRAI
    porteur des métadonnées, et que ses valeurs viennent bien du galaxy.yml
    écrit par l'apprenant.
    """
    tarballs = list(BUILD_DIR.glob("student-lab95-*.tar.gz"))
    assert tarballs, "Pas de tarball à inspecter"
    with tarfile.open(tarballs[0]) as t:
        names = t.getnames()
        assert "MANIFEST.json" in names, (
            "L'archive doit contenir MANIFEST.json : c'est lui qui porte les "
            "métadonnées, galaxy.yml y est consommé à la construction.\n"
            f"Vu : {sorted(names)[:8]}"
        )
        manifest = json.loads(t.extractfile("MANIFEST.json").read())
    info = manifest.get("collection_info", {})
    assert info.get("namespace") == "student" and info.get("name") == "lab95", (
        "MANIFEST.json doit porter le namespace/nom déclarés dans votre "
        f"galaxy.yml (vu : {info.get('namespace')}.{info.get('name')})."
    )
    assert any("plugins/modules/lab95_hello.py" in n for n in names), (
        "tarball doit contenir le module lab95_hello.py"
    )
