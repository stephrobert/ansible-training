"""Tests lab 78 : encrypt_string.

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


def test_result_file_exists(host):
    f = host.file("/tmp/lab78-challenge.txt")
    assert f.exists, message(
        en=f"/tmp/lab78-challenge.txt is missing. {MDP_EN}",
        fr=f"/tmp/lab78-challenge.txt est absent. {MDP_FR}",
    )


def test_admin_username_clair(host):
    """admin_username (en clair dans group_vars/all.yml) est bien lu."""
    content = host.file("/tmp/lab78-challenge.txt").content_string
    assert "lab78_admin" in content, message(
        en="admin_username, which is in the CLEAR in group_vars/all.yml, is "
           "missing: the file was not loaded at all. Encrypted and clear "
           "variables live side by side, and both are read the same way.",
        fr="admin_username, qui est en CLAIR dans group_vars/all.yml, "
           "manque : le fichier n'a pas été chargé du tout. Variables "
           "chiffrées et en clair cohabitent, et se lisent pareil.",
    )


def test_admin_password_decrypted(host):
    """admin_password (chiffré inline) commence bien par AdminS."""
    content = host.file("/tmp/lab78-challenge.txt").content_string
    assert "starts: Admin" in content, message(
        en="The start of admin_password does not appear. This variable is "
           "encrypted INLINE, with encrypt_string, and not in a separate "
           "file: it decrypts with the same password.",
        fr="Le début d'admin_password n'apparaît pas. Cette variable est "
           "chiffrée EN LIGNE, avec encrypt_string, et non dans un fichier "
           "séparé : elle se déchiffre avec le même mot de passe.",
    )


def test_password_length(host):
    """Longueur du password révélée dans le contenu (preuve déchiffrement)."""
    content = host.file("/tmp/lab78-challenge.txt").content_string
    assert "length:" in content, message(
        en="The password's length is not rendered. It is what proves the "
           "decryption really happened: an encrypted string has a different "
           "length from the secret it hides.",
        fr="La longueur du mot de passe n'est pas rendue. C'est elle qui "
           "prouve que le déchiffrement a bien eu lieu : une chaîne chiffrée "
           "n'a pas la longueur du secret qu'elle cache.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
