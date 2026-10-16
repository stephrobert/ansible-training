"""Tests pytest+testinfra du challenge consommer-role.

On prouve l'état de db1.lab, pas le contenu du YAML :
- le rôle consommé via `roles:` a réellement déployé nginx (paquet,
  service, port, page) ;
- l'import statique gardé par un flag éteint n'a PAS posé sa trace, mais
  a exposé les defaults du rôle (chargé au parsing) ;
- l'include dynamique sous condition runtime a posé sa trace, mais garde
  ses variables privées.
Le module orchestre lui-même le run (reset des traces puis solution.yml)
pour que les assertions négatives ne soient pas faussées par un passage
précédent.
"""

import os
import subprocess

import pytest

# REPO_ROOT vient de conftest : le compter en parents[] depuis ce fichier donnait
# labs/ (un cran trop bas), donc un cwd sans ansible.cfg (ni inventaire, ni clé).
from conftest import REPO_ROOT, assert_idempotent, lab_host, lab_playbook, message

# Ce module orchestre lui-même ses runs : le marqueur désactive le replay
# POUR CE MODULE. Poser os.environ["LAB_NO_REPLAY"] ici le désactivait pour
# toute la session, dès la collecte, y compris pour les labs voisins.
pytestmark = pytest.mark.no_replay


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


@pytest.fixture(scope="module", autouse=True)
def _converge():
    """Reset des traces puis run de la solution (apprenant, sinon référence)."""
    subprocess.run(
        [
            "ansible", "db1.lab", "-b",
            "-m", "ansible.builtin.shell",
            "-a", "rm -f /tmp/consommer-*.txt",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    # La référence du formateur est chiffrée : sans vault_args, ansible-playbook
    # ne lit que du $ANSIBLE_VAULT.
    playbook, vault_args = lab_playbook(__file__)
    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = "labs/roles/consommer-role/roles"
    result = subprocess.run(
        ["ansible-playbook", *vault_args, str(playbook)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"solution.yml a échoué (exit {result.returncode})\n"
            f"--- stdout ---\n{result.stdout[-2000:]}\n"
            f"--- stderr ---\n{result.stderr[-1000:]}"
        )


# ---------------------------------------------------------------- play 1


def test_nginx_installe(db1):
    assert db1.package("nginx").is_installed, message(
        en="nginx is absent from db1: play 1 (roles:) did not deploy the role.",
        fr="nginx absent de db1 : le play 1 (roles:) n'a pas déployé le rôle.",
    )


def test_nginx_demarre_et_active(db1):
    svc = db1.service("nginx")
    assert svc.is_running, message(
        en="nginx must be started on db1.",
        fr="nginx doit être démarré sur db1.",
    )
    assert svc.is_enabled, message(
        en="nginx must be enabled at boot on db1.",
        fr="nginx doit être activé au boot sur db1.",
    )


def test_nginx_ecoute_8080(db1):
    assert db1.socket("tcp://0.0.0.0:8080").is_listening, message(
        en="nginx does not listen on 8080: webserver_listen_port was not passed "
        "to the role in play 1.",
        fr="nginx n'écoute pas sur 8080 : webserver_listen_port n'a pas été "
        "passé au rôle dans le play 1.",
    )


def test_page_accueil_deployee(db1):
    index = db1.file("/usr/share/nginx/html/index.html")
    assert index.exists, message(
        en="The role's home page is not deployed.",
        fr="La page d'accueil du rôle n'est pas déployée.",
    )
    assert "Hello from db1.lab" in index.content_string, message(
        en="The page does not carry « Hello from db1.lab »: the role's "
           "template renders the host name, it is not written by hand.",
        fr="La page ne porte pas « Hello from db1.lab » : le template du "
           "rôle rend le nom d'hôte, il ne s'écrit pas à la main.",
    )
    assert index.mode == 0o644, message(
        en=f"The page is {oct(index.mode)}, expected 0644.",
        fr=f"La page est en {oct(index.mode)}, attendu 0644.",
    )


# ---------------------------------------------------------------- play 2


def test_import_garde_par_flag_na_pas_tourne(db1):
    """import_role + when(flag éteint) : la trace ne doit PAS exister.

    Le when: d'un import est recopié sur chaque tâche importée : avec
    deploy_extras=false, aucune ne tourne. Si ce fichier existe, le flag
    n'a pas été honoré (ou la trace a été posée sans condition).
    """
    assert not db1.file("/tmp/consommer-import.txt").exists, message(
        en="/tmp/consommer-import.txt exists: the import guarded by "
        "deploy_extras=false still left its trace.",
        fr="/tmp/consommer-import.txt existe : l'import gardé par "
        "deploy_extras=false a quand même posé sa trace.",
    )


def test_import_expose_les_defaults_du_role(db1):
    """Même sans exécuter une seule tâche, l'import a chargé le rôle.

    C'est le sens de « statique » : au parsing, les defaults du rôle
    (webserver_package=nginx) deviennent visibles pour tout le play.
    """
    trace = db1.file("/tmp/consommer-vars-import.txt")
    assert trace.exists, message(
        en="/tmp/consommer-vars-import.txt missing: play 2's trace task did not "
        "run.",
        fr="/tmp/consommer-vars-import.txt absent : la tâche de trace du "
        "play 2 n'a pas tourné.",
    )
    assert "package=nginx" in trace.content_string, message(
        en="Play 2 was meant to see webserver_package=nginx: an import_role "
        "loads the role at parse time and exposes its defaults, even when its "
        "when: stops all its tasks from running. If you read UNDEFINED here, "
        "the role was not imported statically.",
        fr="Le play 2 devait voir webserver_package=nginx : un import_role "
        "charge le rôle au parsing et expose ses defaults, même quand son "
        "when: empêche toutes ses tâches de tourner. Si vous lisez "
        "UNDEFINED ici, le rôle n'a pas été importé statiquement.",
    )


# ---------------------------------------------------------------- play 3


def test_include_sous_condition_runtime_a_tourne(db1):
    """include_role + condition runtime vraie : la trace existe."""
    trace = db1.file("/tmp/consommer-include.txt")
    assert trace.exists, message(
        en="/tmp/consommer-include.txt missing: the include_role conditioned on "
        "nginx's runtime state did not run (nginx inactive, or a badly "
        "written condition).",
        fr="/tmp/consommer-include.txt absent : l'include_role conditionné "
        "par l'état runtime de nginx n'a pas tourné (nginx inactif, ou "
        "condition mal écrite).",
    )
    assert "via include" in trace.content_string, message(
        en="The trace does not say « via include »: the file exists, but "
           "nothing proves it was the include_role that wrote it.",
        fr="La trace ne dit pas « via include » : le fichier existe, mais "
           "rien ne prouve que c'est l'include_role qui l'a écrit.",
    )


def test_include_garde_ses_variables_privees(db1):
    """Après un include_role (non public), les defaults restent invisibles."""
    trace = db1.file("/tmp/consommer-vars-include.txt")
    assert trace.exists, message(
        en="/tmp/consommer-vars-include.txt missing: play 3's trace task did not "
        "run.",
        fr="/tmp/consommer-vars-include.txt absent : la tâche de trace du "
        "play 3 n'a pas tourné.",
    )
    assert "package=UNDEFINED" in trace.content_string, message(
        en="Play 3 was NOT meant to see webserver_package: an include_role "
        "resolved at runtime keeps its variables private (public: false by "
        "default). If you read package=nginx, either the role was imported "
        "statically in this play, or webserver_package is defined elsewhere "
        "in your playbook.",
        fr="Le play 3 ne devait PAS voir webserver_package : un include_role "
        "résolu au runtime garde ses variables privées (public: false par "
        "défaut). Si vous lisez package=nginx, soit le rôle a été importé "
        "statiquement dans ce play, soit webserver_package est défini "
        "ailleurs dans votre playbook.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
