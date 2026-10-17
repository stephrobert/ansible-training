"""Tests pytest+testinfra pour le challenge failed-when-changed-when.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/failed-when-result.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    """Le fichier existe = la 1ère tâche n'a pas planté (failed_when override)."""
    f = host.file(RESULT_FILE)
    assert f.exists, message(
        en=f"{RESULT_FILE} does not exist. The first task was marked failed, "
           f"and the play stopped there: with failed_when, an rc=1 can be "
           f"declared acceptable.",
        fr=f"{RESULT_FILE} n'existe pas. La première tâche a été marquée "
           f"failed, et le play s'est arrêté là : avec failed_when, un rc=1 "
           f"peut être déclaré acceptable.",
    )


def test_rc_captured(host):
    content = host.file(RESULT_FILE).content_string
    assert "rc=1" in content, message(
        en="The file does not carry rc=1. Register the result and render its "
           "rc: that is the proof the command really did fail, and that "
           "failed_when caught it rather than hid it.",
        fr="Le fichier ne porte pas rc=1. Enregistre le résultat et rends son "
           "rc : c'est la preuve que la commande a bien échoué, et que "
           "failed_when l'a rattrapée plutôt que masquée.",
    )


def test_changed_state(host):
    content = host.file(RESULT_FILE).content_string
    assert "ok=changed" in content, message(
        en="The file does not carry ok=changed. failed_when and changed_when "
           "are two independent decisions: the first says whether the task "
           "failed, the second whether it changed anything.",
        fr="Le fichier ne porte pas ok=changed. failed_when et changed_when "
           "sont deux décisions indépendantes : la première dit si la tâche a "
           "échoué, la seconde si elle a changé quelque chose.",
    )

# Pas de test d'idempotence ici, volontairement.
# Ce lab exige une commande qui retourne rc=1 et qui soit marquée `changed`
# (`changed_when: result.rc == 1`) : elle l'est donc à CHAQUE passage, par
# construction. C'est le sujet du lab, pas un défaut. Exiger changed=0 ici
# contredirait ce qu'il enseigne.
