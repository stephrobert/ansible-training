"""Tests lab 79 : vault-id multiples.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

DEV = "/tmp/lab79-challenge-web1.lab.txt"
PROD = "/tmp/lab79-challenge-db1.lab.txt"

#: Le rappel qui vaut pour tout ce lab : un fichier absent ou un contenu faux
#: viennent presque toujours du même geste manquant, les DEUX `--vault-id`.
LES_DEUX_IDS_EN = (
    "The playbook needs BOTH --vault-id on the same command line, dev@... and "
    "prod@...: with only one, the other environment fails to decrypt."
)
LES_DEUX_IDS_FR = (
    "Le playbook a besoin des DEUX --vault-id sur la même ligne de commande, "
    "dev@... et prod@... : avec un seul, l'autre environnement ne se déchiffre "
    "pas."
)


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


def test_dev_file_on_web1(web1):
    """web1.lab (groupe dev) reçoit son fichier déchiffré."""
    assert web1.file(DEV).exists, message(
        en=f"{DEV} is missing on web1.lab. {LES_DEUX_IDS_EN}",
        fr=f"{DEV} est absent de web1.lab. {LES_DEUX_IDS_FR}",
    )


def test_prod_file_on_db1(db1):
    """db1.lab (groupe prod) reçoit son fichier déchiffré."""
    assert db1.file(PROD).exists, message(
        en=f"{PROD} is missing on db1.lab. {LES_DEUX_IDS_EN}",
        fr=f"{PROD} est absent de db1.lab. {LES_DEUX_IDS_FR}",
    )


def _lines(host, path):
    """Lignes strippées d'un fichier distant.

    On teste ensuite l'appartenance de la LIGNE entière à cette liste, et non une
    sous-chaîne du contenu : le host attendu est prouvé par égalité de ligne, et
    CodeQL ne voit plus une sanitization d'URL incomplète
    (py/incomplete-url-substring-sanitization).
    """
    return [line.strip() for line in host.file(path).content_string.splitlines()]


def test_dev_db_host(web1):
    """web1 voit le db_host de dev (déchiffré avec vault-id dev)."""
    lines = _lines(web1, DEV)
    assert "db_host: dev-db.example.com" in lines, message(
        en="web1.lab does not see dev's db_host. Either the dev variables are "
           "not the ones read on this host, or the group_vars of dev and prod "
           "got crossed: web1.lab belongs to the dev group.",
        fr="web1.lab ne voit pas le db_host de dev. Soit les variables de dev "
           "ne sont pas celles lues sur cet hôte, soit les group_vars de dev "
           "et prod sont croisées : web1.lab appartient au groupe dev.",
    )
    assert "Environnement: dev" in lines, message(
        en="The file on web1.lab does not say « Environnement: dev ». Each "
           "host renders its own environment: the value comes from its group, "
           "it is not written by hand.",
        fr="Le fichier de web1.lab n'annonce pas « Environnement: dev ». "
           "Chaque hôte rend son propre environnement : la valeur vient de son "
           "groupe, elle ne s'écrit pas à la main.",
    )


def test_prod_db_host(db1):
    """db1 voit le db_host de prod (déchiffré avec vault-id prod)."""
    lines = _lines(db1, PROD)
    assert "db_host: prod-db.example.com" in lines, message(
        en="db1.lab does not see prod's db_host. db1.lab belongs to the prod "
           "group, and must decrypt with the prod vault-id.",
        fr="db1.lab ne voit pas le db_host de prod. db1.lab appartient au "
           "groupe prod, et doit déchiffrer avec le vault-id prod.",
    )
    assert "Environnement: prod" in lines, message(
        en="The file on db1.lab does not say « Environnement: prod ».",
        fr="Le fichier de db1.lab n'annonce pas « Environnement: prod ».",
    )


def test_passwords_different_lengths(web1, db1):
    """Les 2 environnements ont des passwords de longueurs différentes (preuve dechiffrement séparé)."""
    dev_content = web1.file(DEV).content_string
    prod_content = db1.file(PROD).content_string
    # dev: "DevDBPass123" (12 chars), prod: "ProdDBPassUltraStrong!2026" (26 chars)
    assert "length: 12" in dev_content, message(
        en="dev's password is not 12 characters long. This test is the proof "
           "that the two vaults were really decrypted SEPARATELY: two "
           "identical lengths would mean the same file was read twice.",
        fr="Le mot de passe de dev ne fait pas 12 caractères. Ce test est la "
           "preuve que les deux vaults ont bien été déchiffrés SÉPARÉMENT : "
           "deux longueurs identiques signifieraient qu'un même fichier a été "
           "lu deux fois.",
    )
    assert "length: 26" in prod_content, message(
        en="prod's password is not 26 characters long: see above, the two "
           "lengths differ on purpose.",
        fr="Le mot de passe de prod ne fait pas 26 caractères : voir "
           "ci-dessus, les deux longueurs diffèrent à dessein.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
