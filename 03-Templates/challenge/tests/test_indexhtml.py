import os

def test_template_contains_required_facts():
    template_path = os.path.join("templates", "index.html.j2")
    assert os.path.exists(template_path), "Le fichier index.html.j2 est manquant"

    with open(template_path) as f:
        content = f.read()
        assert "ansible_facts.hostname" in content
        assert "ansible_facts.distribution" in content
        assert "ansible_facts.distribution_version" in content
        assert "ansible_facts.uptime_seconds" in content
        assert "ansible_facts.memtotal_mb" in content
        assert "ansible_facts.processor_cores" in content
        assert "ansible_facts.processor[0]" in content