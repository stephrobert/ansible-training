"""Tests des pipelines CI EE écrits par l'apprenant (lab 87).

Les deux pipelines (GitHub Actions et GitLab CI) sont livrés en squelette :
ces tests ne passent que lorsque l'apprenant les a réellement écrits
(build, scan Trivy bloquant, push, signature cosign, épinglage SHA).
actionlint est exécuté en plus si le binaire est présent sur le poste.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

LAB_DIR = Path(__file__).resolve().parents[2]
GH_WORKFLOW = LAB_DIR / ".github" / "workflows" / "build-ee.yml"
GITLAB_CI = LAB_DIR / ".gitlab-ci.yml"


def _etapes(workflow):
    """Toutes les étapes (`steps`) déclarées dans le workflow, tous jobs confondus.

    On parcourt la STRUCTURE YAML et jamais le texte : les tests qui faisaient
    `"cosign" in content` étaient satisfaits par le CAHIER DES CHARGES en
    commentaire du squelette, qui cite justement les chaînes attendues. Cinq
    tests sur onze passaient donc sans qu'une ligne soit écrite.
    """
    config = yaml.safe_load(workflow.read_text()) or {}
    etapes = []
    for job in (config.get("jobs") or {}).values():
        etapes.extend(job.get("steps") or [])
    return etapes


def test_github_workflow_exists():
    assert GH_WORKFLOW.is_file(), (
        "Le fichier .github/workflows/build-ee.yml doit exister (squelette livré)"
    )


def test_github_workflow_pins_actions_by_sha():
    content = GH_WORKFLOW.read_text()
    uses = re.findall(r"uses:\s+(\S+)", content)
    assert uses, "Aucune action 'uses:' trouvée : le workflow est-il complété ?"
    for ref in uses:
        assert "@" in ref, f"Action sans référence : {ref}"
        sha = ref.rsplit("@", 1)[1]
        assert re.fullmatch(r"[0-9a-f]{40}", sha), (
            f"Action non épinglée par SHA de 40 caractères : {ref} "
            "(un tag peut être déplacé, un SHA non)"
        )


def test_github_workflow_has_minimal_permissions():
    config = yaml.safe_load(GH_WORKFLOW.read_text())
    assert config.get("permissions") == {}, (
        "Les permissions globales doivent être {} : le moindre privilège se "
        "réélargit ensuite job par job (contents, packages, id-token)"
    )


def test_github_workflow_job_grants_id_token_for_cosign():
    config = yaml.safe_load(GH_WORKFLOW.read_text())
    jobs = config.get("jobs", {})
    granted = any(
        job.get("permissions", {}).get("id-token") == "write"
        for job in jobs.values()
        if isinstance(job, dict)
    )
    assert granted, (
        "La signature cosign keyless (OIDC) exige 'id-token: write' dans les "
        "permissions du job de build"
    )


def test_github_workflow_uses_persist_credentials_false():
    """Le `with:` du checkout doit porter persist-credentials: false."""
    checkouts = [
        e for e in _etapes(GH_WORKFLOW)
        if "actions/checkout" in str(e.get("uses", ""))
    ]
    assert checkouts, "Aucune étape actions/checkout dans le workflow."
    for e in checkouts:
        assert (e.get("with") or {}).get("persist-credentials") is False, (
            "actions/checkout doit poser persist-credentials: false dans son "
            "`with:` (sinon le token reste lisible dans .git/config). "
            f"Vu : {e.get('with')}"
        )


def test_github_workflow_runs_trivy_scan():
    """Une étape doit lancer Trivy, et il doit être BLOQUANT."""
    trivy = [
        e for e in _etapes(GH_WORKFLOW)
        if "trivy" in (str(e.get("uses", "")) + str(e.get("run", ""))).lower()
    ]
    assert trivy, (
        "Il manque l'étape de scan Trivy de l'image EE (aucun `uses:` ni "
        "`run:` ne la mentionne)."
    )
    bloquant = any(
        str((e.get("with") or {}).get("exit-code", "")) == "1"
        or "--exit-code 1" in str(e.get("run", ""))
        for e in trivy
    )
    assert bloquant, (
        "Trivy doit être BLOQUANT : exit-code: '1' sur HIGH/CRITICAL, sinon le "
        "scan est purement cosmétique et le pipeline reste vert sur une image "
        "vulnérable."
    )


def test_github_workflow_signs_with_cosign():
    """Une étape doit réellement signer l'image avec cosign."""
    cosign = [
        e for e in _etapes(GH_WORKFLOW)
        if "cosign" in (str(e.get("uses", "")) + str(e.get("run", ""))).lower()
    ]
    assert cosign, (
        "Il manque la signature cosign de l'image (keyless OIDC recommandé). "
        "Aucun `uses:` ni `run:` ne mentionne cosign."
    )


def test_gitlab_ci_exists_and_has_4_stages():
    assert GITLAB_CI.is_file(), "Le fichier .gitlab-ci.yml doit exister (squelette livré)"
    data = yaml.safe_load(GITLAB_CI.read_text())
    stages = data.get("stages", [])
    for stage in ("build", "scan", "push", "sign"):
        assert stage in stages, (
            f"Le stage '{stage}' doit être déclaré dans stages: "
            "(pipeline en 4 temps : build, scan, push, sign)"
        )


def test_gitlab_ci_has_a_job_per_stage():
    data = yaml.safe_load(GITLAB_CI.read_text())
    reserved = {"stages", "variables", "default", "include", "workflow", "image"}
    jobs = {k: v for k, v in data.items() if k not in reserved and isinstance(v, dict)}
    used_stages = {job.get("stage") for job in jobs.values()}
    for stage in ("build", "scan", "push", "sign"):
        assert stage in used_stages, (
            f"Aucun job ne porte stage: {stage} : chaque stage déclaré doit "
            "avoir son job"
        )


def test_ee_yaml_uses_v3():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    assert data.get("version") == 3, (
        "execution-environment.yml doit déclarer version: 3 (schéma builder v3)"
    )


def test_github_workflow_passes_actionlint():
    """Exécute réellement actionlint sur le workflow (skip si absent)."""
    if shutil.which("actionlint") is None:
        pytest.skip(
            "actionlint absent du poste : installez-le "
            "(https://github.com/rhysd/actionlint) pour valider ce point"
        )
    result = subprocess.run(
        ["actionlint", "-no-color", str(GH_WORKFLOW)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"actionlint signale des erreurs dans le workflow :\n{result.stdout}{result.stderr}"
    )
