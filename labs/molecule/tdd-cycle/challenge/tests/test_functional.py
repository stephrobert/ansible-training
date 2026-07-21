"""Tests du lab 64 : cycle TDD réel avec Molecule.

verify.yml et tasks/main.yml sont livrés VIDES : c'est l'apprenant qui
écrit les tests (RED) puis le rôle (GREEN). Ces tests pytest contrôlent
la sémantique des deux fichiers (parsing YAML, pas de grep), vérifient
que les données du contrat (converge.yml) n'ont pas été altérées, et
exécutent réellement `molecule syntax`. Le cycle complet `molecule test`
est exécuté si LAB_MOLECULE_FULL=1 (nécessite Podman).
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"
ROLE_DIR = LAB_ROOT / "roles" / "users"


def _verify_asserts():
    plays = yaml.safe_load((MOLECULE_DIR / "verify.yml").read_text())
    if not isinstance(plays, list) or not plays:
        return []
    tasks = plays[0].get("tasks") or []
    return [t for t in tasks if isinstance(t, dict) and "ansible.builtin.assert" in t]


def test_argument_specs_untouched():
    """Le contrat d'entrée (livré) doit rester la référence."""
    spec = yaml.safe_load((ROLE_DIR / "meta/argument_specs.yml").read_text())
    assert "users_to_create" in spec["argument_specs"]["main"]["options"], (
        "meta/argument_specs.yml doit toujours spécifier users_to_create : "
        "en TDD, le contrat précède le code"
    )


def test_converge_data_untouched():
    """Les données d'entrée (livrées) ne doivent pas être affaiblies."""
    content = (MOLECULE_DIR / "converge.yml").read_text()
    plays = yaml.safe_load(content)
    users = plays[0].get("vars", {}).get("users_to_create", [])
    by_name = {u.get("name"): u for u in users if isinstance(u, dict)}
    assert {"alice", "bob", "carol"} <= set(by_name), (
        "converge.yml doit garder alice, bob et carol : ce sont les données "
        "que vos tests spécifient"
    )
    assert by_name["alice"].get("shell") == "/bin/zsh", (
        "alice doit garder shell /bin/zsh dans converge.yml"
    )
    assert "wheel" in (by_name["alice"].get("groups") or []), (
        "alice doit garder le groupe wheel dans converge.yml"
    )


def test_verify_written_first_with_4_assertions():
    asserts = _verify_asserts()
    assert len(asserts) >= 4, (
        f"Au moins 4 tâches ansible.builtin.assert attendues dans verify.yml, "
        f"vu : {len(asserts)}. En TDD, chaque comportement attendu a son test "
        "(alice shell + groupe, bob, carol)"
    )
    for t in asserts:
        body = t["ansible.builtin.assert"]
        assert body.get("that"), "Chaque assert doit porter une condition that: non vide"
        assert body.get("fail_msg"), (
            "Chaque assert doit porter un fail_msg : un test rouge doit dire "
            "POURQUOI il est rouge"
        )


def test_verify_covers_all_users():
    dumped = yaml.dump(yaml.safe_load((MOLECULE_DIR / "verify.yml").read_text()))
    for user in ("alice", "bob", "carol"):
        assert user in dumped, (
            f"verify.yml ne teste pas {user} : tous les utilisateurs du "
            "converge doivent être spécifiés"
        )
    assert "/bin/zsh" in dumped, "verify.yml doit vérifier le shell zsh d'alice"
    assert "wheel" in dumped, "verify.yml doit vérifier l'appartenance d'alice à wheel"


def test_role_tasks_loop_over_contract():
    tasks = yaml.safe_load((ROLE_DIR / "tasks/main.yml").read_text())
    assert isinstance(tasks, list) and tasks, (
        "roles/users/tasks/main.yml est vide : écrivez le minimum qui rend "
        "vos tests verts (étape GREEN, après le RED)"
    )
    user_tasks = [
        t for t in tasks if isinstance(t, dict) and any("user" in k for k in t)
    ]
    assert user_tasks, "Le rôle doit utiliser le module ansible.builtin.user"
    task = user_tasks[0]
    loop_expr = str(task.get("loop") or task.get("with_items") or "")
    assert "users_to_create" in loop_expr, (
        "La création doit boucler sur users_to_create (loop:), pas énumérer "
        "les utilisateurs en dur"
    )
    module_args = task.get("ansible.builtin.user") or task.get("user") or {}
    assert "users_default_shell" in str(module_args.get("shell", "")), (
        "Le shell doit retomber sur users_default_shell quand l'entrée n'en "
        "donne pas : {{ item.shell | default(users_default_shell) }}"
    )
    assert module_args.get("append") is True, (
        "append: true attendu : on ajoute les groupes sans écraser ceux "
        "existants"
    )


def test_molecule_syntax_passes():
    """Exécute réellement `molecule syntax` (sans instance, sans Podman)."""
    assert shutil.which("molecule"), (
        "molecule est introuvable sur le poste : installez-le "
        "(pipx install molecule), c'est l'outil enseigné par ce lab"
    )
    env = dict(os.environ, ANSIBLE_ROLES_PATH=str(LAB_ROOT / "roles"))
    result = subprocess.run(
        ["molecule", "syntax"],
        cwd=LAB_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"`molecule syntax` échoue :\n{result.stdout}{result.stderr}"
    )


@pytest.mark.slow
def test_molecule_full_cycle_green():
    """Cycle complet rouge -> vert : `molecule test` exécuté pour de vrai.

    C'est LA preuve finale du lab, et elle était skippée par défaut : il
    fallait poser LAB_MOLECULE_FULL=1 pour l'obtenir. Un garde qui masque la
    preuve centrale d'un lab en fait un lab qui ne prouve rien, et c'est ce qui
    a laissé ce lab injouable si longtemps (aucun scénario ne montait
    d'instance, personne ne le voyait).

    Le garde invoquait « plusieurs minutes » : mesuré, le cycle complet prend
    24 secondes, image en cache. Il passe donc par le marqueur `slow`, comme le
    reboot du capstone : joué par défaut, désélectionnable en environnement
    contraint avec `pytest -m 'not slow'`.
    """
    env = dict(os.environ, ANSIBLE_ROLES_PATH=str(LAB_ROOT / "roles"))
    result = subprocess.run(
        ["molecule", "test"],
        cwd=LAB_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, (
        f"`molecule test` échoue : vos tests ne sont pas encore verts.\n"
        f"{result.stdout[-5000:]}{result.stderr[-2000:]}"
    )

    # Un code retour nul ne suffit pas à prouver qu'une instance a existé.
    # Le driver « default » est délégué : sans create.yml, Molecule saute
    # l'étape « create » en n'émettant qu'un avertissement. Ce lab a
    # réellement vécu dans cet état, et le cycle passait pour « joué »
    # alors qu'aucun conteneur n'avait jamais démarré. On exige donc la
    # preuve que create a tourné, et que verify a rendu son verdict.
    assert "create] Executed: Successful" in combined, (
        "`molecule test` n'a pas réellement créé d'instance : l'étape "
        "create a été sautée (create.yml manquant ?). Le driver « default » "
        "ne crée rien tout seul.\n" + combined[-3000:]
    )
    assert "verify] Executed: Successful" in combined, (
        "`molecule test` n'a pas exécuté verify : vos assertions n'ont "
        "jamais été jouées.\n" + combined[-3000:]
    )
