"""Tests pytest+testinfra du lab ansible-pull (hors EX294).

Le test remet db1 à zéro, exécute le solution.sh de l'apprenant, puis
prouve l'état de db1.lab : ansible-pull a réellement cloné le dépôt dans
/var/lib/ansible-pull et le playbook tiré a posé son marqueur en root.
Pas de solution.yml ici : le mode pull s'orchestre en shell, le conftest
ne rejoue donc rien (LAB_NO_REPLAY).
"""

import subprocess
from pathlib import Path

import pytest

from conftest import lab_host, lab_script, REPO_ROOT

LAB_ROOT = Path(__file__).resolve().parents[2]
REPO_PULL = LAB_ROOT / "repo-pull"

# Ce module orchestre lui-même ses runs : le marqueur désactive le replay
# POUR CE MODULE. Poser os.environ["LAB_NO_REPLAY"] ici le désactivait pour
# toute la session, dès la collecte, y compris pour les labs voisins.
# UNE SEULE affectation : `pytestmark` est une variable ordinaire, une seconde
# affectation ÉCRASE la première sans un mot. C'est ce qui se passait ici, et le
# no_replay était perdu.
#
# Le skipif qui suivait est supprimé : il rendait ce lab injouable en mode
# formateur, où challenge/solution.sh n'existe pas. La fixture pose désormais
# la référence (solution/pratiques/ansible-pull-gitops/solution.sh) et la
# retire après le module.
pytestmark = pytest.mark.no_replay


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


@pytest.fixture(scope="module", autouse=True)
def _run_solution():
    """Reset de db1 puis exécution du solution.sh de l'apprenant.

    Le reset garantit que l'état observé a bien été produit par CE run,
    pas par un passage précédent.
    """
    subprocess.run(
        [
            "ansible", "db1.lab", "-b",
            "-m", "ansible.builtin.shell",
            "-a", "rm -rf /tmp/lab98-pull-marker.txt /var/lib/ansible-pull",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        # Le script réellement en jeu : celui de l'apprenant s'il existe, la
        # référence chiffrée sinon (matérialisée en tmp, jamais dans le lab).
        # Ce module est `no_replay`, la fixture ne pose donc rien pour lui.
        ["bash", str(lab_script(__file__))],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"solution.sh a échoué (exit {result.returncode})\n"
            f"--- stdout ---\n{result.stdout[-2000:]}\n"
            f"--- stderr ---\n{result.stderr[-2000:]}"
        )


def test_repo_pull_est_un_depot_git():
    """Le dépôt source existe côté control node et est un vrai dépôt Git."""
    assert (REPO_PULL / "pull-playbook.yml").is_file(), (
        f"{REPO_PULL}/pull-playbook.yml absent : créez le dépôt en suivant "
        "challenge/README.md."
    )
    assert (REPO_PULL / ".git").is_dir(), (
        f"{REPO_PULL} n'est pas un dépôt Git (pas de .git/) : ansible-pull "
        "ne peut cloner qu'un dépôt initialisé et commité."
    )


def test_ansible_pull_a_clone_le_depot(db1):
    """/var/lib/ansible-pull sur db1 est le clone produit par ansible-pull.

    Si le marqueur avait été copié à la main (scp, ad-hoc copy), ce clone
    n'existerait pas : c'est lui qui prouve le passage en mode pull.
    """
    clone = db1.file("/var/lib/ansible-pull")
    assert clone.is_directory, (
        "/var/lib/ansible-pull absent sur db1 : ansible-pull n'a pas tourné "
        "(ou sans -d /var/lib/ansible-pull)."
    )
    assert db1.file("/var/lib/ansible-pull/.git").is_directory, (
        "/var/lib/ansible-pull n'est pas un clone Git : ansible-pull clone "
        "le dépôt passé en -U, il ne copie pas des fichiers."
    )
    assert db1.file("/var/lib/ansible-pull/pull-playbook.yml").is_file, (
        "pull-playbook.yml absent du clone : le dépôt commité ne contient "
        "pas le playbook (git add + git commit oubliés ?)."
    )


def test_marqueur_pose_par_le_pull(db1):
    """Le playbook tiré a posé son marqueur, en root, sur db1 lui-même."""
    marker = db1.file("/tmp/lab98-pull-marker.txt")
    assert marker.exists, (
        "/tmp/lab98-pull-marker.txt absent sur db1 : le playbook tiré n'a "
        "pas été exécuté (nom de playbook erroné pour ansible-pull ?)."
    )
    assert marker.user == "root", (
        "Le marqueur doit appartenir à root : lancez ansible-pull avec "
        "élévation (become) pour que le play s'applique en root."
    )
    assert marker.mode == 0o644

    content = marker.content_string
    assert "ansible-pull executed" in content, (
        "Le marqueur doit contenir 'ansible-pull executed' (cf. contrat du "
        "challenge)."
    )
    assert "db1" in content, (
        "Le marqueur doit contenir le hostname de la machine qui a exécuté "
        "le play ({{ ansible_hostname }}) : c'est la preuve que db1 s'est "
        "configuré lui-même, et non le control node."
    )
