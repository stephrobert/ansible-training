"""Tests du challenge intégration HashiCorp Vault / OpenBao.

Le serveur Vault est déclaré dans `runtime.services` du lab.yaml : `dsoxlab run`
et `dsoxlab check` le montent, l'initialisent (secret/lab82) et l'arrêtent à
`dsoxlab clean`. Plus de script à lancer à la main, donc plus de lab qui se
skippe chez qui a oublié de le faire.

Les tests lisent les secrets directement via l'API HTTP et vérifient que la
preuve déposée par le playbook y correspond, sans jamais exposer les valeurs.
Si le serveur n'est pas celui du lab, le module est skippé avec la raison
exacte : rien ne passe à vide, et rien n'accuse le lab pour un serveur voisin.
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

# 8201, pas 8200 : le lab publie son Vault sur un port qui lui est propre
# (runtime.services du lab.yaml), pour ne pas dialoguer avec celui d'une
# autre formation qui occuperait le port par défaut.
VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8201")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "lab82-root")


def _vault_du_lab() -> str | None:
    """Le serveur qui répond est-il CELUI DU LAB ? Sinon, dit pourquoi non.

    Vérifier qu'un port répond ne prouve rien : 8200 est le port par défaut de
    Vault, et n'importe quel autre Vault du poste l'occupe aussi bien. Vécu le
    2026-07-28 : le conteneur `dsoxlab-terraform-training-vault` d'une autre
    formation écoutait là, ce module a donc cessé de se skipper, et ses quatre
    tests ont échoué sur « Forbidden: Permission Denied to path ['lab82'] ».
    Un test qui se croit chez lui parce qu'un port répond accuse le lab pour une
    cause qui lui est étrangère.

    On exige donc les deux marques du serveur du lab : notre token est accepté,
    et secret/lab82 y existe.
    """
    sante = f"{VAULT_ADDR}/v1/sys/health"
    try:
        urllib.request.urlopen(sante, timeout=3)
    except urllib.error.HTTPError:
        pass  # le serveur répond, même avec un statut non-200 (scellé, standby…)
    except OSError:
        return f"aucun serveur Vault ne répond sur {VAULT_ADDR}"

    requete = urllib.request.Request(
        f"{VAULT_ADDR}/v1/secret/data/lab82",
        headers={"X-Vault-Token": VAULT_TOKEN},
    )
    try:
        urllib.request.urlopen(requete, timeout=3)
    except urllib.error.HTTPError as err:
        if err.code in (403, 401):
            return (
                f"un Vault répond sur {VAULT_ADDR} mais refuse le token du lab "
                "(HTTP {code}) : ce n'est pas le nôtre, c'est un autre serveur "
                "qui occupe le port".format(code=err.code)
            )
        if err.code == 404:
            return (
                f"le Vault de {VAULT_ADDR} ne contient pas secret/lab82 : "
                "serveur d'une autre formation, ou secrets non initialisés"
            )
        return f"le Vault de {VAULT_ADDR} a répondu HTTP {err.code} sur secret/lab82"
    except OSError as err:
        return f"lecture de secret/lab82 impossible sur {VAULT_ADDR} : {err}"
    return None


@pytest.fixture(scope="module", autouse=True)
def _exige_le_vault_du_lab(_apply_lab_state):
    """Skippe le module si le Vault en face n'est pas celui du lab.

    Fixture, et non `pytest.skip(allow_module_level=True)` : un skip de module
    s'évalue à l'IMPORT, donc avant toute fixture — donc avant que le conftest
    n'ait monté le service déclaré dans `runtime.services`. Le lab se serait
    skippé alors même que dsoxlab s'apprêtait à lui fournir son serveur.

    Dépendre de `_apply_lab_state` fixe l'ordre : services montés et solution
    rejouée d'abord, vérification ensuite.
    """
    probleme = _vault_du_lab()
    if probleme:
        pytest.skip(
            f"{probleme}.\n"
            "Montez le Vault du lab : `dsoxlab run vault-integration-hashicorp` "
            "(Docker requis), qui le démarre et y pose secret/lab82. "
            "Si un autre serveur occupe déjà 8201, arrêtez-le ou pointez "
            "VAULT_ADDR ailleurs."
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
            "relancez `dsoxlab run vault-integration-hashicorp`, dont le "
            "post_start repose les secrets de démo."
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
