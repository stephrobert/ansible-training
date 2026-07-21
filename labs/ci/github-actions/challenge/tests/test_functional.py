"""Tests du workflow GitHub Actions écrit par l'apprenant (lab 69).

Le workflow est livré en squelette (des `???`) : ces tests ne passent que
lorsque l'apprenant l'a réellement complété. Ils chargent le YAML et
contrôlent la sémantique (jobs, matrice, épinglage SHA, permissions), puis
exécutent actionlint si le binaire est disponible sur le poste.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = LAB_ROOT / ".github/workflows/test.yml"


def _config():
    return yaml.safe_load(WORKFLOW.read_text())


def test_workflow_file_present():
    assert WORKFLOW.exists(), (
        "Le fichier .github/workflows/test.yml doit exister (squelette livré)"
    )


def test_workflow_has_lint_and_molecule_jobs():
    jobs = _config().get("jobs", {})
    assert "lint" in jobs, "Il manque le job 'lint' (yamllint + ansible-lint)"
    assert "molecule" in jobs, "Il manque le job 'molecule' (tests de rôle)"


def test_lint_job_runs_ansible_lint():
    steps = _config()["jobs"]["lint"].get("steps") or []
    cmds = " ".join(s.get("run", "") for s in steps if isinstance(s, dict))
    assert "ansible-lint" in cmds, (
        "Le job lint doit exécuter ansible-lint (étape 'run:')"
    )
    assert "--profile" in cmds and "production" in cmds, (
        "ansible-lint doit être lancé avec --profile=production (profil le plus strict)"
    )
    assert "yamllint" in cmds, "Le job lint doit aussi exécuter yamllint"


def test_molecule_job_uses_matrix_strategy():
    """Matrice multi-distros + multi-versions ansible-core."""
    job = _config()["jobs"]["molecule"]
    matrix = job.get("strategy", {}).get("matrix")
    assert matrix, (
        "Le job molecule doit déclarer strategy.matrix (distro x version ansible-core)"
    )
    assert "distro" in matrix, "La matrice doit avoir un axe 'distro'"
    assert "ansible" in matrix, "La matrice doit avoir un axe 'ansible' (versions ansible-core)"
    assert len(matrix["distro"]) >= 2, "Au moins 2 distros dans la matrice"
    assert len(matrix["ansible"]) >= 2, "Au moins 2 versions d'ansible-core dans la matrice"


def test_molecule_job_fail_fast_disabled():
    strategy = _config()["jobs"]["molecule"].get("strategy", {})
    assert strategy.get("fail-fast") is False, (
        "fail-fast: false attendu : une combinaison qui échoue ne doit pas "
        "annuler les autres (rapport complet)"
    )


def test_molecule_job_depends_on_lint():
    """Le job molecule ne tourne que si lint passe."""
    needs = _config()["jobs"]["molecule"].get("needs")
    assert needs == "lint" or (isinstance(needs, list) and "lint" in needs), (
        "Le job molecule doit déclarer needs: lint (chaînage lint -> molecule)"
    )


def test_actions_pinned_by_sha():
    """Toutes les actions externes épinglées par SHA (sécurité supply chain)."""
    content = WORKFLOW.read_text()
    uses = re.findall(r"uses:\s+(\S+)", content)
    assert uses, "Aucune action 'uses:' trouvée : le workflow est-il complété ?"
    for ref in uses:
        assert "@" in ref, f"Action sans référence : {ref}"
        sha = ref.rsplit("@", 1)[1]
        assert re.fullmatch(r"[0-9a-f]{40}", sha), (
            f"Action non épinglée par SHA de 40 caractères : {ref} "
            "(un tag comme @v4 peut être déplacé, un SHA non)"
        )


def test_permissions_minimal():
    """permissions: {} au niveau global (moindre privilège)."""
    config = _config()
    assert "permissions" in config, (
        "Déclarez 'permissions:' au niveau global du workflow"
    )
    assert config["permissions"] == {}, (
        "Le global doit être le plus strict possible : permissions: {} "
        "(réélargissez ensuite job par job)"
    )


def test_persist_credentials_false():
    """Chaque checkout désactive la persistance du token."""
    content = WORKFLOW.read_text()
    nb_checkout = content.count("actions/checkout@")
    assert nb_checkout >= 2, (
        "Chaque job doit faire son propre checkout (au moins 2 attendus)"
    )
    assert content.count("persist-credentials: false") >= nb_checkout, (
        "Chaque actions/checkout doit poser persist-credentials: false "
        "(sinon le token reste lisible dans .git/config)"
    )


def test_workflow_passes_actionlint():
    """Exécute réellement actionlint sur le workflow.

    Un workflow qui ne passe pas son linter officiel n'a aucune chance de
    tourner sur GitHub. Skip honnête si le binaire n'est pas installé.
    """
    if shutil.which("actionlint") is None:
        pytest.skip(
            "actionlint absent du poste : installez-le "
            "(https://github.com/rhysd/actionlint) pour valider ce point"
        )
    result = subprocess.run(
        ["actionlint", "-no-color", str(WORKFLOW)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"actionlint signale des erreurs dans le workflow :\n{result.stdout}{result.stderr}"
    )
