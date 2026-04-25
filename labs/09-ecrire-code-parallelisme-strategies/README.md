# Parallélisme et stratégies — `serial:` rolling update

🔗 [**Parallélisme et stratégies Ansible : forks, serial, throttle, strategy**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/parallelisme-strategies/)

## 🌟 Objectif

1. Lancer un playbook avec `serial: 1` sur le groupe `webservers` (web1, web2)
2. Vérifier que les hôtes sont traités **séquentiellement** (timestamps croissants)

## ⚙️ Exercice

Créez `playbook.yml` :

```yaml
---
- name: Démo serial:1 sur webservers
  hosts: webservers
  serial: 1
  become: true
  tasks:
    - name: Poser un marqueur horodaté
      ansible.builtin.shell: |
        date --iso-8601=seconds > /tmp/serial-timestamp.txt
      changed_when: true
```

Lancer :

```bash
ansible-playbook labs/09-ecrire-code-parallelisme-strategies/playbook.yml
```

`serial: 1` impose le traitement séquentiel. Le timestamp posé sur web1 est
**antérieur** à celui de web2.

## 🚀 Challenge

Voir `challenge/README.md`.
