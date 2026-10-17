"""Tests pytest+testinfra pour le challenge lab 03a — configuration Ansible."""

import configparser
import re
from pathlib import Path

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab03a-config.txt"

LAB_DIR = Path(__file__).resolve().parents[2]
ANSIBLE_CFG = LAB_DIR / "ansible.cfg"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_ansible_cfg_exists():
    assert ANSIBLE_CFG.is_file(), message(
        en=f"{ANSIBLE_CFG} missing: create the file, following the challenge's hints.",
        fr=f"{ANSIBLE_CFG} absent — créez le fichier en suivant les indices du challenge.",
    )


def test_ansible_cfg_has_forks_20():
    cfg = configparser.ConfigParser()
    cfg.read(ANSIBLE_CFG)
    assert cfg.get("defaults", "forks", fallback=None) == "20", message(
        en="ansible.cfg [defaults] must set forks = 20",
        fr="ansible.cfg [defaults] doit définir forks = 20",
    )


def test_ansible_cfg_has_yaml_result_format():
    """La sortie YAML doit être demandée par la clé qui la produit réellement.

    `stdout_callback = yaml` était le réglage d'avant ansible-core 2.19 ; le
    plugin a été supprimé. Et son remplaçant a un nom trompeur : l'option se
    documente `result_format`, mais sa clé INI est `callback_result_format`.
    Écrire `result_format = yaml` dans un ansible.cfg ne produit rien et ne
    lève rien, la sortie reste en JSON.
    """
    cfg = configparser.ConfigParser()
    cfg.read(ANSIBLE_CFG)
    assert cfg.get("defaults", "callback_result_format", fallback=None) == "yaml", message(
        en="ansible.cfg [defaults] must set callback_result_format = yaml",
        fr="ansible.cfg [defaults] doit définir callback_result_format = yaml",
    )


def test_ansible_cfg_has_profile_tasks_callback():
    cfg = configparser.ConfigParser()
    cfg.read(ANSIBLE_CFG)
    callbacks = cfg.get("defaults", "callbacks_enabled", fallback="")
    assert "ansible.posix.profile_tasks" in callbacks, message(
        en=f"callbacks_enabled must include ansible.posix.profile_tasks, seen: '{callbacks}'",
        fr=f"callbacks_enabled doit inclure ansible.posix.profile_tasks, vu : '{callbacks}'",
    )


def test_proof_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, message(
        en=f"{RESULT_FILE} missing on {TARGET_HOST}: did solution.yml run with an "
        f"environment: ANSIBLE_CONFIG pointing at the lab's ansible.cfg?",
        fr=f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné "
        f"avec un environment: ANSIBLE_CONFIG qui désigne l'ansible.cfg du lab ?",
    )


def test_proof_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, message(
        en=f"Expected mode 0644, seen: {oct(f.mode)}",
        fr=f"Mode attendu 0644, vu : {oct(f.mode)}",
    )


def test_proof_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root", message(
        en=f"The proof file belongs to {f.user}, expected root.",
        fr=f"Le fichier de preuve appartient à {f.user}, attendu root.",
    )


def test_proof_file_has_at_least_three_lines(host):
    """La sortie de ansible-config dump --only-changed doit contenir ≥3 lignes."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) >= 3, message(
        en=f"{RESULT_FILE} must hold at least 3 non-empty lines, seen: {len(lines)}.\n"
        f"Contents: {content[:200]}",
        fr=f"{RESULT_FILE} doit contenir ≥3 lignes non vides, vu : {len(lines)}.\n"
        f"Contenu : {content[:200]}",
    )


def test_proof_file_contains_config_keys(host):
    """Le contenu doit ressembler à une sortie ansible-config dump (clé FORKS)."""
    content = host.file(RESULT_FILE).content_string
    assert re.search(r"DEFAULT_FORKS|FORKS\b", content), message(
        en="The file must contain a reference to FORKS (ansible-config dump output)",
        fr="Le fichier doit contenir une référence à FORKS (sortie ansible-config dump)",
    )


# ----------------------------------------------------------------------
# Les tests ci-dessus vérifient que le fichier EXISTE et contient les bonnes
# chaînes. C'est utile pour diagnostiquer, mais ça ne prouve pas qu'Ansible
# l'a CHARGÉ : un ansible.cfg parfait au mauvais endroit, ou supplanté par un
# autre (ANSIBLE_CFG, ./ansible.cfg, ~/.ansible.cfg), les satisferait tous.
#
# `ansible-config dump --only-changed --type all` indique, entre parenthèses, la SOURCE de
# chaque valeur. Exiger que la source soit le cfg du lab prouve la précédence,
# qui est justement le sujet de ce lab.
# ----------------------------------------------------------------------


def _dumped(host, key):
    """Ligne du dump pour une clé, ou None. Format : CLÉ(source) = valeur."""
    content = host.file(RESULT_FILE).content_string
    m = re.search(rf"^{re.escape(key)}\(([^)]*)\)\s*=\s*(.+)$", content, re.MULTILINE)
    return (m.group(1), m.group(2).strip()) if m else None


def test_dump_prouve_que_le_cfg_du_lab_est_actif(host):
    """CONFIG_FILE du dump doit désigner l'ansible.cfg du lab."""
    content = host.file(RESULT_FILE).content_string
    m = re.search(r"^CONFIG_FILE\(\)\s*=\s*(.+)$", content, re.MULTILINE)
    assert m, message(
        en="The dump does not contain CONFIG_FILE: did ansible-config run?",
        fr="Le dump ne contient pas CONFIG_FILE : ansible-config a-t-il tourné ?",
    )
    assert m.group(1).strip().endswith(
        "labs/decouvrir/configuration-ansible/ansible.cfg"
    ), message(
        en="Ansible did not load the lab's ansible.cfg, but "
        f"{m.group(1).strip()}. The file can be correct and still inactive: "
        "precedence is what decides.",
        fr="Ansible n'a pas chargé l'ansible.cfg du lab, mais "
        f"{m.group(1).strip()}. Le fichier peut être correct et rester inactif : "
        "c'est la précédence qui décide.",
    )


def test_dump_forks_20_vient_du_cfg_du_lab(host):
    """forks=20 doit être ACTIF et venir du cfg du lab, pas d'ailleurs."""
    got = _dumped(host, "DEFAULT_FORKS")
    assert got, message(
        en="DEFAULT_FORKS absent from the dump: the value is not applied.",
        fr="DEFAULT_FORKS absent du dump : la valeur n'est pas appliquée.",
    )
    source, value = got
    assert value == "20", message(
        en=f"active forks = {value}, expected 20.",
        fr=f"forks actif = {value}, attendu 20.",
    )
    assert source.endswith("labs/decouvrir/configuration-ansible/ansible.cfg"), message(
        en=f"forks=20 is active but comes from « {source} », not the lab's cfg.",
        fr=f"forks=20 est actif mais vient de « {source} », pas du cfg du lab.",
    )


def test_dump_result_format_yaml_vient_du_cfg_du_lab(host):
    """La sortie YAML doit être ACTIVE et venir du cfg du lab.

    Les options de plugin n'apparaissent que dans `--type all` : c'est pour
    cela que le dump du lab le demande. Sans ce drapeau, la clé est absente du
    dump et l'on ne peut rien prouver du tout.
    """
    got = _dumped(host, "result_format")
    assert got, message(
        en="result_format absent from the dump: the YAML output is not applied, "
        "or the dump was taken without --type all.",
        fr="result_format absent du dump : la sortie YAML n'est pas appliquée, "
        "ou le dump a été pris sans --type all.",
    )
    source, value = got
    assert value == "yaml", message(
        en=f"active result_format = {value}, expected yaml.",
        fr=f"result_format actif = {value}, attendu yaml.",
    )
    assert source.endswith("labs/decouvrir/configuration-ansible/ansible.cfg"), message(
        en=f"result_format=yaml is active but comes from « {source} ».",
        fr=f"result_format=yaml est actif mais vient de « {source} ».",
    )


def test_dump_profile_tasks_active(host):
    """Le callback profile_tasks doit être réellement activé, pas juste écrit."""
    got = _dumped(host, "CALLBACKS_ENABLED")
    assert got, message(
        en="CALLBACKS_ENABLED absent from the dump: no callback is enabled.",
        fr="CALLBACKS_ENABLED absent du dump : aucun callback n'est activé.",
    )
    source, value = got
    assert "ansible.posix.profile_tasks" in value, message(
        en=f"profile_tasks is not among the active callbacks: {value}",
        fr=f"profile_tasks n'est pas dans les callbacks actifs : {value}",
    )
    assert source.endswith("labs/decouvrir/configuration-ansible/ansible.cfg"), message(
        en=f"The active callbacks come from « {source} », not the lab's cfg.",
        fr=f"Les callbacks actifs viennent de « {source} », pas du cfg du lab.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
