"""Tests structurels lab 95 — créer une collection custom.

Valide la structure générée par l'apprenant : galaxy.yml conforme,
module Python avec DOCUMENTATION/EXAMPLES/RETURN, tarball buildé.
"""

import json
import re
import tarfile
from pathlib import Path

import yaml

from conftest import message

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = LAB_DIR / "challenge"
COLL_ROOT = CHALLENGE_DIR / "collection_root" / "ansible_collections" / "student" / "lab95"
BUILD_DIR = CHALLENGE_DIR / "build"


def test_collection_root_exists():
    assert COLL_ROOT.is_dir(), message(
        en=f"{COLL_ROOT} missing: you must run "
        "`ansible-galaxy collection init student.lab95 --init-path collection_root/`.",
        fr=f"{COLL_ROOT} absent — vous devez exécuter "
        "`ansible-galaxy collection init student.lab95 --init-path collection_root/`.",
    )


def test_galaxy_yml_namespace_and_name():
    f = COLL_ROOT / "galaxy.yml"
    assert f.is_file(), message(
        en="galaxy.yml missing",
        fr="galaxy.yml absent",
    )
    data = yaml.safe_load(f.read_text())
    assert data["namespace"] == "student", message(
        en=f"galaxy.yml declares the namespace {data['namespace']!r}, "
           f"expected 'student'. It is the first half of the FQCN, and it "
           f"cannot be changed after publication.",
        fr=f"galaxy.yml déclare le namespace {data['namespace']!r}, attendu "
           f"'student'. C'est la première moitié du FQCN, et elle ne se "
           f"change plus après publication.",
    )
    assert data["name"] == "lab95", message(
        en=f"galaxy.yml declares the name {data['name']!r}, expected 'lab95'.",
        fr=f"galaxy.yml déclare le nom {data['name']!r}, attendu 'lab95'.",
    )
    assert data["version"] == "1.0.0", message(
        en=f"galaxy.yml declares the version {data['version']!r}, expected "
           f"'1.0.0'. It is the version the built archive will carry.",
        fr=f"galaxy.yml déclare la version {data['version']!r}, attendu "
           f"'1.0.0'. C'est elle que portera l'archive construite.",
    )


def test_galaxy_yml_has_tags():
    data = yaml.safe_load((COLL_ROOT / "galaxy.yml").read_text())
    tags = data.get("tags", [])
    assert isinstance(tags, list) and len(tags) >= 2, message(
        en=f"galaxy.yml must have at least 2 tags (Galaxy requires them), seen: {tags}",
        fr=f"galaxy.yml doit avoir au moins 2 tags (obligatoire pour Galaxy), vu : {tags}",
    )


def test_runtime_yml_requires_ansible():
    f = COLL_ROOT / "meta" / "runtime.yml"
    assert f.is_file(), message(
        en="meta/runtime.yml missing",
        fr="meta/runtime.yml absent",
    )
    data = yaml.safe_load(f.read_text())
    assert "requires_ansible" in data, message(
        en="meta/runtime.yml must declare requires_ansible: '>=2.18.0'",
        fr="meta/runtime.yml doit déclarer requires_ansible: '>=2.18.0'",
    )


def test_module_python_exists():
    f = COLL_ROOT / "plugins" / "modules" / "lab95_hello.py"
    assert f.is_file(), message(
        en=f"{f} missing: create the Python module, following the skeleton.",
        fr=f"{f} absent — créez le module Python en suivant le squelette.",
    )


def test_module_has_documentation_examples_return():
    """Le module Python contient les 3 sections obligatoires."""
    content = (COLL_ROOT / "plugins" / "modules" / "lab95_hello.py").read_text()
    for section in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
        assert section in content, message(
            en=f"Section {section} missing from the Python module",
            fr=f"Section {section} absente du module Python",
        )


def test_module_returns_hello_message():
    content = (COLL_ROOT / "plugins" / "modules" / "lab95_hello.py").read_text()
    assert re.search(r"Hello.*lab95", content), message(
        en="The module must return a msg containing 'Hello' and 'lab95'.",
        fr="Le module doit retourner un msg contenant 'Hello' et 'lab95'.",
    )


def test_tarball_built():
    tarballs = list(BUILD_DIR.glob("student-lab95-*.tar.gz")) if BUILD_DIR.exists() else []
    assert tarballs, message(
        en=f"{BUILD_DIR}/student-lab95-1.0.0.tar.gz missing: run "
        "`ansible-galaxy collection build --output-path ../../../../build/`.",
        fr=f"{BUILD_DIR}/student-lab95-1.0.0.tar.gz absent — exécutez "
        "`ansible-galaxy collection build --output-path ../../../../build/`.",
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
    assert tarballs, message(
        en="No tarball to inspect",
        fr="Pas de tarball à inspecter",
    )
    with tarfile.open(tarballs[0]) as t:
        names = t.getnames()
        assert "MANIFEST.json" in names, message(
            en="The archive must contain MANIFEST.json: it is what carries the "
            "metadata, and galaxy.yml is consumed into it at build time.\n"
            f"Seen: {sorted(names)[:8]}",
            fr="L'archive doit contenir MANIFEST.json : c'est lui qui porte les "
            "métadonnées, galaxy.yml y est consommé à la construction.\n"
            f"Vu : {sorted(names)[:8]}",
        )
        manifest = json.loads(t.extractfile("MANIFEST.json").read())
    info = manifest.get("collection_info", {})
    assert info.get("namespace") == "student" and info.get("name") == "lab95", message(
        en="MANIFEST.json must carry the namespace and name declared in your "
        f"galaxy.yml (seen: {info.get('namespace')}.{info.get('name')}).",
        fr="MANIFEST.json doit porter le namespace/nom déclarés dans votre "
        f"galaxy.yml (vu : {info.get('namespace')}.{info.get('name')}).",
    )
    assert any("plugins/modules/lab95_hello.py" in n for n in names), message(
        en="The tarball must contain the lab95_hello.py module",
        fr="tarball doit contenir le module lab95_hello.py",
    )
