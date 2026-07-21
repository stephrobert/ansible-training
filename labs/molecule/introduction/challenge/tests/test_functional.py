"""Tests du scénario Molecule écrit par l'apprenant (lab 62).

Les trois fichiers du scénario sont livrés en squelette : ces tests ne
passent que lorsque l'apprenant les a réellement complétés. Ils chargent
le YAML, contrôlent la sémantique, puis exécutent `molecule syntax` pour
prouver que le scénario est accepté par l'outil (sans créer d'instance,
donc sans besoin de Podman).
"""

import os
import shutil
import subprocess
from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"


def _load(name):
    return yaml.safe_load((MOLECULE_DIR / name).read_text())


def test_scenario_files_present():
    for name in ("molecule.yml", "converge.yml", "verify.yml"):
        assert (MOLECULE_DIR / name).exists(), (
            f"molecule/default/{name} manquant : le squelette livré a-t-il été supprimé ?"
        )


def test_molecule_yml_has_driver():
    config = _load("molecule.yml")
    driver = config.get("driver", {}).get("name")
    assert driver in ("default", "delegated", "docker", "podman"), (
        f"driver.name invalide ({driver!r}) : le driver moderne de Molecule "
        "v6+ s'appelle 'default'"
    )


def test_molecule_yml_has_platforms():
    config = _load("molecule.yml")
    platforms = config.get("platforms") or []
    assert len(platforms) >= 1, (
        "Déclarez au moins une plateforme (name, image systemd, "
        "pre_build_image, command /sbin/init)"
    )
    for p in platforms:
        assert "name" in p and "image" in p, (
            "Chaque plateforme doit déclarer au minimum name et image"
        )


def test_molecule_yml_has_verifier():
    config = _load("molecule.yml")
    verifier = config.get("verifier", {}).get("name")
    assert verifier in ("ansible", "testinfra", "goss"), (
        f"verifier.name invalide ({verifier!r}) : pour ce lab, les "
        "assertions sont en Ansible natif (verify.yml)"
    )


def test_converge_applies_webserver_role():
    plays = _load("converge.yml")
    assert isinstance(plays, list) and plays, "converge.yml doit contenir un play"
    play = plays[0]
    roles = play.get("roles") or []
    role_names = [r.get("role") if isinstance(r, dict) else r for r in roles]
    includes = [
        t
        for t in (play.get("tasks") or [])
        if isinstance(t, dict)
        and any("include_role" in k or "import_role" in k for k in t)
    ]
    assert "webserver" in role_names or includes, (
        "converge.yml doit appliquer le rôle 'webserver' (section roles: "
        "ou include_role/import_role)"
    )
    assert play.get("become") is True, (
        "converge.yml doit élever les privilèges (become: true) : le rôle "
        "installe des paquets et gère des services"
    )


def test_verify_has_real_assertions():
    plays = _load("verify.yml")
    assert isinstance(plays, list) and plays, "verify.yml doit contenir un play"
    tasks = plays[0].get("tasks") or []
    asserts = [t for t in tasks if isinstance(t, dict) and "ansible.builtin.assert" in t]
    assert len(asserts) >= 2, (
        f"Au moins 2 tâches ansible.builtin.assert attendues, vu : {len(asserts)}. "
        "Prouvez l'état : paquet nginx installé ET /etc/nginx/nginx.conf présent"
    )
    for t in asserts:
        body = t["ansible.builtin.assert"]
        assert body and body.get("that"), (
            "Chaque assert doit porter une condition 'that:' non vide"
        )


def _assert_that_text(task):
    """Texte concaténé (minuscule) des conditions `that:` d'une tâche assert."""
    that = task["ansible.builtin.assert"].get("that") or []
    if isinstance(that, str):
        that = [that]
    return " ".join(str(c) for c in that).lower()


# Notions d'état concret : un `that:` qui prouve quelque chose de nginx doit
# parler d'un paquet, d'un service ou d'un fichier — pas juste exister.
_STATE_TOKENS = (
    # paquet
    "package", "paquet", "rpm", "dpkg", "installed", "installé",
    # service
    "service", "systemd", "started", "running", "active",
    # fichier / configuration
    "stat", "exists", "isreg", "conf", "path", "file", "fichier",
)


def test_verify_asserts_prove_nginx_state():
    """Le CONTENU des `that:` doit prouver un état concret de nginx.

    `test_verify_has_real_assertions` ne fait que compter les asserts et exiger
    un `that:` non vide : deux `ansible.builtin.assert: {that: [true]}` le
    passent sans rien prouver. Or l'énoncé (challenge/README.md) promet des
    assertions qui prouvent l'ÉTAT — « le paquet nginx est installé »,
    « /etc/nginx/nginx.conf existe ». On exige donc qu'au moins un assert porte,
    dans ses conditions `that:`, la sous-chaîne 'nginx' ET une notion d'état
    concret (paquet / service / fichier). La solution de référence le fait via
    `nginx_package.rc == 0` et `nginx_conf.stat.exists`.
    """
    plays = _load("verify.yml")
    assert isinstance(plays, list) and plays, "verify.yml doit contenir un play"
    tasks = plays[0].get("tasks") or []
    asserts = [t for t in tasks if isinstance(t, dict) and "ansible.builtin.assert" in t]

    proving = [
        _assert_that_text(t)
        for t in asserts
        if "nginx" in _assert_that_text(t)
        and any(tok in _assert_that_text(t) for tok in _STATE_TOKENS)
    ]
    assert proving, (
        "Aucune condition `that:` ne prouve un état concret de nginx. L'énoncé "
        "demande de prouver le paquet nginx installé ET /etc/nginx/nginx.conf "
        "présent : au moins une assertion doit porter, dans son `that:`, la "
        "sous-chaîne 'nginx' et une notion de paquet/service/fichier "
        "(ex. `nginx_package.rc == 0`, `nginx_conf.stat.exists`). "
        f"`that:` vus : {[_assert_that_text(t) for t in asserts]!r}"
    )


def test_molecule_syntax_passes():
    """Exécute réellement `molecule syntax` sur le scénario de l'apprenant.

    L'action syntax valide dependency + syntax-check ansible-playbook sans
    créer d'instance : pas besoin de Podman ni de réseau.
    """
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
        f"`molecule syntax` échoue sur votre scénario :\n{result.stdout}{result.stderr}"
    )
