"""Tests pytest pour le challenge « versionner ses playbooks avec Git ».

Ce lab est local au control node : pas de VM, pas de testinfra/SSH.

Le principe : le test EXÉCUTE le `solution.sh` (celui de l'apprenant, ou la
référence déchiffrée en mode formateur, résolus par `lab_script`), puis il
INSPECTE l'état réel du dépôt Git que le script a produit. Il ne cherche jamais
une chaîne dans le texte du script : « le script contient git commit » est
forgeable et ne prouve rien. On interroge la base d'objets Git en lecture
(`git log`, `ls-files`, `rev-parse`, `ls-remote`, `config --local`), ce qui ne
peut être satisfait qu'en ayant réellement initialisé, committé et poussé.

Le dépôt vit dans `challenge/work/` (gitignoré) : rien ne remonte vers le dépôt
Git du dépôt ansible-training.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import lab_script

CHALLENGE_DIR = Path(__file__).resolve().parent.parent  # .../challenge
WORK = CHALLENGE_DIR / "work"
REPO = WORK / "playbooks"        # dépôt de travail attendu
BARE = WORK / "playbooks.git"    # remote bare local attendu


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Lance `git -C <repo> <args>` et renvoie le résultat brut (sans lever)."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def run_solution() -> subprocess.CompletedProcess:
    """Repart d'un workdir vierge, exécute le script, rend son résultat.

    Le nettoyage AVANT exécution est essentiel : sans lui, un dépôt laissé par
    un run précédent masquerait un script devenu incapable de le recréer (le
    contrôle négatif passerait à tort). `challenge/work/` est gitignoré, donc
    ce rmtree ne touche jamais un fichier suivi du dépôt parent.
    """
    if WORK.exists():
        shutil.rmtree(WORK)
    script = lab_script(__file__)  # apprenant, sinon référence déchiffrée (tmp)
    return subprocess.run(
        [str(script)],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_script_reussit(run_solution):
    """Le script se termine proprement (exit 0)."""
    assert run_solution.returncode == 0, (
        f"solution.sh a échoué (exit {run_solution.returncode}).\n"
        f"stdout : {run_solution.stdout}\n"
        f"stderr : {run_solution.stderr}"
    )


def test_depot_initialise(run_solution):
    """Un dépôt Git est réellement initialisé dans le workdir."""
    assert (REPO / ".git").is_dir(), (
        f"Aucun dépôt Git dans {REPO}. Le script doit faire `git init`."
    )
    res = _git(REPO, "rev-parse", "--is-inside-work-tree")
    assert res.returncode == 0 and res.stdout.strip() == "true", (
        "`git rev-parse --is-inside-work-tree` ne confirme pas un dépôt valide : "
        f"{res.stdout}{res.stderr}"
    )


def test_playbooks_suivis(run_solution):
    """Des playbooks sont réellement SUIVIS (indexés), pas juste posés sur le disque."""
    res = _git(REPO, "ls-files")
    assert res.returncode == 0, res.stderr
    tracked = [f for f in res.stdout.splitlines() if f.strip()]
    assert tracked, (
        "`git ls-files` est vide : des fichiers ont peut-être été créés, mais "
        "aucun n'a été `git add`. Suivre les playbooks est le cœur du lab."
    )
    assert any(f.endswith((".yml", ".yaml")) for f in tracked), (
        f"Aucun playbook (.yml/.yaml) suivi. Fichiers suivis : {tracked}"
    )


def test_historique_a_deux_commits(run_solution):
    """Le dépôt porte un VRAI historique : au moins deux commits.

    L'énoncé demande un premier commit PUIS un second, « pour construire un
    historique ». Un dépôt à un seul commit n'a pas d'historique à comparer : il
    ne prouve pas le cycle add/commit répété. On exige donc >= 2 commits, fidèle
    à la solution de référence qui committe le projet initial puis le playbook
    webserver séparément.
    """
    res = _git(REPO, "log", "--oneline")
    assert res.returncode == 0, (
        "`git log` échoue : aucun commit n'existe. Des fichiers `git add`és mais "
        f"jamais committés laissent un dépôt sans historique.\n{res.stderr}"
    )
    commits = [line for line in res.stdout.splitlines() if line.strip()]
    assert len(commits) >= 2, (
        "L'historique doit contenir au moins deux commits (un premier commit, "
        f"puis un second pour construire l'historique). Commits trouvés : {len(commits)}."
    )


def test_branche_main(run_solution):
    """Le dépôt travaille sur la branche `main`, pas `master`.

    L'énoncé impose `git init -b main` (et un push de `main`). Sans cette
    assertion, un dépôt initialisé sur `master` passerait tous les autres tests.
    On lit la branche courante depuis la ref symbolique HEAD du dépôt de preuve.
    """
    branch = _git(REPO, "branch", "--show-current").stdout.strip()
    assert branch == "main", (
        f"La branche courante est « {branch or '(détachée)'} », attendu « main ». "
        "Initialisez le dépôt avec `git init -b main`."
    )


def test_message_de_commit_non_vide(run_solution):
    """Le dernier commit porte un message non vide (pas un commit fantôme)."""
    subject = _git(REPO, "log", "-1", "--pretty=%s").stdout.strip()
    assert subject, "Le dernier commit n'a pas de message : `git commit -m \"...\"`."


def test_identite_auteur_locale(run_solution):
    """Une identité d'auteur est posée EN LOCAL sur le dépôt.

    On lit la config `--local` (donc .git/config du dépôt), pas la config
    globale du poste : cela prouve que l'apprenant a posé user.name/user.email
    sur CE dépôt, et non qu'une identité ambiante existait déjà.
    """
    name = _git(REPO, "config", "--local", "user.name").stdout.strip()
    email = _git(REPO, "config", "--local", "user.email").stdout.strip()
    assert name, "Aucun user.name local : `git config user.name \"...\"`."
    assert email, "Aucun user.email local : `git config user.email \"...\"`."


def test_arbre_de_travail_propre(run_solution):
    """Après commit, l'arbre est propre : tout est committé, rien ne traîne.

    Un fichier créé mais oublié au commit apparaîtrait ici (`??` ou ` M`).
    Exiger un `git status --porcelain` vide prouve que le add + commit ont été
    menés jusqu'au bout.
    """
    res = _git(REPO, "status", "--porcelain")
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == "", (
        "L'arbre de travail n'est pas propre : des changements ne sont ni "
        f"committés ni ignorés.\n{res.stdout}"
    )


def test_push_recu_par_le_bare(run_solution):
    """Le remote bare local a REÇU le push : même commit que le HEAD local.

    C'est la preuve non forgeable de « push » sans réseau : on compare le SHA
    du HEAD local aux références publiées dans le bare (`git ls-remote`). Un
    script qui prétendrait pousser sans le faire laisserait un bare sans
    branche, et cette comparaison échouerait.
    """
    assert (BARE / "HEAD").is_file(), (
        f"Aucun dépôt bare dans {BARE}. Le script doit `git init --bare` la "
        "cible du push."
    )
    local_head = _git(REPO, "rev-parse", "HEAD").stdout.strip()
    assert local_head, "HEAD local introuvable."

    res = _git(REPO, "ls-remote", str(BARE))
    assert res.returncode == 0, (
        f"`git ls-remote` sur le bare échoue : {res.stderr}"
    )
    heads = {
        parts[1]: parts[0]
        for line in res.stdout.splitlines()
        if (parts := line.split()) and len(parts) >= 2 and parts[1].startswith("refs/heads/")
    }
    assert heads, (
        "Le bare n'a aucune branche : rien n'a été poussé. `git push origin main`."
    )
    assert local_head in heads.values(), (
        f"Le HEAD local ({local_head[:8]}) n'a pas été poussé vers le bare. "
        f"Branches côté bare : {heads}"
    )
