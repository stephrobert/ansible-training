"""Tests structurels lab 98 — ansible-pull (hors EX294).

Lab tests structurels : on vérifie le repo Git + le script orchestrateur.
Pas de connexion à db1.lab requise (le pull n'est pas un vrai test
infrastructure, c'est un pattern de mise en œuvre).
"""

from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
REPO_PULL = LAB_DIR / "repo-pull"
SOLUTION_SH = LAB_DIR / "challenge" / "solution.sh"


def test_repo_pull_dir_exists():
    assert REPO_PULL.is_dir(), (
        f"{REPO_PULL} absent — créez le mini-repo Git en suivant les indices."
    )


def test_repo_pull_has_git_dir():
    git_dir = REPO_PULL / ".git"
    assert git_dir.is_dir(), (
        f"{git_dir} absent — initialisez le repo : "
        "cd repo-pull && git init && git add . && git commit -m initial"
    )


def test_pull_playbook_exists():
    pb = REPO_PULL / "pull-playbook.yml"
    assert pb.is_file(), f"{pb} absent dans le repo-pull/"


def test_pull_playbook_targets_localhost():
    """Le playbook doit cibler localhost + connection: local (pattern pull)."""
    pb = REPO_PULL / "pull-playbook.yml"
    content = pb.read_text()
    assert "localhost" in content, (
        "pull-playbook.yml doit avoir hosts: localhost (pattern ansible-pull)"
    )
    assert "connection: local" in content or "connection:\n  local" in content, (
        "pull-playbook.yml doit avoir connection: local (pattern ansible-pull)"
    )


def test_pull_playbook_uses_fqcn_copy():
    pb = REPO_PULL / "pull-playbook.yml"
    content = pb.read_text()
    assert "ansible.builtin.copy" in content, (
        "Le playbook doit utiliser ansible.builtin.copy (FQCN)"
    )


def test_solution_sh_exists():
    assert SOLUTION_SH.is_file(), (
        f"{SOLUTION_SH} absent — créez le script orchestrateur."
    )


def test_solution_sh_invokes_ansible_pull():
    """Le script doit invoquer ansible-pull (pas ansible-playbook)."""
    content = SOLUTION_SH.read_text()
    assert "ansible-pull" in content, (
        "solution.sh doit invoquer ansible-pull (pas ansible-playbook). "
        "C'est la base du mode pull."
    )


def test_solution_sh_uses_url_or_path():
    """Le script doit passer -U avec une URL ou un chemin."""
    content = SOLUTION_SH.read_text()
    assert "-U " in content or "--url " in content, (
        "solution.sh doit passer -U <url-ou-chemin> à ansible-pull"
    )
