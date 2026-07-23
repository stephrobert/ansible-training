def test_nginx_installe(host):
    assert host.package("nginx").is_installed
