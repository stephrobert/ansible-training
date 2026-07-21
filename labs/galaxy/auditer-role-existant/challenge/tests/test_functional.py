"""Tests du lab 75 : audit factuel d'un rôle tiers.

L'apprenant audite vendor/thirdparty_backup/ et livre ses conclusions
dans challenge/audit.yml. Ces tests recalculent chaque fait directement
depuis le code du rôle (parsing YAML, pas de grep de checklist) et les
comparent au rapport : les conclusions doivent être VRAIES, pas
recopiées.
"""

from pathlib import Path

import pytest
import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
ROLE = LAB_ROOT / "vendor" / "thirdparty_backup"
AUDIT = LAB_ROOT / "challenge" / "audit.yml"

# Clés d'une tâche qui ne sont pas des modules.
TASK_KEYWORDS = {
    "name", "when", "loop", "loop_control", "with_items", "register",
    "ignore_errors", "notify", "tags", "vars", "become", "become_user",
    "changed_when", "failed_when", "check_mode", "delegate_to", "until",
    "retries", "delay", "environment", "no_log", "block", "rescue",
    "always", "args",
}


def _tasks():
    return yaml.safe_load((ROLE / "tasks" / "main.yml").read_text())


def _module_of(task):
    candidates = [k for k in task if k not in TASK_KEYWORDS]
    return candidates[0] if candidates else None


def _facts():
    """Recalcule la vérité terrain depuis le code du rôle."""
    tasks = _tasks()
    non_fqcn = 0
    insecure = 0
    unguarded = 0
    ignore_errors = 0
    for task in tasks:
        module = _module_of(task)
        if module and "." not in module:
            non_fqcn += 1
        if module and module.split(".")[-1] == "get_url":
            url = str(task[module].get("url", ""))
            if url.startswith("http://") or "checksum" not in task[module]:
                insecure += 1
        if module and module.split(".")[-1] in ("shell", "command"):
            params = task[module]
            params = params if isinstance(params, dict) else {}
            guards = set(params) | set(task.get("args") or {})
            if not {"creates", "removes"} & guards:
                unguarded += 1
        if task.get("ignore_errors") is True:
            ignore_errors += 1
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())
    secret = any(
        any(hint in key.lower() for hint in ("password", "secret", "token"))
        and isinstance(value, str)
        and value
        for key, value in defaults.items()
    )
    return {
        "has_argument_specs": (ROLE / "meta" / "argument_specs.yml").is_file(),
        "has_molecule_tests": (ROLE / "molecule").is_dir(),
        "non_fqcn_task_count": non_fqcn,
        "insecure_download_count": insecure,
        "unguarded_shell_count": unguarded,
        "ignore_errors_count": ignore_errors,
        "secret_in_defaults": secret,
    }


def _audit():
    assert AUDIT.is_file(), (
        "challenge/audit.yml manquant : livrez votre rapport d'audit au "
        "format documenté dans challenge/README.md"
    )
    data = yaml.safe_load(AUDIT.read_text())
    assert isinstance(data, dict), "audit.yml doit être un mapping YAML"
    return data


def test_role_under_audit_untouched():
    """Le rôle audité ne doit pas être modifié : on audite, on ne corrige pas."""
    tasks = _tasks()
    assert len(tasks) >= 4, (
        "vendor/thirdparty_backup/tasks/main.yml semble modifié : l'audit "
        "porte sur le rôle TEL QUE LIVRÉ (dsoxlab clean le restaure)"
    )


def test_audit_identifies_role():
    audit = _audit()
    assert audit.get("role") == "thirdparty_backup", (
        "audit.yml doit identifier le rôle audité (role: thirdparty_backup)"
    )


@pytest.mark.parametrize(
    "key",
    [
        "has_argument_specs",
        "has_molecule_tests",
        "non_fqcn_task_count",
        "insecure_download_count",
        "unguarded_shell_count",
        "ignore_errors_count",
        "secret_in_defaults",
    ],
)
def test_audit_facts_are_true(key):
    """Chaque conclusion du rapport est recalculée depuis le code du rôle."""
    audit = _audit()
    facts = _facts()
    assert key in audit, (
        f"audit.yml : clé {key!r} manquante (voir le format dans "
        "challenge/README.md)"
    )
    assert audit[key] == facts[key], (
        f"audit.yml : {key} = {audit[key]!r}, or l'analyse du rôle donne "
        f"{facts[key]!r}. Retournez lire le code du rôle : un audit "
        "n'affirme que ce qu'il a vérifié"
    )


def test_audit_verdict_consistent():
    """Secret en clair + zéro test : la conclusion ne fait pas débat."""
    audit = _audit()
    score = audit.get("score")
    assert isinstance(score, int) and 0 <= score <= 10, (
        "audit.yml : score doit être un entier entre 0 et 10"
    )
    assert score <= 4, (
        f"Score {score}/10 trop indulgent : mot de passe en clair dans "
        "defaults, aucun test, idempotence cassée. Relisez la grille de "
        "AUDIT_CHECKLIST.md"
    )
    assert audit.get("verdict") == "reject", (
        "Verdict attendu : reject. Un rôle qui embarque un secret en clair "
        "et n'a aucun test ne s'adopte pas et ne se forke pas tel quel"
    )
