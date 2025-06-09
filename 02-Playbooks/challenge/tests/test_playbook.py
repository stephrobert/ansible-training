import os
import pytest
import testinfra

def test_file_exists(host):
    f = host.file("/tmp/config_ansible.txt")
    assert f.exists
    assert f.is_file

def test_file_content(host):
    f = host.file("/tmp/config_ansible.txt")
    content = f.content_string
    assert "# BEGIN ANSIBLE MANAGED BLOCK" in content
    assert "param1 = valeur1" in content
    assert "param2 = valeur2" in content
    assert "# END ANSIBLE MANAGED BLOCK" in content

def test_file_permissions_and_owner(host):
    f = host.file("/tmp/config_ansible.txt")
    current_user = os.getenv("USER") or host.user().name
    assert f.user == current_user
    assert f.group == current_user
    assert f.mode == 0o600
