# Check mode et diff — Dry-run et visualisation

Bienvenue ! 🚀

🔗 [**Check mode et diff Ansible : dry-run et visualisation des changements**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/checkmode-diff/)

## 🌟 Objectif

1. Lancer un playbook en `--check` (dry-run) et vérifier qu'il **ne modifie rien**
2. Combiner `--check --diff` pour voir les diffs sans appliquer
3. Comprendre comment `check_mode: false` force une tâche à s'exécuter même en dry-run

## ⚙️ Exercice

Créez `playbook.yml` qui modifie `/etc/motd` sur web1 :

```yaml
---
- name: Modifier le MOTD
  hosts: web1.lab
  become: true
  tasks:
    - name: Poser un MOTD personnalisé
      ansible.builtin.copy:
        dest: /etc/motd
        content: "Bienvenue sur web1 — Ansible RHCE 2026\n"
        mode: "0644"
```

Lancer en dry-run avec affichage du diff :

```bash
ansible-playbook labs/08-ecrire-code-checkmode-diff/playbook.yml --check --diff
```

PLAY RECAP : `changed=1` MAIS `/etc/motd` n'est **pas** modifié côté web1.lab. C'est la magie du `--check`.

Pour appliquer pour de vrai :

```bash
ansible-playbook labs/08-ecrire-code-checkmode-diff/playbook.yml --diff
```

## 🚀 Challenge

Lire `challenge/README.md` pour le challenge complet.
