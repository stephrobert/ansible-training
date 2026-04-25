# Délégation — `delegate_to` et `run_once`

🔗 [**Délégation Ansible : delegate_to, run_once, local_action**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/delegation/)

## 🌟 Objectif

1. Cibler les **webservers** dans le `hosts:` du play
2. Mais **rediriger** une tâche vers `db1.lab` via `delegate_to:`
3. Et l'exécuter **une seule fois** via `run_once: true`

## ⚙️ Exercice

Créez `playbook.yml` :

```yaml
---
- name: Démo delegate_to + run_once
  hosts: webservers
  become: true
  tasks:
    - name: Notifier la DB depuis chaque webserver (mais une seule fois)
      ansible.builtin.copy:
        dest: /tmp/delegated-from-webservers.txt
        content: "Notifié par {{ inventory_hostname }} à {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"
      delegate_to: db1.lab
      run_once: true
```

Le play boucle sur webservers, **mais** la tâche tourne sur db1 et **une
seule fois**. Le fichier sur db1 contient le hostname **du premier webserver
traité** (pas de db1).

## 🚀 Challenge

Voir `challenge/README.md`.
