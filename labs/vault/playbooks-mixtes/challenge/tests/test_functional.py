"""Tests lab 80 : playbook mixte, clair et vault.

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
    return lab_host("web1.lab")


def test_file_exists(host):
    f = host.file("/tmp/lab80-challenge.txt")
    assert f.exists, message(
        en=f"/tmp/lab80-challenge.txt is missing. {MDP_EN}",
        fr=f"/tmp/lab80-challenge.txt est absent. {MDP_FR}",
    )


def test_clair_variables(host):
    """Variables main.yml (clair) bien lues."""
    content = host.file("/tmp/lab80-challenge.txt").content_string
    assert "Env: lab80" in content, message(
        en="« Env: lab80 » is missing. This variable is in the clear, in "
           "group_vars/all/main.yml: if it is absent, the whole group_vars "
           "directory was not read.",
        fr="« Env: lab80 » manque. Cette variable est en clair, dans "
           "group_vars/all/main.yml : si elle est absente, c'est tout le "
           "répertoire group_vars qui n'a pas été lu.",
    )
    assert "Port: 80" in content, message(
        en="« Port: 80 » is missing.",
        fr="« Port: 80 » manque.",
    )


def test_vault_admin_token(host):
    """vault_admin_token (group_vars/all/vault.yml) déchiffré."""
    content = host.file("/tmp/lab80-challenge.txt").content_string
    # 10 premiers chars
    assert "Admin token starts: lab80_admi" in content, message(
        en="The admin token is not decrypted. It is in "
           "group_vars/all/vault.yml: a clear file and an encrypted file "
           "coexist in the same directory, and Ansible loads both.",
        fr="Le jeton d'administration n'est pas déchiffré. Il est dans "
           "group_vars/all/vault.yml : un fichier clair et un fichier chiffré "
           "cohabitent dans le même répertoire, et Ansible charge les deux.",
    )


def test_vault_web_secret(host):
    """vault_web_secret (group_vars/webservers/vault.yml) déchiffré."""
    content = host.file("/tmp/lab80-challenge.txt").content_string
    # 'web_secret_lab80_xyz' = 20 chars
    assert "Web secret length: 20" in content, message(
        en="The web secret's length is not 20. It lives in "
           "group_vars/webservers/vault.yml, which only applies to hosts of "
           "that group: check web1.lab really belongs to webservers.",
        fr="La longueur du secret web ne vaut pas 20. Il vit dans "
           "group_vars/webservers/vault.yml, qui ne s'applique qu'aux hôtes "
           "de ce groupe : vérifie que web1.lab appartient bien à webservers.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
