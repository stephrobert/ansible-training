"""Tests pytest+testinfra pour le challenge lab 97 — migration rôle → collection."""

import re

import yaml
from pathlib import Path

import pytest

from conftest import lab_host, assert_idempotent

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = LAB_DIR / "challenge"
COLL_ROOT = CHALLENGE_DIR / "ansible_collections" / "student" / "lab97_migrated"

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab97-migration.txt"

# `lab97_status` : le nom que le module portait dans library/ du rôle standalone.
# `lab97_check`  : le nom qu'il porte dans la collection. La redirection va du
# premier vers le second — c'est tout l'objet de la migration.
LEGACY_MODULE = "lab97_status"
NEW_MODULE = "lab97_check"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_collection_initialized():
    assert COLL_ROOT.is_dir(), (
        f"{COLL_ROOT} absent — exécutez "
        "`ansible-galaxy collection init student.lab97_migrated --init-path ansible_collections/`."
    )


def test_runtime_yml_has_redirect():
    """La route part de l'ANCIEN nom et pointe vers le nouveau FQCN.

    La clé de `plugin_routing.modules` est le nom à faire survivre
    (`lab97_status`, celui du rôle standalone), la cible est le nom retenu dans
    la collection (`lab97_check`). Les deux doivent DIFFÉRER : une entrée
    `lab97_check: {redirect: student.lab97_migrated.lab97_check}` se redirige
    vers elle-même, et ansible-core la refuse au runtime avec « plugin redirect
    loop resolving lab97_check ». Ce test exigeait exactement cette boucle : il
    rendait le lab impossible à résoudre, quelle que soit la solution écrite.
    """
    f = COLL_ROOT / "meta" / "runtime.yml"
    assert f.is_file(), "meta/runtime.yml absent"
    data = yaml.safe_load(f.read_text())
    routing = data.get("plugin_routing", {}).get("modules", {})
    assert LEGACY_MODULE in routing, (
        f"plugin_routing.modules.{LEGACY_MODULE} absent de meta/runtime.yml : "
        "c'est l'ancien nom qu'il faut router, pas le nouveau."
    )
    redirect = routing[LEGACY_MODULE].get("redirect", "")
    assert redirect == f"student.lab97_migrated.{NEW_MODULE}", (
        f"redirect doit pointer vers student.lab97_migrated.{NEW_MODULE}, "
        f"vu : {redirect!r}"
    )


def test_legacy_module_n_existe_que_par_la_redirection():
    """Aucun fichier ne porte l'ancien nom : seule la route le fait vivre.

    Sans ce contrôle, copier le module sous ses deux noms ferait passer tous les
    autres tests sans qu'aucun `plugin_routing` ne serve à quoi que ce soit —
    et la migration ne prouverait plus rien.
    """
    orphelin = COLL_ROOT / "plugins" / "modules" / f"{LEGACY_MODULE}.py"
    assert not orphelin.exists(), (
        f"{orphelin} ne doit PAS exister : l'ancien nom doit être servi par "
        "plugin_routing.redirect, pas par une copie du module."
    )


def test_runtime_yml_has_deprecation():
    data = yaml.safe_load((COLL_ROOT / "meta" / "runtime.yml").read_text())
    routing = data["plugin_routing"]["modules"][LEGACY_MODULE]
    assert "deprecation" in routing, "deprecation: absent"
    assert "removal_version" in routing["deprecation"], (
        "removal_version absent dans deprecation"
    )


def test_module_python_migrated():
    f = COLL_ROOT / "plugins" / "modules" / "lab97_check.py"
    assert f.is_file(), (
        f"{f} absent — déplacez/créez le module dans plugins/modules/."
    )
    content = f.read_text()
    for section in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
        assert section in content, f"Section {section} absente du module"


def test_proof_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent — solution.yml a-t-elle tourné avec "
        "ANSIBLE_COLLECTIONS_PATH=challenge/ansible_collections ?"
    )


def test_proof_file_mode(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644


def test_proof_file_contains_new_fqcn_result(host):
    """Le fichier doit prouver que le module a tourné via le nouveau FQCN."""
    content = host.file(RESULT_FILE).content_string
    assert re.search(r"^new:\s*lab97-migrated-OK\s*$", content, re.M), (
        "Le fichier doit porter une ligne `new: lab97-migrated-OK`, sortie du "
        f"module appelé par son FQCN complet. Vu : {content[:200]!r}"
    )


def test_proof_file_prouve_que_l_ancien_nom_marche(host):
    """L'ancien nom a rendu le même résultat que le nouveau, via la redirection.

    C'est LE test de la migration : `lab97_status` n'existe nulle part comme
    fichier (cf. test_legacy_module_n_existe_que_par_la_redirection). S'il rend
    « lab97-migrated-OK », c'est que plugin_routing.redirect l'a résolu vers
    `lab97_check`. Si la route bouclait ou manquait, le playbook sortirait sur
    « couldn't resolve module/action » et ce fichier n'existerait pas.
    """
    content = host.file(RESULT_FILE).content_string
    assert re.search(r"^legacy:\s*lab97-migrated-OK\s*$", content, re.M), (
        "Le fichier doit porter une ligne `legacy: lab97-migrated-OK` : la "
        "preuve qu'un appel à l'ANCIEN nom a bien été servi par la "
        f"redirection. Vu : {content[:200]!r}"
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
