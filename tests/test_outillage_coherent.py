"""Vérifie que l'outillage du dépôt est cohérent avec lui-même.

Ce module existe à cause d'un incident réel : au cours d'une session de travail,
`tests/test_solutions_chiffrees.py` puis le hook `internal-links` de
`.pre-commit-config.yaml` ont disparu, sans qu'aucune opération git ne l'explique
(le reflog ne montre ni `checkout`, ni `restore`, ni `clean`). Plusieurs
processus écrivent dans ce dépôt ; une édition concurrente peut donc défaire une
modification sans rien signaler.

Une disparition de ce genre est silencieuse par nature : un test absent ne
proteste pas, un hook absent ne se déclenche plus. Le seul remède est de rendre
l'incohérence détectable, ce que fait ce module :

1. tout hook local qui lance un test pointe vers un fichier qui existe ;
2. tout vérificateur de catalogue est soit câblé en pre-commit, soit
   explicitement recensé comme « à la demande » (avec sa raison).

Le second point est le plus utile : un test présent mais débranché passe
totalement inaperçu, alors qu'il ne protège plus rien.

    pytest tests/test_outillage_coherent.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.resolve()
TESTS_DIR = REPO_ROOT / "tests"
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"

# Vérificateurs délibérément NON câblés en pre-commit, avec la raison.
# Les y mettre bloquerait un commit hors ligne ou ralentirait chaque commit.
HORS_PRE_COMMIT = {
    "test_doc_urls.py": "113 requêtes réseau : échouerait hors ligne ou site indisponible",
    "test_solutions_chiffrees.py": "déjà couvert par le hook `solutions-encrypted` (script)",
}


def _hooks_locaux() -> list[dict]:
    cfg = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8"))
    hooks = []
    for repo in cfg.get("repos", []):
        if repo.get("repo") == "local":
            hooks.extend(repo.get("hooks", []))
    return hooks


HOOKS = _hooks_locaux()


def test_le_pre_commit_declare_des_hooks_locaux() -> None:
    """Garde-fou : un parsing cassé rendrait les tests suivants verts à vide."""
    assert HOOKS, "aucun hook local trouvé dans .pre-commit-config.yaml"


@pytest.mark.parametrize(
    "hook",
    [h for h in HOOKS if "pytest tests/" in str(h.get("entry", ""))],
    ids=lambda h: str(h.get("id", "?")),
)
def test_le_hook_pointe_un_test_existant(hook: dict) -> None:
    cible = re.search(r"pytest (tests/[\w.]+\.py)", str(hook["entry"]))
    assert cible, f"entry inattendue pour le hook {hook['id']} : {hook['entry']}"
    chemin = REPO_ROOT / cible.group(1)

    assert chemin.is_file(), (
        f"Le hook `{hook['id']}` lance {cible.group(1)}, qui n'existe pas.\n"
        "Soit le fichier a été supprimé et le hook doit suivre, soit il a disparu "
        "accidentellement et il faut le restaurer."
    )


@pytest.mark.parametrize(
    "test_file",
    sorted(p.name for p in TESTS_DIR.glob("test_*.py")),
)
def test_le_verificateur_est_cable_ou_recense(test_file: str) -> None:
    """Un vérificateur présent mais débranché ne protège plus rien, en silence."""
    if test_file in HORS_PRE_COMMIT:
        pytest.skip(f"hors pre-commit assumé : {HORS_PRE_COMMIT[test_file]}")

    cable = any(test_file in str(h.get("entry", "")) for h in HOOKS)

    assert cable, (
        f"{test_file} existe dans tests/ mais aucun hook pre-commit ne le lance : "
        "il ne protège donc plus rien, sans que rien ne le signale.\n\n"
        "Soit ajoutez un hook local dans .pre-commit-config.yaml, soit inscrivez-le "
        "dans HORS_PRE_COMMIT (dans ce fichier) avec la raison de l'exclusion."
    )
