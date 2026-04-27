"""Tests pytest+testinfra pour le challenge lab 14a — custom facts."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab14a-custom-facts.txt"
FACT_INI = "/etc/ansible/facts.d/lab14a.fact"
FACT_SCRIPT = "/etc/ansible/facts.d/lab14a-uptime.fact"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_facts_dir_exists(host):
    f = host.file("/etc/ansible/facts.d")
    assert f.is_directory, "/etc/ansible/facts.d/ doit être un dossier"


def test_static_fact_file_exists(host):
    f = host.file(FACT_INI)
    assert f.exists, f"{FACT_INI} absent"
    assert f.mode == 0o644, f"Le fact INI doit être en 0644 (statique), vu : {oct(f.mode)}"


def test_dynamic_fact_file_executable(host):
    f = host.file(FACT_SCRIPT)
    assert f.exists, f"{FACT_SCRIPT} absent"
    assert f.mode == 0o755, (
        f"Le script Bash doit être EXÉCUTABLE en 0755 (sinon Ansible le lit comme statique), "
        f"vu : {oct(f.mode)}"
    )


def test_proof_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, f"{RESULT_FILE} absent — solution.yml a-t-elle tourné ?"


def test_proof_file_mode(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644
    assert f.user == "root"


def test_proof_file_contains_static_fact_values(host):
    """Le fichier preuve contient les valeurs du fact INI."""
    content = host.file(RESULT_FILE).content_string
    assert "lab14a" in content, (
        f"Le fichier doit contenir 'lab14a' (project.name du fact statique), vu : {content[:200]}"
    )


def test_proof_file_contains_dynamic_fact_values(host):
    """Le fichier preuve contient une valeur du fact dynamique (kernel)."""
    content = host.file(RESULT_FILE).content_string
    # Le kernel d'AlmaLinux 10 commence typiquement par "5." ou "6."
    assert "kernel:" in content.lower() or "kernel " in content.lower(), (
        f"Le fichier doit contenir une référence au kernel (fact dynamique), vu : {content[:200]}"
    )


def test_proof_file_at_least_four_lines(host):
    """Au moins 4 lignes (project, version, owner, kernel)."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) >= 4, (
        f"Le fichier doit contenir ≥4 lignes (les 4 valeurs lues), vu : {len(lines)}"
    )
