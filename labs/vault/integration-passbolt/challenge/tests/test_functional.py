"""Tests du challenge intégration Passbolt.

Passbolt authentifie des humains par clé OpenPGP : l'inscription admin,
la clé et la ressource `lab83-demo` se créent via l'interface web. Ces
tests ne font donc pas semblant : si le serveur ne répond pas, si la clé
n'est pas exportée ou si la passphrase manque, le module entier est
skippé avec la marche à suivre. Quand tout est là, le conftest rejoue le
playbook de l'apprenant et on vérifie l'état produit, pas le YAML.
"""

import os
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from conftest import assert_idempotent, lab_solution_text

LAB_ROOT = Path(__file__).resolve().parents[2]
SOLUTION = LAB_ROOT / "challenge" / "solution.yml"
PRIVATE_KEY = LAB_ROOT / ".passbolt-private.asc"
PROOF = Path("/tmp/lab83-passbolt-lookup.txt")

PASSBOLT_URL = os.environ.get("PASSBOLT_URL", "https://localhost:8443")


def _passbolt_reachable() -> bool:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        urllib.request.urlopen(
            f"{PASSBOLT_URL}/healthcheck/status.json", timeout=3, context=ctx
        )
        return True
    except urllib.error.HTTPError:
        return True  # le serveur répond, même avec un statut non-200
    except OSError:
        return False


if not _passbolt_reachable():
    pytest.skip(
        f"Serveur Passbolt injoignable sur {PASSBOLT_URL} : lancez "
        "labs/vault/integration-passbolt/setup-passbolt.sh (podman requis) "
        "et terminez l'inscription via l'interface web, puis relancez pytest.",
        allow_module_level=True,
    )

if not PRIVATE_KEY.exists():
    pytest.skip(
        f"Clé OpenPGP absente ({PRIVATE_KEY}) : exportez la clé privée du "
        "compte Passbolt (cf. challenge/README.md, pré-requis manuels).",
        allow_module_level=True,
    )

if not os.environ.get("PASSBOLT_PASSPHRASE"):
    pytest.skip(
        "Variable PASSBOLT_PASSPHRASE absente de l'environnement : "
        "export PASSBOLT_PASSPHRASE='...' puis relancez pytest.",
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


def test_preuve_deposee_et_protegee():
    """Le playbook a récupéré le secret et déposé la preuve en 0600."""
    assert PROOF.exists(), (
        f"{PROOF} absent : la lookup Passbolt n'a pas abouti ou la preuve "
        "n'a pas été déposée."
    )
    assert PROOF.stat().st_uid == os.getuid(), (
        f"{PROOF} n'appartient pas à l'utilisateur courant : le play a "
        "tourné avec become alors qu'il doit déclarer become: false."
    )
    assert (PROOF.stat().st_mode & 0o777) == 0o600, (
        f"{PROOF} doit être en 0600 : un fichier dérivé d'un secret ne se "
        "pose jamais en lecture pour tous."
    )


def test_preuve_contient_une_longueur_plausible():
    """La preuve annonce une longueur de secret non nulle."""
    content = PROOF.read_text()
    match = re.search(r"Secret length: (\d+)", content)
    assert match, (
        f"Contenu inattendu dans {PROOF} : attendu 'Secret length: <n>', "
        f"trouvé : {content!r}"
    )
    assert int(match.group(1)) >= 1, (
        "Longueur nulle : la lookup a retourné un secret vide. Vérifiez que "
        "la ressource lab83-demo existe dans Passbolt avec un mot de passe."
    )


def test_aucun_secret_en_dur_dans_le_yaml():
    """Ni passphrase ni bloc de clé privée écrits en dur dans solution.yml."""
    content = lab_solution_text(__file__)
    assert "BEGIN PGP PRIVATE KEY BLOCK" not in content, (
        "La clé privée OpenPGP est collée dans solution.yml : elle doit être "
        "lue depuis .passbolt-private.asc via lookup('file', ...)."
    )
    passphrase = os.environ["PASSBOLT_PASSPHRASE"]
    assert passphrase not in content, (
        "La passphrase est écrite en dur dans solution.yml : elle doit venir "
        "de l'environnement (lookup env PASSBOLT_PASSPHRASE)."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
