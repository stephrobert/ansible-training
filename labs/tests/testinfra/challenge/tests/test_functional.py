"""Tests du setup testinfra écrit par l'apprenant (lab 66).

Le fichier de tests testinfra est livré en squelette : ces tests analysent
le code Python de l'apprenant via l'AST (pas de grep de sous-chaînes) et
vérifient que pytest sait réellement collecter ses tests.

Exécution complète (`molecule test`) : elle exige Podman et le pull d'une
image systemd, trop lourd pour ce harnais ; elle reste la validation
manuelle documentée dans le README.
"""

import ast
import subprocess
import sys
from pathlib import Path

import yaml

from conftest import lab_solution_text

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"
TESTS_DIR = MOLECULE_DIR / "tests"


def _test_functions():
    """Retourne les fonctions test_* de tous les fichiers testinfra."""
    functions = []
    for f in sorted(TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(f.read_text(), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                functions.append(node)
    return functions


def test_molecule_yml_uses_testinfra_verifier():
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    verifier = config.get("verifier", {}).get("name")
    assert verifier == "testinfra", (
        f"verifier.name doit valoir 'testinfra' (vu : {verifier!r}) : c'est "
        "tout l'objet du lab, remplacer verify.yml par des tests Python"
    )


def test_at_least_4_test_functions():
    functions = _test_functions()
    assert len(functions) >= 4, (
        f"Au moins 4 fonctions test_* attendues dans molecule/default/tests/, "
        f"vu : {len(functions)}. Prouvez : paquet, service, socket 8080, nginx -t"
    )


def test_all_test_functions_use_host_fixture():
    functions = _test_functions()
    assert functions, "Aucune fonction test_* trouvée dans molecule/default/tests/"
    for fn in functions:
        args = [a.arg for a in fn.args.args]
        assert "host" in args, (
            f"{fn.name} ne reçoit pas la fixture 'host' : sans elle, le test "
            "ne s'exécute pas contre l'instance Molecule"
        )


def test_test_functions_contain_assertions():
    functions = _test_functions()
    for fn in functions:
        has_assert = any(isinstance(n, ast.Assert) for n in ast.walk(fn))
        has_todo = any(
            isinstance(n, ast.Raise) for n in ast.walk(fn)
        )
        assert has_assert and not has_todo, (
            f"{fn.name} doit contenir de vraies assertions (assert ...) et "
            "ne plus lever NotImplementedError : le squelette est à remplacer"
        )


def test_named_state_checks_present():
    """Le fichier de vérification prouve les 4 contrôles d'état de l'énoncé.

    Les tests AST ci-dessus garantissent la FORME (>= 4 fonctions test_*,
    fixture `host`, vraies assertions) mais PAS que les contrôles d'état
    précis nommés dans l'énoncé y figurent : paquet installé, service démarré
    ET activé au boot, socket en écoute sur 8080, `nginx -t` valide. On
    inspecte donc le CONTENU du fichier en jeu (celui de l'apprenant sous
    challenge/, sinon la référence déchiffrée).
    """
    content = lab_solution_text(__file__, name="files/test_webserver.py")
    assert "is_installed" in content, (
        "contrôle 'paquet nginx installé' (host.package(...).is_installed) absent"
    )
    assert "is_running" in content and "is_enabled" in content, (
        "contrôle 'service démarré ET activé au boot' incomplet "
        "(is_running / is_enabled attendus tous les deux)"
    )
    assert "8080" in content and "is_listening" in content, (
        "contrôle 'socket en écoute sur 8080' absent "
        "(host.socket('tcp://...:8080').is_listening attendu)"
    )
    assert "nginx -t" in content, (
        "contrôle 'nginx -t (configuration valide)' absent"
    )


def test_pytest_collects_testinfra_file():
    """Exécute réellement pytest en collecte sur vos tests testinfra.

    La collecte prouve que le fichier s'importe (syntaxe, imports) sans
    avoir besoin d'une instance Molecule active.
    """
    result = subprocess.run(
        # --confcutdir : la collecte doit prouver que VOTRE fichier s'importe,
        # indépendamment de la configuration du catalogue. Le conftest racine du
        # dépôt exclut `labs/*/*/molecule/*` (pour éviter que ces tests tournent
        # contre le poste du formateur au run global) : sans cette option, pytest
        # remonte jusqu'à lui et ne collecte rien, alors que le fichier est bon.
        [
            sys.executable, "-m", "pytest", "--collect-only", "-q",
            "-p", "no:cacheprovider", f"--confcutdir={TESTS_DIR}", str(TESTS_DIR),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        cwd=TESTS_DIR,
    )
    assert result.returncode == 0, (
        f"pytest n'arrive pas à collecter vos tests testinfra :\n"
        f"{result.stdout}{result.stderr}"
    )
