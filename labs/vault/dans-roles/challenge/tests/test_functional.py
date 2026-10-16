"""Tests lab 81 : vault dans un rôle.

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


@pytest.fixture(scope="module")
def host():
    return lab_host("db1.lab")


def test_file_exists(host):
    f = host.file("/tmp/lab81-secured-app.txt")
    assert f.exists, message(
        en=f"/tmp/lab81-secured-app.txt is missing. {MDP_EN}",
        fr=f"/tmp/lab81-secured-app.txt est absent. {MDP_FR}",
    )


def test_default_user(host):
    """secured_app_user (default clair)."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "user: appuser" in content, message(
        en="user: appuser is missing. It is the role's default, in "
           "defaults/main.yml, and nothing overrides it here.",
        fr="user: appuser manque. C'est le défaut du rôle, dans "
           "defaults/main.yml, et rien ne le surcharge ici.",
    )


def test_override_port(host):
    """secured_app_port override par le play (9999)."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "port: 9999" in content, message(
        en="port: 9999 is missing: the play's override did not reach the "
           "role. A defaults/main.yml value has the lowest priority, so it is "
           "overridden by the role param, not the other way round.",
        fr="port: 9999 manque : la surcharge du play n'a pas atteint le rôle. "
           "Une valeur de defaults/main.yml a la priorité la plus basse, elle "
           "est donc surchargée par le role param, et non l'inverse.",
    )


def test_db_password_decrypted(host):
    """vault_secured_app_db_password déchiffré et exposé via secured_app_db_password."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "RoleDBPas" in content, message(
        en="The role's database password is not decrypted. The convention is "
           "a vault_ prefixed variable in the encrypted file, referenced by a "
           "clear one in defaults: that is what keeps the role readable.",
        fr="Le mot de passe de base du rôle n'est pas déchiffré. La "
           "convention est une variable préfixée vault_ dans le fichier "
           "chiffré, référencée par une variable claire dans defaults : c'est "
           "ce qui garde le rôle lisible.",
    )


def test_api_token_decrypted(host):
    """vault_secured_app_api_token déchiffré."""
    content = host.file("/tmp/lab81-secured-app.txt").content_string
    assert "role_api_tok_lab81_xyz" in content, message(
        en="The role's API token is not decrypted.",
        fr="Le jeton d'API du rôle n'est pas déchiffré.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
