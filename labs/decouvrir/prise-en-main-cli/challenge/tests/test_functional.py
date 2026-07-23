"""Tests pytest pour le challenge prise-en-main-cli (ansible-vault).

Lab local — pas de testinfra, juste l'exécution locale du solution.sh.
"""

import os
import subprocess
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
SOLUTION = CHALLENGE_DIR / "solution.sh"
SECRET = CHALLENGE_DIR / "vault-secret.yml"
VAULT_PASS = CHALLENGE_DIR / ".vault-pass"


def test_solution_script_exists():
    assert SOLUTION.exists(), (
        f"Le script {SOLUTION} doit exister. Suivre challenge/README.md."
    )


def test_solution_script_executable():
    assert os.access(SOLUTION, os.X_OK), (
        f"{SOLUTION} doit être exécutable."
    )


def test_solution_script_uses_ansible_vault_encrypt():
    """Le script invoque `ansible-vault encrypt` (pas un autre tool)."""
    content = SOLUTION.read_text()
    assert "ansible-vault encrypt" in content, (
        "Le script doit utiliser `ansible-vault encrypt` pour chiffrer."
    )


def test_solution_script_uses_vault_password_file():
    """Le script utilise --vault-password-file (pas un mot de passe en dur)."""
    content = SOLUTION.read_text()
    assert "--vault-password-file" in content, (
        "Le script doit utiliser `--vault-password-file` pour passer le password."
    )


def test_solution_script_returns_zero():
    """solution.sh doit retourner exit 0."""
    # Cleanup avant
    SECRET.unlink(missing_ok=True)
    result = subprocess.run(
        [str(SOLUTION)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"solution.sh a échoué (exit {result.returncode}).\n"
        f"stdout : {result.stdout}\nstderr : {result.stderr}"
    )


def test_secret_file_is_vault_encrypted():
    """vault-secret.yml doit être chiffré (header ANSIBLE_VAULT)."""
    assert SECRET.exists(), f"{SECRET} doit avoir été créé par solution.sh"
    first_line = SECRET.read_text().splitlines()[0]
    assert first_line.startswith("$ANSIBLE_VAULT;1.1;AES256"), (
        f"{SECRET} n'est pas chiffré par ansible-vault. "
        f"Première ligne : {first_line!r}"
    )
