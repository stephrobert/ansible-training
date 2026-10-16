"""Tests du lab 68 : lint production + pre-commit.

Le rôle est livré volontairement fautif et les configs en squelette. Le
juge de paix est l'exécution réelle d'ansible-lint --profile production
(code retour 0). Des garde-fous vérifient que l'apprenant a corrigé le
rôle sans le vider de son comportement.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import message

LAB_ROOT = Path(__file__).resolve().parents[2]
TASKS = LAB_ROOT / "roles" / "webserver" / "tasks" / "main.yml"


def test_ansible_lint_config_written():
    config = yaml.safe_load((LAB_ROOT / ".ansible-lint").read_text())
    assert config.get("profile") == "production", message(
        en="The profile must be 'production' in .ansible-lint: it is the "
        "strictest check, the one companies require",
        fr="Le profil doit être 'production' dans .ansible-lint : c'est le "
        "contrôle le plus strict, celui exigé en entreprise",
    )
    assert config.get("exclude_paths"), message(
        en="Declare sensible exclude_paths (.cache/, .git/, molecule/, tests/)",
        fr="Déclarez des exclude_paths raisonnables (.cache/, .git/, "
        "molecule/, tests/)",
    )


def test_yamllint_config_written():
    config = yaml.safe_load((LAB_ROOT / ".yamllint").read_text())
    assert config.get("extends") == "default", message(
        en=".yamllint must extend yamllint's default config",
        fr=".yamllint doit étendre la config default de yamllint",
    )
    truthy = (config.get("rules") or {}).get("truthy") or {}
    allowed = truthy.get("allowed-values", []) if isinstance(truthy, dict) else []
    assert "true" in allowed and "false" in allowed, message(
        en="The truthy rule must only accept true/false (strict YAML 1.2)",
        fr="La règle truthy doit n'admettre que true/false (YAML 1.2 strict)",
    )
    assert "yes" not in allowed and "no" not in allowed, message(
        en="yes/no must no longer be accepted: they are the YAML 1.1 traps",
        fr="yes/no ne doivent plus être admis : ce sont les pièges YAML 1.1",
    )


def test_pre_commit_config_written():
    f = LAB_ROOT / ".pre-commit-config.yaml"
    config = yaml.safe_load(f.read_text())
    repos = config.get("repos") or []
    assert repos, message(
        en=".pre-commit-config.yaml must declare hook repos",
        fr=".pre-commit-config.yaml doit déclarer des repos de hooks",
    )
    hook_ids = [
        h.get("id")
        for repo in repos
        for h in (repo.get("hooks") or [])
        if isinstance(h, dict)
    ]
    assert "yamllint" in hook_ids, message(
        en="The yamllint hook is missing",
        fr="Il manque le hook yamllint",
    )
    assert "ansible-lint" in hook_ids, message(
        en="The ansible-lint hook is missing",
        fr="Il manque le hook ansible-lint",
    )
    assert "detect-private-key" in hook_ids, message(
        en="detect-private-key is missing: the hook that blocks key leaks",
        fr="Il manque detect-private-key : le hook qui bloque les fuites de clés",
    )
    content = f.read_text()
    assert "production" in content, message(
        en="The ansible-lint hook must enforce the production profile (args)",
        fr="Le hook ansible-lint doit imposer le profil production (args)",
    )


def test_role_still_does_its_job():
    """Garde-fou : corriger le lint ne veut pas dire vider le rôle."""
    tasks = yaml.safe_load(TASKS.read_text())
    assert isinstance(tasks, list) and len(tasks) >= 5, message(
        en="The role must keep its tasks (install, configure, deploy, open the "
        "port, start): we fix the style, not the behaviour",
        fr="Le rôle doit garder ses tâches (installer, configurer, déployer, "
        "ouvrir le port, démarrer) : on corrige le style, pas le comportement",
    )
    dumped = yaml.dump(tasks)
    assert "nginx.conf.j2" in dumped, message(
        en="The nginx.conf.j2 template must still be deployed",
        fr="Le template nginx.conf.j2 doit toujours être déployé",
    )
    assert "firewalld" in dumped, message(
        en="Opening the firewalld port must stay",
        fr="L'ouverture du port firewalld doit rester",
    )


def test_ansible_lint_production_passes():
    """Exécute réellement ansible-lint --profile production sur le rôle.

    C'est LE test du lab : un lab de lint qui ne linte jamais ne prouve
    rien. Le rôle livré échoue avec une dizaine de findings, il doit
    sortir à 0.
    """
    assert shutil.which("ansible-lint"), message(
        en="ansible-lint is not on this machine: install it "
        "(pipx install ansible-lint), it is the tool this lab teaches",
        fr="ansible-lint est introuvable sur le poste : installez-le "
        "(pipx install ansible-lint), c'est l'outil enseigné par ce lab",
    )
    result = subprocess.run(
        ["ansible-lint", "--profile", "production", "--nocolor", "roles/"],
        cwd=LAB_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, message(
        en="ansible-lint --profile production still fails on the role:\n"
        f"{result.stdout[-4000:]}{result.stderr[-2000:]}",
        fr="ansible-lint --profile production échoue encore sur le rôle :\n"
        f"{result.stdout[-4000:]}{result.stderr[-2000:]}",
    )


def test_yamllint_passes():
    """Exécute réellement yamllint avec votre configuration (skip si absent)."""
    if shutil.which("yamllint") is None:
        pytest.skip(
            "yamllint absent du poste : pipx install yamllint pour valider "
            "ce point (ansible-lint couvre déjà les règles yaml[...])"
        )
    result = subprocess.run(
        ["yamllint", "-c", ".yamllint", "roles/"],
        cwd=LAB_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, message(
        en=f"yamllint fails with your configuration:\n{result.stdout}{result.stderr}",
        fr=f"yamllint échoue avec votre configuration :\n{result.stdout}{result.stderr}",
    )
