"""Vérifie qu'aucune solution de formateur n'est en clair dans `solution/`.

Une solution en clair spoile le lab, et l'historique git la conserve : une fois
poussée, la retirer ne suffit plus. Le contrôle mérite donc d'être mécanique.

Ce module double `scripts/check-solutions-encrypted.sh` (tâche `mise run
solutions-status`) sous forme de test, pour qu'il tombe au même endroit que les
autres vérifications de catalogue et nomme précisément le fichier fautif.

Le risque n'est pas théorique : corriger une solution impose de la déchiffrer,
puis de la re-chiffrer. Un `ansible-vault encrypt` oublié en fin de manipulation
laisse la réponse lisible dans le dépôt, sans que rien ne le signale.

**Ce module n'est pas collecté par la suite normale** : `testpaths = ["labs"]`
dans `pyproject.toml` limite la collecte aux challenges. On le lance à la
demande, et il est instantané (aucun réseau, aucune VM) :

    pytest tests/test_solutions_chiffrees.py -v
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOLUTION_DIR = REPO_ROOT / "solution"
VAULT_HEADER = b"$ANSIBLE_VAULT"

# Rien à chiffrer dans ces fichiers de service.
EXEMPTS = {".gitkeep", ".gitignore"}


def _fichiers_suivis() -> list[Path]:
    """Fichiers de `solution/` que git suit réellement.

    On s'aligne sur le script : un fichier non suivi ne partira pas dans un
    commit, donc il ne peut pas fuiter. Inclure les non-suivis ferait échouer le
    test sur des artefacts de travail locaux (un déchiffrement en cours, par
    exemple), ce qui n'apporterait rien.
    """
    if not SOLUTION_DIR.is_dir():
        return []
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", "solution"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    fichiers = []
    for rel in out.split(b"\0"):
        if not rel:
            continue
        p = REPO_ROOT / rel.decode()
        if p.name in EXEMPTS or not p.is_file():
            continue
        if p.stat().st_size == 0:  # un fichier vide ne révèle rien
            continue
        fichiers.append(p)
    return fichiers


SOLUTIONS = _fichiers_suivis()


def test_le_repertoire_solution_est_bien_peuple() -> None:
    """Garde-fou : sans lui, un `git ls-files` cassé rendrait la suite verte à vide."""
    assert SOLUTIONS, (
        "aucun fichier suivi trouvé sous solution/ : le parcours est cassé, "
        "ou le dépôt n'a pas de solutions (auquel cas ce test n'a pas lieu d'être)"
    )


@pytest.mark.parametrize(
    "fichier",
    SOLUTIONS,
    ids=lambda p: str(p.relative_to(SOLUTION_DIR)),
)
def test_la_solution_est_chiffree(fichier: Path) -> None:
    entete = fichier.read_bytes()[: len(VAULT_HEADER)]

    assert entete == VAULT_HEADER, (
        f"{fichier.relative_to(REPO_ROOT)} n'est PAS chiffré.\n\n"
        "Une solution en clair spoile le lab, et git en garde la trace même après "
        "correction. Re-chiffrez avant de committer :\n"
        f"  ansible-vault encrypt --vault-password-file .vault-pass "
        f"{fichier.relative_to(REPO_ROOT)}"
    )
