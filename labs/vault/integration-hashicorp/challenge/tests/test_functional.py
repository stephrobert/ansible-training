"""Tests du challenge intégration HashiCorp Vault / OpenBao.

Ces tests exigent le Vault dev local (./setup-vault.sh) : ils lisent les
secrets directement via l'API HTTP et vérifient que la preuve déposée par
le playbook de l'apprenant y correspond, sans jamais exposer les valeurs.
Sans serveur joignable, tout le module est skippé avec la marche à suivre :
rien ne passe à vide.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from conftest import assert_idempotent, lab_solution_text

LAB_ROOT = Path(__file__).resolve().parents[2]
SOLUTION = LAB_ROOT / "challenge" / "solution.yml"
PROOF = Path("/tmp/lab82-vault-lookup.txt")

VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "lab82-root")


def _vault_reachable() -> bool:
    try:
        urllib.request.urlopen(f"{VAULT_ADDR}/v1/sys/health", timeout=3)
        return True
    except urllib.error.HTTPError:
        return True  # le serveur répond, même avec un statut non-200
    except OSError:
        return False


if not _vault_reachable():
    pytest.skip(
        f"Serveur Vault injoignable sur {VAULT_ADDR} : lancez "
        "labs/vault/integration-hashicorp/setup-vault.sh (podman requis) "
        "puis relancez pytest.",
        allow_module_level=True,
    )

# L'état observé doit venir de CE run : on efface la preuve avant que le
# conftest ne rejoue solution.yml.
try:
    PROOF.unlink(missing_ok=True)
except PermissionError:
    pytest.fail(
        f"{PROOF} appartient à root : un run précédent a tourné avec become. "
        "Le play doit déclarer become: false (ansible.cfg l'active "
        f"globalement). Supprimez le fichier : sudo rm {PROOF}",
        pytrace=False,
    )


def _fetch_secrets() -> dict:
    """Lit secret/lab82 directement dans Vault (référence indépendante)."""
    req = urllib.request.Request(
        f"{VAULT_ADDR}/v1/secret/data/lab82",
        headers={"X-Vault-Token": VAULT_TOKEN},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise AssertionError(
            f"Impossible de lire secret/lab82 dans Vault (HTTP {exc.code}) : "
            "relancez ./setup-vault.sh pour reposer les secrets de démo."
        ) from exc
    return payload["data"]["data"]


def test_preuve_deposee_et_protegee():
    """Le playbook a déposé la preuve, en 0600."""
    assert PROOF.exists(), (
        f"{PROOF} absent : le playbook n'a pas déposé la preuve de lookup."
    )
    assert PROOF.stat().st_uid == os.getuid(), (
        f"{PROOF} n'appartient pas à l'utilisateur courant : le play a "
        "tourné avec become alors qu'il doit déclarer become: false."
    )
    assert (PROOF.stat().st_mode & 0o777) == 0o600, (
        f"{PROOF} doit être en 0600 : un fichier dérivé d'un secret ne se "
        "pose jamais en lecture pour tous."
    )


def test_longueurs_correspondent_aux_secrets_de_vault():
    """La preuve correspond aux secrets réellement stockés dans Vault.

    Le test lit les valeurs via l'API et compare les longueurs : si la
    lookup n'a pas eu lieu (valeurs inventées, fichier écrit à la main),
    la correspondance casse dès que le secret change côté serveur.
    """
    secrets = _fetch_secrets()
    content = PROOF.read_text()
    assert f"db_password length: {len(secrets['db_password'])}" in content, (
        "La ligne 'db_password length: <n>' ne correspond pas à la longueur "
        "réelle du secret stocké dans Vault."
    )
    assert f"api_key length: {len(secrets['api_key'])}" in content, (
        "La ligne 'api_key length: <n>' ne correspond pas à la longueur "
        "réelle du secret stocké dans Vault."
    )


def test_aucun_secret_en_clair():
    """Ni la preuve ni le playbook ne contiennent les valeurs des secrets."""
    secrets = _fetch_secrets()
    proof_content = PROOF.read_text()
    # La solution RÉELLEMENT en jeu : celle de l'apprenant si elle existe,
    # la référence sinon. Coder challenge/solution.yml en dur rendait ce
    # test infaisable en mode formateur, où ce fichier n'existe pas.
    solution_content = lab_solution_text(__file__)
    for name, value in secrets.items():
        assert value not in proof_content, (
            f"La valeur du secret '{name}' apparaît en clair dans {PROOF} : "
            "la preuve ne doit contenir que des longueurs."
        )
        assert value not in solution_content, (
            f"La valeur du secret '{name}' est écrite en dur dans "
            "solution.yml : tout l'intérêt de la lookup est de ne jamais "
            "poser le secret dans le YAML."
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
