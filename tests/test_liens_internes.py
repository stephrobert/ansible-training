"""Vérifie que les liens relatifs des README pointent vers un fichier existant.

Pendant local de `test_doc_urls.py` : celui-ci vérifie les guides en ligne,
celui-là les renvois internes au dépôt. Aucun réseau, donc rapide et
déterministe.

Ce que ça attrape, et qui était bien réel avant d'écrire ce test :

- **la profondeur fausse** : 112 README pointaient `../../README.md` depuis
  `labs/<section>/<lab>/`, ce qui vise `labs/README.md`, un fichier qui n'existe
  pas. Il manquait un niveau ;
- **l'ancienne numérotation** : 38 renvois du type `../62-roles-molecule-introduction/`,
  restés après le passage de `NN-section-lab` à `section/lab`.

Aucun de ces liens ne cassait un test : ils cassaient seulement la navigation de
l'apprenant, silencieusement. C'est exactement le genre de dérive qu'un test
attrape mieux qu'une relecture.

Lancement (le module n'est pas dans `testpaths`, cf. pyproject.toml) :

    pytest tests/test_liens_internes.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.resolve()
LABS = REPO_ROOT / "labs"

# [libellé](cible) où cible est relatif (commence par ./ ou ../).
# Les URL absolues sont du ressort de test_doc_urls.py.
LIEN_RELATIF = re.compile(r"\[[^\]]*\]\((\.\.?/[^)]+)\)")


def _fichiers_markdown() -> list[Path]:
    return sorted(LABS.rglob("*.md"))


def _liens_casses(fichier: Path) -> list[str]:
    """Cibles relatives introuvables depuis ce fichier.

    L'ancre (`#section`) est retirée avant de tester le chemin : elle est
    résolue par le lecteur Markdown, pas par le système de fichiers.
    """
    contenu = fichier.read_text(encoding="utf-8", errors="ignore")
    casses = []
    for cible in LIEN_RELATIF.findall(contenu):
        chemin = (fichier.parent / cible.split("#")[0]).resolve()
        if not chemin.exists():
            casses.append(cible)
    return casses


def test_il_y_a_des_markdown_a_verifier() -> None:
    """Garde-fou : sans lui, un glob cassé rendrait la suite verte à vide."""
    assert _fichiers_markdown(), "aucun .md trouvé sous labs/ : le parcours est cassé"


@pytest.mark.parametrize(
    "fichier",
    _fichiers_markdown(),
    ids=lambda p: str(p.relative_to(LABS)),
)
def test_les_liens_relatifs_pointent_vers_un_fichier_existant(fichier: Path) -> None:
    casses = _liens_casses(fichier)

    assert not casses, (
        f"{fichier.relative_to(REPO_ROOT)} contient {len(casses)} lien(s) mort(s) :\n"
        + "\n".join(f"  - {c}" for c in casses)
        + "\n\nUn renvoi vers un lab utilise son chemin réel (`../../<section>/<lab>/`), "
        "jamais l'ancienne numérotation `NN-section-lab`. Pour le README racine "
        "depuis un lab, compter les niveaux : `../../../README.md`."
    )
