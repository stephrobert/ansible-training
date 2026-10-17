"""Tests lab 77 : introduction à Vault.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

#: Le geste manquant est presque toujours le même sur les labs vault : le mot
#: de passe n'a pas été fourni, donc rien n'a pu être déchiffré.
MDP_EN = (
    "Without the vault password, the play cannot read the encrypted "
    "variables: pass --vault-password-file, or --ask-vault-pass."
)
MDP_FR = (
    "Sans le mot de passe du vault, le play ne peut pas lire les variables "
    "chiffrées : passe --vault-password-file, ou --ask-vault-pass."
)

TARGET = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET)


def test_result_file_exists(host):
    """Le fichier prouve que les 2 fichiers chiffrés ont été déchiffrés."""
    f = host.file("/tmp/lab77-challenge-result.txt")
    assert f.exists, message(
        en=f"/tmp/lab77-challenge-result.txt is missing. {MDP_EN}",
        fr=f"/tmp/lab77-challenge-result.txt est absent. {MDP_FR}",
    )


def test_db_secrets_decrypted(host):
    """db_user du fichier chiffré db_secrets.yml apparaît dans le fichier final."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "db_user: app_admin" in content, message(
        en="db_user, which lives in the encrypted db_secrets.yml, is not in "
           "the result: this first file was not loaded, or not decrypted.",
        fr="db_user, qui vit dans db_secrets.yml chiffré, n'est pas dans le "
           "résultat : ce premier fichier n'a pas été chargé, ou pas "
           "déchiffré.",
    )


def test_api_secrets_decrypted(host):
    """api_endpoint du fichier chiffré api_secrets.yml apparaît dans le fichier final."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "api_endpoint: https://api.example.com/v1" in content, message(
        en="api_endpoint, from the encrypted api_secrets.yml, is missing. The "
           "challenge loads TWO encrypted files: the second is forgotten.",
        fr="api_endpoint, de api_secrets.yml chiffré, manque. Le challenge "
           "charge DEUX fichiers chiffrés : le second est oublié.",
    )


def test_db_password_partial(host):
    """db_password (chiffré) commence bien par 'Challenge'."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "ChallengeDB2026" in content[:200] or "Challenge" in content, message(
        en="db_password does not appear in the result: the variable was read "
           "but never rendered.",
        fr="db_password n'apparaît pas dans le résultat : la variable a été "
           "lue mais jamais rendue.",
    )


def test_api_key_present(host):
    """api_key (chiffré) est bien présent dans la sortie."""
    content = host.file("/tmp/lab77-challenge-result.txt").content_string
    assert "challenge_api_xyz789" in content, message(
        en="api_key does not appear in the result.",
        fr="api_key n'apparaît pas dans le résultat.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
