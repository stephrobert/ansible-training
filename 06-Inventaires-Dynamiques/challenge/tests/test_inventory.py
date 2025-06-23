import json
import subprocess
import pytest


@pytest.fixture(scope="module")
def inventory():
    """Charge l'inventaire dynamique au format JSON"""
    result = subprocess.run(
        ["ansible-inventory", "--list"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )
    return json.loads(result.stdout)


def test_web01_not_in_inventory(inventory):
    """Vérifie que web01 n'est pas dans l'inventaire (car il est arrêté)"""
    all_hosts = inventory.get("_meta", {}).get("hostvars", {}).keys()
    assert "web01" not in all_hosts, "web01 ne devrait pas être listé (conteneur arrêté)"
