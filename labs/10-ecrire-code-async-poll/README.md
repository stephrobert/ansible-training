# Async et poll — Tâches longues sans bloquer SSH

🔗 [**Async et poll Ansible : tâches longues, fire-and-forget, async_status**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/)

## 🌟 Objectif

1. Lancer une tâche **longue** (sleep 8 secondes) en mode `async + poll: 0`
2. Capturer le **job ID** via `register:`
3. Vérifier la fin avec **`async_status:`** + `until: ... finished`

## ⚙️ Exercice

Créez `playbook.yml` :

```yaml
---
- name: Démo async + async_status
  hosts: web1.lab
  become: true
  tasks:
    - name: Lancer un sleep long en background
      ansible.builtin.command: sleep 8
      async: 30
      poll: 0
      register: sleep_job

    - name: Attendre la fin du job async
      ansible.builtin.async_status:
        jid: "{{ sleep_job.ansible_job_id }}"
      register: job_result
      until: job_result.finished
      retries: 15
      delay: 2

    - name: Afficher le statut final
      ansible.builtin.debug:
        msg: "Job {{ sleep_job.ansible_job_id }} terminé en {{ job_result.delta }}"
```

Lancer et observer la fin propre.

## 🚀 Challenge

Voir `challenge/README.md`.
