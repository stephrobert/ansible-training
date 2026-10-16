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

from conftest import assert_idempotent, lab_solution_text, message

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
        "`dsoxlab run vault-integration-passbolt` (Docker requis), qui monte "
        "MariaDB puis Passbolt et crée le compte admin, terminez l'inscription "
        "via l'interface web, puis relancez pytest.",
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
        message(
        en=f"{PROOF} belongs to root: an earlier run used become. "
        "The play must declare become: false (ansible.cfg enables it "
        f"globally). Delete the file: sudo rm {PROOF}",
        fr=f"{PROOF} appartient à root : un run précédent a tourné avec become. "
        "Le play doit déclarer become: false (ansible.cfg l'active "
        f"globalement). Supprimez le fichier : sudo rm {PROOF}",
    ),
        pytrace=False,
    )


def test_preuve_deposee_et_protegee():
    """Le playbook a récupéré le secret et déposé la preuve en 0600."""
    assert PROOF.exists(), message(
        en=f"{PROOF} missing: the Passbolt lookup did not succeed, or the proof "
        "was not written.",
        fr=f"{PROOF} absent : la lookup Passbolt n'a pas abouti ou la preuve "
        "n'a pas été déposée.",
    )
    assert PROOF.stat().st_uid == os.getuid(), message(
        en=f"{PROOF} does not belong to the current user: the play ran with "
        "become while it must declare become: false.",
        fr=f"{PROOF} n'appartient pas à l'utilisateur courant : le play a "
        "tourné avec become alors qu'il doit déclarer become: false.",
    )
    assert (PROOF.stat().st_mode & 0o777) == 0o600, message(
        en=f"{PROOF} must be mode 0600: a file derived from a secret is never "
        "left world-readable.",
        fr=f"{PROOF} doit être en 0600 : un fichier dérivé d'un secret ne se "
        "pose jamais en lecture pour tous.",
    )


def test_preuve_contient_une_longueur_plausible():
    """La preuve annonce une longueur de secret non nulle."""
    content = PROOF.read_text()
    match = re.search(r"Secret length: (\d+)", content)
    assert match, message(
        en=f"Unexpected contents in {PROOF}: expected 'Secret length: <n>', "
        f"found: {content!r}",
        fr=f"Contenu inattendu dans {PROOF} : attendu 'Secret length: <n>', "
        f"trouvé : {content!r}",
    )
    assert int(match.group(1)) >= 1, message(
        en="Zero length: the lookup returned an empty secret. Check that the "
        "lab83-demo resource exists in Passbolt, with a password.",
        fr="Longueur nulle : la lookup a retourné un secret vide. Vérifiez que "
        "la ressource lab83-demo existe dans Passbolt avec un mot de passe.",
    )


def test_aucun_secret_en_dur_dans_le_yaml():
    """Ni passphrase ni bloc de clé privée écrits en dur dans solution.yml."""
    content = lab_solution_text(__file__)
    assert "BEGIN PGP PRIVATE KEY BLOCK" not in content, message(
        en="The OpenPGP private key is pasted into solution.yml: it must be read "
        "from .passbolt-private.asc through lookup('file', ...).",
        fr="La clé privée OpenPGP est collée dans solution.yml : elle doit être "
        "lue depuis .passbolt-private.asc via lookup('file', ...).",
    )
    passphrase = os.environ["PASSBOLT_PASSPHRASE"]
    assert passphrase not in content, message(
        en="The passphrase is hardcoded in solution.yml: it must come from the "
        "environment (lookup env PASSBOLT_PASSPHRASE).",
        fr="La passphrase est écrite en dur dans solution.yml : elle doit venir "
        "de l'environnement (lookup env PASSBOLT_PASSPHRASE).",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
