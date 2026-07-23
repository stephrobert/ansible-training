"""Tests du pipeline GitLab CI écrit par l'apprenant (lab 70).

Le .gitlab-ci.yml est livré en squelette : ces tests ne passent que
lorsque l'apprenant l'a réellement complété. Ils chargent le YAML et
contrôlent la sémantique (stages, matrice, needs, rules sur tag).

Exécution réelle du pipeline : elle exigerait un runner GitLab ou
`gitlab-ci-local` + Docker, trop lourds pour ce harnais. On valide donc la
sémantique du fichier, qui est l'objet du lab (l'exécution cloud se fait
en poussant sur GitLab).
"""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
GITLAB_CI = LAB_ROOT / ".gitlab-ci.yml"


def _config():
    return yaml.safe_load(GITLAB_CI.read_text())


def test_gitlab_ci_present():
    assert GITLAB_CI.exists(), "Le fichier .gitlab-ci.yml doit exister (squelette livré)"


def test_pipeline_has_three_stages():
    stages = _config().get("stages", [])
    for stage in ("lint", "test", "release"):
        assert stage in stages, (
            f"Le stage '{stage}' doit être déclaré dans stages: "
            "(pipeline en trois temps : lint, test, release)"
        )


def test_ansible_lint_job_present():
    config = _config()
    assert "ansible-lint" in config, "Il manque le job 'ansible-lint'"
    job = config["ansible-lint"]
    assert job.get("stage") == "lint", "Le job ansible-lint doit être dans le stage 'lint'"
    script = " ".join(str(line) for line in job.get("script", []))
    assert "ansible-lint" in script, "Le job doit exécuter ansible-lint dans son script"
    assert "production" in script, (
        "ansible-lint doit être lancé avec --profile=production (profil le plus strict)"
    )
    assert "yamllint" in script, "Le job doit aussi exécuter yamllint"


def test_molecule_test_uses_parallel_matrix():
    """Matrice multi-distros / multi-versions via parallel:matrix."""
    config = _config()
    assert "molecule-test" in config, "Il manque le job 'molecule-test'"
    job = config["molecule-test"]
    assert "parallel" in job, (
        "Le job molecule-test doit déclarer parallel:matrix (exécution en éventail)"
    )
    matrix = job["parallel"].get("matrix", [])
    assert isinstance(matrix, list), "parallel.matrix doit être une liste de combinaisons"
    nb_combos = 0
    for entry in matrix:
        sizes = [len(v) if isinstance(v, list) else 1 for v in entry.values()]
        combo = 1
        for s in sizes:
            combo *= s
        nb_combos += combo
    assert nb_combos >= 3, (
        f"Au moins 3 combinaisons DISTRO x ANSIBLE_VERSION attendues, vu : {nb_combos}"
    )


def test_molecule_test_depends_on_lint():
    needs = _config()["molecule-test"].get("needs", [])
    assert "ansible-lint" in needs, (
        "molecule-test doit déclarer needs: [\"ansible-lint\"] "
        "(pas de tests si le lint échoue)"
    )


def test_release_only_on_tag():
    """Le job release n'est déclenché que sur un tag Git."""
    config = _config()
    assert "release" in config, "Il manque le job 'release'"
    job = config["release"]
    assert job.get("stage") == "release", "Le job release doit être dans le stage 'release'"
    rules = job.get("rules", [])
    assert any("CI_COMMIT_TAG" in str(r.get("if", "")) for r in rules), (
        "Le job release doit porter une règle 'if: $CI_COMMIT_TAG' "
        "(publication uniquement sur tag Git)"
    )


def test_no_secrets_in_yaml():
    """Pas de tokens ni de secrets en clair dans .gitlab-ci.yml."""
    content = GITLAB_CI.read_text().lower()
    forbidden = ["password:", "secret:", "api_key=", "token="]
    for f in forbidden:
        assert f not in content, (
            f"Motif interdit '{f}' trouvé : les secrets passent par les "
            "CI/CD Variables GitLab (masked + protected), jamais dans le YAML"
        )
