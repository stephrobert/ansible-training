"""Tests pytest+testinfra pour le challenge lab 14a — custom facts."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab14a-custom-facts.txt"
FACT_INI = "/etc/ansible/facts.d/lab14a.fact"
FACT_SCRIPT = "/etc/ansible/facts.d/lab14a-uptime.fact"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_facts_dir_exists(host):
    f = host.file("/etc/ansible/facts.d")
    assert f.is_directory, message(
        en="/etc/ansible/facts.d/ must be a directory",
        fr="/etc/ansible/facts.d/ doit être un dossier",
    )


def test_static_fact_file_exists(host):
    f = host.file(FACT_INI)
    assert f.exists, message(
        en=f"{FACT_INI} missing",
        fr=f"{FACT_INI} absent",
    )
    assert f.mode == 0o644, message(
        en=f"The INI fact must be 0644 (static), seen: {oct(f.mode)}",
        fr=f"Le fact INI doit être en 0644 (statique), vu : {oct(f.mode)}",
    )


def test_dynamic_fact_file_executable(host):
    f = host.file(FACT_SCRIPT)
    assert f.exists, message(
        en=f"{FACT_SCRIPT} missing",
        fr=f"{FACT_SCRIPT} absent",
    )
    assert f.mode == 0o755, message(
        en=f"The Bash script must be EXECUTABLE, 0755 (otherwise Ansible reads it "
        f"as a static file), seen: {oct(f.mode)}",
        fr=f"Le script Bash doit être EXÉCUTABLE en 0755 (sinon Ansible le lit comme statique), "
        f"vu : {oct(f.mode)}",
    )


def test_proof_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, message(
        en=f"{RESULT_FILE} missing: did solution.yml run?",
        fr=f"{RESULT_FILE} absent — solution.yml a-t-elle tourné ?",
    )


def test_proof_file_mode(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, message(
        en=f"The proof file is {oct(f.mode)}, expected 0644.",
        fr=f"Le fichier de preuve est en {oct(f.mode)}, attendu 0644.",
    )
    assert f.user == "root", message(
        en=f"The proof file belongs to {f.user}, expected root.",
        fr=f"Le fichier de preuve appartient à {f.user}, attendu root.",
    )


def test_proof_file_contains_static_fact_values(host):
    """Le fichier preuve contient les valeurs du fact INI."""
    content = host.file(RESULT_FILE).content_string
    assert "lab14a" in content, message(
        en=f"The file must contain 'lab14a' (project.name of the static fact), seen: {content[:200]}",
        fr=f"Le fichier doit contenir 'lab14a' (project.name du fact statique), vu : {content[:200]}",
    )


def test_proof_file_contains_dynamic_fact_values(host):
    """Le fichier preuve contient une valeur du fact dynamique (kernel)."""
    content = host.file(RESULT_FILE).content_string
    # Le kernel d'AlmaLinux 9 commence typiquement par "5." ou "6."
    assert "kernel:" in content.lower() or "kernel " in content.lower(), message(
        en=f"The file must contain a reference to the kernel (the dynamic fact), seen: {content[:200]}",
        fr=f"Le fichier doit contenir une référence au kernel (fact dynamique), vu : {content[:200]}",
    )


def test_proof_file_at_least_four_lines(host):
    """Au moins 4 lignes (project, version, owner, kernel)."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) >= 4, message(
        en=f"The file must contain at least 4 lines (the 4 values read), seen: {len(lines)}",
        fr=f"Le fichier doit contenir ≥4 lignes (les 4 valeurs lues), vu : {len(lines)}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
