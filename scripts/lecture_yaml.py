"""Lecture tolérante des YAML du catalogue.

Pourquoi ce module existe
-------------------------
Les vérificateurs de catalogue tournent **en CI, sur le contenu d'une pull
request**. Le `lab.yaml` qu'ils lisent est donc écrit par quelqu'un d'autre, et
il peut être malformé — ce n'est pas une hypothèse : un simple guillemet non
fermé faisait remonter une `yaml.scanner.ScannerError` jusqu'au terminal.

Mesuré le 2026-09-15 sur un lab témoin :

    check-labs-completude.py    TRACE PYTHON : yaml.scanner.ScannerError
    gen_catalog.py              TRACE PYTHON : yaml.scanner.ScannerError

Un contributeur recevait une trace Python au lieu du nom de son fichier. Le
défaut est le même que celui que la CLI dsoxlab a corrigé dans son propre
scanner, et son harnais de fuzz énonce le contrat mieux que nous :

    « A malformed lab is meant to be *skipped*, never to take the CLI down. »

Le contrat, ici
---------------
Un YAML illisible **ne fait pas tomber le vérificateur**. Il produit un défaut
nommé, qui dit quel fichier et pourquoi, et le lab est traité comme non
livrable. Un vérificateur qui tombe ne mesure plus rien : il n'annonce pas que
CE lab est mauvais, il annonce que la CI est cassée.

Ce module est le SEUL endroit où `yaml.safe_load` est appelé sur un fichier de
lab. Rustiner chaque appel aurait garanti d'en oublier un.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class YamlIllisible(Exception):
    """Un fichier YAML du catalogue n'a pas pu être lu.

    Porte un message déjà présentable à un contributeur : le nom du fichier et
    la raison, sans trace d'appels.
    """


def lire_yaml(fichier: Path) -> dict[str, Any]:
    """Lit un YAML de catalogue, ou lève YamlIllisible avec un message utile.

    Rend toujours un dictionnaire. Un fichier vide donne `{}` ; un fichier dont
    la racine n'est pas une table est une erreur, parce que tout le reste du
    code ferait ensuite `.get()` sur une liste ou une chaîne.
    """
    try:
        texte = fichier.read_text(encoding="utf-8")
    except OSError as exc:
        raise YamlIllisible(f"{fichier.name} : illisible ({exc.strerror})") from exc
    except UnicodeDecodeError as exc:
        raise YamlIllisible(
            f"{fichier.name} : n'est pas de l'UTF-8 (octet {exc.start})"
        ) from exc

    try:
        donnees = yaml.safe_load(texte)
    except yaml.YAMLError as exc:
        # `problem` et `problem_mark` viennent des erreurs de scanner et de
        # parser ; les autres YAMLError n'en ont pas, d'où le repli.
        detail = getattr(exc, "problem", None) or "YAML invalide"
        marque = getattr(exc, "problem_mark", None)
        ou = f", ligne {marque.line + 1}" if marque is not None else ""
        raise YamlIllisible(f"{fichier.name} : {detail}{ou}") from exc
    except RecursionError as exc:
        # Des alias YAML profondément imbriqués épuisent la pile avant même
        # que PyYAML ne s'en plaigne. C'est une entrée hostile, pas un bug
        # d'ici : elle se refuse, elle ne se corrige pas.
        raise YamlIllisible(f"{fichier.name} : structure trop imbriquée") from exc

    if donnees is None:
        return {}
    if not isinstance(donnees, dict):
        raise YamlIllisible(
            f"{fichier.name} : la racine est un(e) {type(donnees).__name__}, "
            "une table clé/valeur était attendue"
        )
    return donnees
