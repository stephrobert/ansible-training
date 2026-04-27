"""
Valide que le playbook Ansible est idempotent et converge vers une seule
ligne « Servi par ... » dans index.html, indépendamment du nombre de runs.

Lancement depuis la racine du repo :
    pytest -v labs/decouvrir/declaratif-vs-imperatif/challenge/tests/
"""

import subprocess

from conftest import lab_host


def get_host():
    return lab_host("web1.lab")


def test_nginx_installed_and_running():
    host = get_host()
    assert host.package("nginx").is_installed
    nginx = host.service("nginx")
    assert nginx.is_enabled
    assert nginx.is_running


def test_firewalld_http_open():
    host = get_host()
    cmd = host.run("sudo firewall-cmd --list-services")
    assert "http" in cmd.stdout


def test_index_contains_exactly_one_servi_par_line():
    host = get_host()
    page = host.run("curl -s http://localhost/")
    occurrences = page.stdout.count("Servi par")
    assert occurrences == 1, (
        f"index.html doit contenir EXACTEMENT 1 ligne « Servi par » "
        f"(idempotence du playbook), trouvé : {occurrences}"
    )


def test_playbook_idempotent_second_run():
    """Relancer le playbook une 2e fois doit afficher changed=0."""
    result = subprocess.run(
        [
            "ansible-playbook",
            "labs/decouvrir/declaratif-vs-imperatif/playbook.yml",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    # Cherche la ligne PLAY RECAP avec changed=0 pour web1.lab
    recap = [line for line in result.stdout.splitlines() if "web1.lab" in line and "changed=" in line]
    assert recap, "Pas de ligne PLAY RECAP pour web1.lab"
    assert "changed=0" in recap[-1], (
        f"Le 2e run du playbook devrait avoir changed=0 (idempotence), "
        f"observé : {recap[-1]}"
    )
