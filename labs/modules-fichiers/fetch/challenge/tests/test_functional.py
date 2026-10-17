"""Tests pytest pour le challenge module fetch.

Particularité : `fetch:` rapatrie des fichiers du managed node vers le
control node. Les tests vérifient des fichiers LOCAUX (côté
control node = la machine où tourne pytest), pas via testinfra ssh.
"""

import os
from pathlib import Path

from conftest import assert_idempotent, message

# Le dest fetch est relatif au cwd du playbook ansible-playbook, soit la racine
# du dépôt. On la déduit de l'emplacement de ce fichier
# (labs/<section>/<lab>/challenge/tests/) plutôt que de la coder en dur :
# le dépôt se clone où l'apprenant veut. ANSIBLE_TRAINING_ROOT reste
# prioritaire pour les cas particuliers.
_REPO_ROOT = Path(__file__).resolve().parents[5]
COLLECTED_DIR = Path(os.environ.get("ANSIBLE_TRAINING_ROOT", _REPO_ROOT)) / "collected"


def test_collected_dir_exists():
    assert COLLECTED_DIR.is_dir(), message(
        en=f"The {COLLECTED_DIR} directory does not exist. fetch's dest: is "
           f"relative to the directory ansible-playbook was launched from, "
           f"which must be the root of the repository.",
        fr=f"Le répertoire {COLLECTED_DIR} n'existe pas. Le dest: de fetch "
           f"est relatif au répertoire d'où ansible-playbook a été lancé, qui "
           f"doit être la racine du dépôt.",
    )


def test_web1_os_release_fetched():
    f = COLLECTED_DIR / "web1-os-release.txt"
    assert f.exists(), message(
        en=f"{f.name} was not fetched. By default fetch rebuilds the whole "
           f"remote path under dest: use flat: true to land on the exact "
           f"name the mission asks for.",
        fr=f"{f.name} n'a pas été rapatrié. Par défaut, fetch reconstruit "
           f"tout le chemin distant sous dest: utilise flat: true pour "
           f"atterrir sur le nom exact que demande la mission.",
    )
    assert "NAME=" in f.read_text(), message(
        en=f"{f.name} does not hold an os-release: the fetched file is not "
           f"/etc/os-release.",
        fr=f"{f.name} ne porte pas un os-release : le fichier rapatrié n'est "
           f"pas /etc/os-release.",
    )


def test_db1_os_release_fetched():
    f = COLLECTED_DIR / "db1-os-release.txt"
    assert f.exists(), message(
        en=f"{f.name} was not fetched, while web1's was: the play only "
           f"targets one host, or dest: does not depend on "
           f"inventory_hostname and the two files overwrite each other.",
        fr=f"{f.name} n'a pas été rapatrié alors que celui de web1 l'a été : "
           f"le play ne vise qu'un hôte, ou dest: ne dépend pas "
           f"d'inventory_hostname et les deux fichiers s'écrasent.",
    )
    assert "NAME=" in f.read_text(), message(
        en=f"{f.name} does not hold an os-release.",
        fr=f"{f.name} ne porte pas un os-release.",
    )


def test_web1_tag_content():
    f = COLLECTED_DIR / "web1-tag.txt"
    assert f.exists(), message(
        en=f"{f.name} was not fetched.",
        fr=f"{f.name} n'a pas été rapatrié.",
    )
    assert "RHCE-LAB-2026" in f.read_text(), message(
        en=f"{f.name} does not hold RHCE-LAB-2026: the tag file has to be "
           f"written on the remote host before being fetched back.",
        fr=f"{f.name} ne porte pas RHCE-LAB-2026 : le fichier de tag doit "
           f"être écrit sur l'hôte distant avant d'être rapatrié.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Ce lab n'avait aucun contrôle d'idempotence, et sans la justification que
    portent les trois labs légitimement exemptés (touch, async, changed_when).
    C'était un oubli : `fetch` compare les sommes de contrôle et ne rapatrie
    pas un fichier identique, la solution converge (mesuré).
    """
    assert_idempotent(__file__)
