"""Tests pytest+testinfra pour le challenge precedence-variables.

Deux duels sont vérifiés ici, et il faut les deux :

- `winner` : le conftest passe `--extra-vars "winner=extra_vars_wins"`, donc ce
  duel ne prouve QUE le niveau 22. C'est ce que testait la version précédente,
  et c'est pour ça qu'elle n'a jamais attrapé l'erreur du cours : avec
  `--extra-vars` dans la boucle, l'ordre relatif de `vars:` et `vars_files:`
  n'est jamais observé.
- `duel` : personne ne le passe en `--extra-vars`. Il oppose donc directement
  les `vars:` du play (niveau 12) au `vars_files:` (niveau 14), et c'est
  `vars_files` qui doit gagner. C'est le coeur pédagogique du lab, et le
  garde-fou qui empêche le cours de redériver vers l'ordre inverse.
"""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/precedence-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def resultat(host):
    """Le fichier de résultat, parsé en dict {variable: valeur}.

    Parsé plutôt que cherché en sous-chaîne : `assert "duel=vars_files" in
    content` passerait aussi sur une ligne `autre_duel=vars_files`, et surtout
    ne distingue pas une variable absente d'une variable fausse.
    """
    fichier = host.file(RESULT_FILE)
    assert fichier.exists, (
        f"{RESULT_FILE} est absent de {TARGET_HOST}. Votre solution.yml doit le "
        "poser avec les valeurs résolues de `winner` et `duel`."
    )
    valeurs = {}
    for ligne in fichier.content_string.splitlines():
        if "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            valeurs[cle.strip()] = valeur.strip()
    return valeurs


def test_extra_vars_wins(resultat):
    """--extra-vars (niveau 22) écrase tous les autres niveaux."""
    assert resultat.get("winner") == "extra_vars_wins", (
        "--extra-vars (niveau 22) doit gagner sur les `vars:` du play (12) et "
        f"sur le `vars_files:` (14). Reçu : winner={resultat.get('winner')!r}"
    )


def test_vars_files_bat_play_vars(resultat):
    """vars_files: (14) bat les vars: du play (12). LE point du lab.

    Contre-intuitif : on croit spontanément que ce qui est écrit dans le play
    l'emporte sur un fichier chargé à côté. C'est l'inverse, et c'est ce que
    l'EX294 vérifie.
    """
    assert "duel" in resultat, (
        f"La variable `duel` est absente de {RESULT_FILE}. Elle doit être "
        "déclarée À LA FOIS dans les `vars:` du play et dans "
        "`vars/loader.yml`, puis écrite dans le fichier de résultat : c'est "
        "elle qui démontre l'ordre `vars_files:` > `vars:`."
    )
    assert resultat["duel"] == "vars_files", (
        "`vars_files:` (niveau 14) doit gagner sur les `vars:` du play "
        f"(niveau 12). Reçu : duel={resultat['duel']!r}.\n"
        "Si vous avez obtenu 'play_vars', vérifiez que `duel` est bien défini "
        "dans vars/loader.yml ET que ce fichier est chargé par `vars_files:`."
    )


def test_play_vars_does_not_win(resultat):
    """Les `vars:` du play (12) ne gagnent aucun des deux duels."""
    perdants = {c: v for c, v in resultat.items() if v == "play_vars"}
    assert not perdants, (
        "Les `vars:` du play (niveau 12) sont le niveau le plus FAIBLE des "
        "trois en jeu ici : ils perdent contre `vars_files:` (14) comme contre "
        f"`--extra-vars` (22). Or ils gagnent pour : {sorted(perdants)}."
    )


def test_vars_files_ne_bat_pas_extra_vars(resultat):
    """vars_files: (14) gagne sur le play, mais jamais sur --extra-vars (22)."""
    assert resultat.get("winner") != "vars_files", (
        "`vars_files:` ne doit PAS gagner sur `--extra-vars` : le niveau 22 "
        "gagne sur tout, sans exception."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
