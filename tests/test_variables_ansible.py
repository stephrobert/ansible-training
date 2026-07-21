"""Vérifie que les variables `ANSIBLE_*` citées par les labs existent vraiment.

Une variable d'environnement inventée est le pire cas pédagogique : l'apprenant
la pose, rien ne se passe, aucune erreur ne s'affiche, et il conclut que l'outil
est cassé. Aucun test fonctionnel ne peut l'attraper, puisque la variable n'a
justement aucun effet.

Deux cas réels trouvés dans ce dépôt, tous deux dans des labs de dépannage :

- `ANSIBLE_DEBUGGER_IGNORE_ERRORS`, proposée pour désactiver le débogueur en CI.
  Elle n'existe pas, et la variable au nom proche
  (`ANSIBLE_TASK_DEBUGGER_IGNORE_ERRORS`) fait l'inverse : elle *invoque* le
  débogueur sur une tâche portant `ignore_errors: true`.
- `ANSIBLE_PROFILE_TASKS=1`, proposée pour activer le profilage. Mesuré : zéro
  ligne de profilage. Un callback s'active par `ANSIBLE_CALLBACKS_ENABLED`.

La référence est `ansible-config list`, c'est-à-dire ce que l'ansible-core
installé reconnaît réellement — pas une liste maintenue à la main qui prendrait
du retard à chaque montée de version.

**Ce module n'est pas collecté par la suite normale** : `testpaths = ["labs"]`
limite la collecte aux challenges. On le lance à la demande :

    pytest tests/test_variables_ansible.py -v
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.resolve()
LABS = REPO_ROOT / "labs"

VARIABLE = re.compile(r"\bANSIBLE_[A-Z0-9_]+")

# Fichiers à ne pas auditer : ce ne sont pas nos énoncés.
EXCLUS = ("/challenge/deps/", "/local_collections/", "/ansible_collections/", "/__pycache__/")

SUFFIXES = {".md", ".yml", ".yaml", ".sh", ".cfg"}

# Variables légitimes qu'`ansible-config list` ne connaît pas.
#
# - ANSIBLE_CONFIG : lue avant le chargement de la config, donc absente de la
#   liste des réglages, mais parfaitement réelle.
# - ANSIBLE_NAVIGATOR_* : réglages d'ansible-navigator, un autre outil.
# - ANSIBLE_GALAXY_TOKEN : jeton lu par la CLI galaxy.
# - les autres : variables propres au dépôt ou inventées par un lab pour son
#   propre usage (elles ne prétendent pas piloter ansible-core).
CONNUES_HORS_CONFIG = {
    # En-tête des fichiers chiffrés (`$ANSIBLE_VAULT;1.1;AES256`), pas une
    # variable d'environnement : la regex la ramasse, le contrôle ne s'y applique pas.
    "ANSIBLE_VAULT",
    "ANSIBLE_CONFIG",
    "ANSIBLE_GALAXY_TOKEN",
    "ANSIBLE_NAVIGATOR_CONFIG",
    "ANSIBLE_NAVIGATOR_EE_IMAGE",
    "ANSIBLE_NAVIGATOR_MODE",
    "ANSIBLE_TRAINING",
    "ANSIBLE_TRAINING_ROOT",
    "ANSIBLE_CFG",
    "ANSIBLE_VERSION",
    "ANSIBLE_VERSIONS",
    "ANSIBLE_VAULT_PASSWORD_FILE_DEV",
    "ANSIBLE_VAULT_PASSWORD_FILE_PROD",
}


def _variables_reconnues() -> set[str]:
    """Ce que l'ansible-core installé reconnaît, d'après lui-même."""
    out = subprocess.run(
        ["ansible-config", "list"], capture_output=True, text=True, check=False
    ).stdout
    if not out:
        pytest.skip("ansible-config indisponible : impossible de valider les variables")
    return set(re.findall(r"name:\s+(ANSIBLE_[A-Z0-9_]+)", out))


def _fichiers() -> list[Path]:
    return sorted(
        p
        for p in LABS.rglob("*")
        if p.is_file()
        and p.suffix in SUFFIXES
        and not any(x in str(p) for x in EXCLUS)
    )


# Variables citées VOLONTAIREMENT comme n'existant pas, pour prévenir l'erreur.
# Les nommer reste utile : c'est ce que l'apprenant risque de taper. Le test doit
# donc les tolérer là où le texte explique justement qu'elles sont fausses.
CONTRE_EXEMPLES = {
    "ANSIBLE_PROFILE_TASKS",          # cf. troubleshooting/idempotence-perfs
    "ANSIBLE_DEBUGGER_IGNORE_ERRORS",  # cf. troubleshooting/debugger
}

RECONNUES = _variables_reconnues()
FICHIERS = _fichiers()


def test_il_y_a_des_fichiers_a_auditer() -> None:
    """Garde-fou : sans lui, un glob cassé rendrait la suite verte à vide."""
    assert FICHIERS, "aucun fichier de lab trouvé : le parcours est cassé"


@pytest.mark.parametrize("fichier", FICHIERS, ids=lambda p: str(p.relative_to(LABS)))
def test_les_variables_ansible_citees_existent(fichier: Path) -> None:
    citees = set(VARIABLE.findall(fichier.read_text(encoding="utf-8", errors="ignore")))
    inconnues = sorted(citees - RECONNUES - CONNUES_HORS_CONFIG - CONTRE_EXEMPLES)

    assert not inconnues, (
        f"{fichier.relative_to(REPO_ROOT)} cite {len(inconnues)} variable(s) "
        f"qu'ansible-core ne reconnaît pas : {', '.join(inconnues)}.\n\n"
        "Une variable inventée ne produit aucune erreur : l'apprenant la pose, rien "
        "ne se passe, et il croit à un bug de l'outil. Vérifiez le nom exact avec "
        "`ansible-config list | grep <MOTIF>`.\n"
        "Si la variable est légitime mais absente de la liste (autre outil, ou "
        "variable propre au dépôt), ajoutez-la à CONNUES_HORS_CONFIG dans ce test, "
        "avec la raison."
    )
