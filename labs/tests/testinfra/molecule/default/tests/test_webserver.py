"""Tests testinfra du rôle webserver — exécutés DANS le container Molecule.

testinfra fournit une API Python expressive pour les assertions :
- host.package(name).is_installed
- host.service(name).is_running / is_enabled
- host.socket('tcp://...').is_listening
- host.file(path).exists / mode / content_string

Plus expressif que verify.yml Ansible — surtout pour des assertions complexes.
"""


def test_nginx_is_installed(host):
    """Vérifie que nginx est installé."""
    assert host.package("nginx").is_installed


def test_nginx_is_running_and_enabled(host):
    """Service nginx démarré et activé au boot."""
    nginx = host.service("nginx")
    assert nginx.is_running
    assert nginx.is_enabled


def test_nginx_listens_on_8080(host):
    """nginx écoute sur 8080 (override de webserver_listen_port)."""
    assert host.socket("tcp://0.0.0.0:8080").is_listening


def test_nginx_config_valid(host):
    """nginx -t renvoie OK (config syntaxiquement valide)."""
    cmd = host.run("nginx -t")
    assert cmd.rc == 0


def test_index_html_content(host):
    """Page d'accueil contient le custom message."""
    f = host.file("/usr/share/nginx/html/index.html")
    assert f.exists
    assert f.user == "root"  # ou "nginx" selon défaut
    assert "testinfra-tested" in f.content_string


def test_firewall_port_8080_open(host):
    """firewalld a 8080/tcp dans la zone publique."""
    cmd = host.run("firewall-cmd --zone=public --list-ports")
    # NB : dans un container minimaliste, firewalld peut être absent.
    # On skip si la commande retourne le bon message.
    if cmd.rc == 127:  # firewall-cmd not found
        return
    if cmd.rc == 0:
        assert "8080/tcp" in cmd.stdout
