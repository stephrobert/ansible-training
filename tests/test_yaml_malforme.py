"""Un YAML de catalogue malformé se signale, il ne fait pas tomber l'outil.

Pourquoi ce fichier existe
--------------------------
Les vérificateurs de catalogue tournent en CI **sur le contenu d'une pull
request**. Le `lab.yaml` qu'ils lisent vient donc de quelqu'un d'autre, et il
peut être malformé.

Mesuré le 2026-09-15, avant correctif, sur un lab témoin dont le titre portait
un guillemet non fermé :

    check-labs-completude.py    TRACE PYTHON : yaml.scanner.ScannerError
    gen_catalog.py              TRACE PYTHON : yaml.scanner.ScannerError

Un contributeur recevait une trace Python au lieu du nom de son fichier. Pire,
un vérificateur qui tombe n'annonce pas que CE lab est mauvais : il annonce que
la CI est cassée, et les 112 autres labs ne sont plus vérifiés du tout.

Le contrat éprouvé ici est celui que la CLI dsoxlab s'applique déjà à
elle-même : un lab malformé est écarté avec un message, jamais au prix du
processus.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))

from lecture_yaml import YamlIllisible, lire_yaml


def ecrire(tmp_path: Path, contenu: str, nom: str = "lab.yaml") -> Path:
    fichier = tmp_path / nom
    fichier.write_text(contenu, encoding="utf-8")
    return fichier


# Chaque cas est une entrée qu'un contributeur peut réellement produire, ou
# qu'un fichier corrompu peut contenir. Aucun n'est théorique.
CAS_ILLISIBLES = [
    pytest.param('id: x\ntitle: "pas fermé\n', id="guillemet-non-ferme"),
    pytest.param("id: x\n\ttitle: tabulation\n", id="tabulation-en-indentation"),
    pytest.param("id: x\ntitle: [non, fermée\n", id="crochet-non-ferme"),
    pytest.param("id: x\n  title: indentation-folle\n", id="indentation-incoherente"),
    pytest.param("- juste\n- une\n- liste\n", id="racine-liste"),
    pytest.param("une simple chaîne", id="racine-chaine"),
    pytest.param("id: x\ntitle: *alias_inexistant\n", id="alias-non-defini"),
]


@pytest.mark.parametrize("contenu", CAS_ILLISIBLES)
def test_un_yaml_illisible_leve_une_erreur_nommee(tmp_path: Path, contenu: str) -> None:
    """Toujours YamlIllisible, jamais une exception de la bibliothèque YAML."""
    fichier = ecrire(tmp_path, contenu)
    with pytest.raises(YamlIllisible) as capture:
        lire_yaml(fichier)

    message = str(capture.value)
    assert fichier.name in message, (
        f"le message ne nomme pas le fichier fautif, un contributeur ne saura pas "
        f"lequel corriger : {message!r}"
    )
    assert "Traceback" not in message


def test_le_message_ne_fuit_pas_le_chemin_absolu(tmp_path: Path) -> None:
    """Le message porte le NOM du fichier, pas le chemin du runner.

    Un chemin `/home/runner/work/...` dans une sortie de CI n'apprend rien au
    contributeur et allonge la ligne qu'il doit lire.
    """
    fichier = ecrire(tmp_path, 'title: "pas fermé\n')
    with pytest.raises(YamlIllisible) as capture:
        lire_yaml(fichier)
    assert str(tmp_path) not in str(capture.value)


def test_un_yaml_valide_passe(tmp_path: Path) -> None:
    """Le contrôle doit aussi laisser passer ce qui est correct.

    Sans ce cas, une fonction qui lève toujours passerait tous les autres tests.
    """
    fichier = ecrire(tmp_path, "id: mon-lab\ntitle: Un titre\nlevel: system-hardening\n")
    assert lire_yaml(fichier)["id"] == "mon-lab"


def test_un_fichier_vide_donne_une_table_vide(tmp_path: Path) -> None:
    """Un fichier vide n'est pas illisible, il est vide.

    La distinction compte : les appelants font `.get()` sur le résultat, et un
    `None` leur exploserait à la figure une ligne plus loin.
    """
    assert lire_yaml(ecrire(tmp_path, "")) == {}
    assert lire_yaml(ecrire(tmp_path, "# que des commentaires\n")) == {}


def test_un_fichier_absent_est_signale(tmp_path: Path) -> None:
    with pytest.raises(YamlIllisible):
        lire_yaml(tmp_path / "jamais-ecrit.yaml")


def test_un_fichier_binaire_est_signale(tmp_path: Path) -> None:
    """Un `lab.yaml` qui n'est pas de l'UTF-8 arrive : fichier tronqué, mauvais
    encodage, binaire ajouté par erreur."""
    fichier = tmp_path / "lab.yaml"
    fichier.write_bytes(b"\xff\xfe\x00binaire")
    with pytest.raises(YamlIllisible) as capture:
        lire_yaml(fichier)
    assert "UTF-8" in str(capture.value)


def test_les_alias_imbriques_ne_font_pas_exploser_la_pile(tmp_path: Path) -> None:
    """Une bombe d'expansion YAML est une entrée hostile, pas un bug d'ici.

    Elle se refuse. Le point important est qu'elle se refuse SANS emporter le
    processus : c'est exactement la différence entre un vérificateur qui protège
    la CI et un vérificateur qui la casse.
    """
    bombe = "a: &a [x, x, x, x, x, x, x, x, x]\n"
    for i in range(1, 8):
        precedent = chr(ord("a") + i - 1)
        courant = chr(ord("a") + i)
        bombe += f"{courant}: &{courant} [{', '.join(['*' + precedent] * 9)}]\n"

    fichier = ecrire(tmp_path, bombe)
    # Lisible ou refusée, les deux sont acceptables ; ce qui ne l'est pas, c'est
    # une RecursionError ou un MemoryError qui remonte.
    with contextlib.suppress(YamlIllisible):
        lire_yaml(fichier)
