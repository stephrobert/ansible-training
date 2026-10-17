"""Lire `dsoxlab check --json`, et en tirer un verdict qui ne mente pas.

CE FICHIER EST IDENTIQUE DANS LES DOUZE CATALOGUES. Ne le modifier que pour le
répercuter partout : c'est la divergence de douze copies de `valider-labs.py`
qui a rendu ce module nécessaire, et une treizième variante annulerait le
bénéfice. `tests/test_verdict_check_partage.py` tient la règle là où il existe.

POURQUOI IL EXISTE

`valider-labs.py` lisait le score dans l'encadré que `dsoxlab check` affiche :

    SCORE = re.compile(r"Score\\s*:\\s*(\\d+)\\s*/\\s*100")

Cet encadré est de l'INTERFACE. Il a changé en 0.4.0, et la regex a cessé de
trouver quoi que ce soit : 281 labs se sont retrouvés sans verdict lisible,
d'un catalogue à l'autre, sans qu'aucun contrôle le dise. La sortie `--json`
est au contraire un CONTRAT, elle porte un `schema`, et c'est elle qu'il faut
lire.

TROIS ISSUES, PAS DEUX

Le piège que la 0.4.1 de dsoxlab a corrigé vaut aussi pour qui le lit. Une
suite entièrement skippée rend :

    "ok": true, "passed": 0, "total": 5, "score": 0

`ok` est VRAI, parce qu'il dit « aucun test n'a échoué », ce qui est exact de
cinq tests qui n'ont pas tourné ; et `score` vaut 0. Un lecteur qui s'arrête à
l'un ou à l'autre conclut donc au succès ou à l'échec, là où rien n'a été
mesuré. C'est `status` qui tranche :

    passed        les tests ont tourné, aucun n'a échoué
    failed        les tests ont tourné, au moins un a échoué
    not_measured  rien n'a tourné : suite entièrement skippée, ou rien collecté

et `recorded` dit si la note vaut quelque chose. Un lab `not_measured` n'est ni
VALIDE ni ROUGE : il est SKIP, et il reste à mesurer. Le peindre en rouge
accuserait le lab de ce qui manque au POSTE (un service arrêté, une VM
injoignable, un outil absent) ; le peindre en vert serait pire.
"""

from __future__ import annotations

import re

# Les noms des tests en échec, tels que pytest les liste. La sortie est repliée
# sur la largeur de la console, ce qui coupe les noms longs : on recolle.
_ECHEC = re.compile(r"^FAILED\s+\S+::(\S+)", re.MULTILINE)

# Les trois verdicts, et leur sens.
VALIDE = "VALIDE"      # le cycle complet a prouvé le lab
ROUGE = "ROUGE"        # le cycle a mesuré quelque chose de faux
SKIP = "SKIP"          # le cycle n'a rien pu mesurer : le poste, pas le lab

# Les codes de sortie, calqués sur ceux de `dsoxlab doctor --strict`, où `9`
# (un contrôle requis a échoué) et `10` (il n'a pas pu être mesuré) sont
# distincts à dessein : le premier se répare, le second se remesure.
RC_TOUT_VALIDE = 0
RC_UN_ROUGE = 1
RC_UN_SKIP = 10


class JsonIllisible(RuntimeError):
    """`dsoxlab check --json` n'a pas rendu le document attendu."""


def tests_en_echec(sortie: str) -> list[str]:
    """Les noms des tests en échec, lus dans la sortie brute de pytest.

    Le repli de la console coupe les noms longs en plein milieu : on recolle
    les lignes de continuation avant de lire, puis, si rien ne sort, on retente
    sans aucun retour à la ligne, au prix de la lisibilité.
    """
    recollee = re.sub(r"\n(?=[A-Za-z_])", "", sortie) if "\nFAILED" not in sortie else sortie
    noms = _ECHEC.findall(recollee)
    if not noms:
        noms = _ECHEC.findall("FAILED " + sortie.replace("\n", ""))
    return sorted(set(noms))


def lire(stdout: str) -> dict:
    """Le document de `dsoxlab check --json`, réduit à ce qui décide.

    `status` est lu sans défaut tolérant : une sortie qui n'en porte pas vient
    d'un dsoxlab antérieur à la 0.4.1, et le silence ferait reprendre
    exactement le défaut qu'on corrige. On le dit, et on s'arrête.
    """
    import json

    try:
        d = json.loads(stdout)["check"]
    except (json.JSONDecodeError, KeyError, TypeError) as erreur:
        raise JsonIllisible(
            f"`dsoxlab check --json` n'a pas rendu de JSON lisible : {erreur}"
        ) from erreur

    if "status" not in d:
        raise JsonIllisible(
            "le document ne porte pas `status` : ce dsoxlab est antérieur à la "
            "0.4.1, où une suite entièrement skippée annonçait encore le "
            "succès. Mets l'outil à jour (`uv tool upgrade dsoxlab`) : sans "
            "`status`, aucun verdict d'ici ne vaut rien."
        )

    return {
        "status": d["status"],
        "passed": d.get("passed", 0),
        "total": d.get("total", 0),
        "skipped": d.get("skipped", 0),
        # La note n'est lue que si le moteur l'a inscrite : un `score` de 0 sur
        # une exécution non mesurée n'est pas une note, c'est une absence.
        "score": d.get("score", 0) if d.get("recorded") else None,
        "recorded": bool(d.get("recorded")),
        "echecs": tests_en_echec(d.get("output", "")),
    }


def a_mesure(c: dict) -> bool:
    """Ce `check` a-t-il mesuré quelque chose ?"""
    return c["status"] != "not_measured"


def pourquoi_rien_mesure(c: dict) -> str:
    """La phrase à donner quand rien n'a été mesuré, selon la cause lisible."""
    if c["total"] == 0:
        return (
            "aucun test n'a été collecté : le `conftest.py` lève, ou le lab n'a "
            "pas de test"
        )
    return (
        f"les {c['total']} tests collectés ont tous skippé : le lab n'est pas "
        "prêt sur ce poste (répertoire de travail non préparé, service arrêté, "
        "machine injoignable)"
    )


def code_de_sortie(verdicts: dict) -> int:
    """Le code de sortie d'une campagne, les trois issues distinguées.

    Un ROUGE l'emporte sur un SKIP, comme `9` l'emporte sur `10` dans
    `doctor --strict` : une certitude est plus forte qu'une ignorance.
    """
    rendus = [v.get("verdict") for v in verdicts.values()]
    if ROUGE in rendus:
        return RC_UN_ROUGE
    if SKIP in rendus:
        return RC_UN_SKIP
    return RC_TOUT_VALIDE
