"""Tests pytest+testinfra pour le challenge premiers pas ansible-vault (04b).

Valide que le challenge a bien :
- chiffré le fichier de secrets (présence du header $ANSIBLE_VAULT)
- protégé le mot de passe vault (mode 0600)
- déposé /tmp/db1-app.conf sur db1.lab avec les 3 secrets attendus.
"""

import os
import stat
from pathlib import Path

import pytest

from conftest import lab_host, assert_idempotent, lab_artifact

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/db1-app.conf"

LAB_ROOT = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = LAB_ROOT / "challenge"
VAULT_PASSWORD_FILE = CHALLENGE_DIR / ".vault_password"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_vault_password_file_exists():
    assert VAULT_PASSWORD_FILE.exists(), (
        f"{VAULT_PASSWORD_FILE} absent — créez-le avec "
        f"`echo 'mon-mdp' > {VAULT_PASSWORD_FILE} && chmod 0600`."
    )


def test_vault_password_file_mode_0600():
    """Le fichier de mot de passe vault doit avoir mode 0600 (sécurité)."""
    mode = stat.S_IMODE(os.stat(VAULT_PASSWORD_FILE).st_mode)
    assert mode == 0o600, (
        f"{VAULT_PASSWORD_FILE} doit avoir mode 0600, vu : {oct(mode)}. "
        f"Lancer : chmod 0600 {VAULT_PASSWORD_FILE}"
    )


def test_secrets_file_is_encrypted():
    """Le fichier de secrets réellement en jeu doit être chiffré.

    On vérifie l'artefact que le playbook a CONSOMMÉ : celui de l'apprenant
    s'il existe, la référence du formateur sinon. Coder challenge/files/ en dur
    rendait ce test infaisable en mode formateur, où l'apprenant n'existe pas.
    """
    secrets = lab_artifact(__file__, "files/app_secrets.yml")
    head = secrets.read_text().splitlines()[0] if secrets.read_text() else ""
    assert head.startswith("$ANSIBLE_VAULT"), (
        f"{secrets} n'est pas chiffré. Lancer : "
        f"ansible-vault encrypt {secrets} --vault-password-file=…"
    )


def test_db1_app_conf_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné ?"
    )


def test_db1_app_conf_mode_0600(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o600, (
        f"{RESULT_FILE} doit avoir mode 0600 (secrets), vu : {oct(f.mode)}"
    )


def test_db1_app_conf_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root", (
        f"{RESULT_FILE} doit appartenir à root, vu : {f.user}"
    )


def test_db1_app_conf_contains_three_secrets(host):
    """Le fichier doit contenir les 3 variables après déchiffrement."""
    content = host.file(RESULT_FILE).content_string
    for marker in ("db_password=", "jwt_secret=", "redis_token="):
        assert marker in content, (
            f"Marqueur '{marker}' absent de {RESULT_FILE}. "
            f"Reçu : {content[:200]}"
        )


def test_db1_app_conf_secrets_not_empty(host):
    """Les valeurs ne doivent pas être vides après déchiffrement."""
    content = host.file(RESULT_FILE).content_string
    for line in content.splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            assert value.strip(), (
                f"La valeur de '{key}' est vide dans {RESULT_FILE}. "
                f"Le déchiffrement a-t-il bien fonctionné ?"
            )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
