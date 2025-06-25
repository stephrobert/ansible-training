# 13 – TP Tâches Asynchrones Ansible : gagnez en performance

Bienvenue dans le treizième TP de la formation Ansible ! Vous allez apprendre à
utiliser les **tâches asynchrones et le suivi d’état** pour exécuter des
opérations longues de façon parallèle et sans blocage.
Basé sur le guide "Les tâches asynchrones sous Ansible" de Stéphane Robert

---

## 🧠 Lecture recommandée

Avant de commencer, lisez ce chapitre :
[Les tâches asynchrones Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/taches-asynchrones/)

Vous y découvrirez :

- Pourquoi passer en mode async (gain de temps, non bloquant)
- L’utilisation d’options `async` et `poll`
- Suivi avec `async_status`
- Gestion de la concurrence via `throttle`
- Différences entre `forks` et `throttle`
- Exécution parallèle dans les playbooks

---

## 🎯 Objectifs du TP

1. Lancer une commande longue en mode asynchrone (Ad-hoc)
2. Suivre l’état de la tâche avec `async_status`
3. Implémenter une tâche async dans un playbook
4. Attendre la fin de la tâche avant de poursuivre
5. Contrôler le parallélisme avec `throttle` en playbook
6. Comparer `forks` et `throttle`
7. Regrouper plusieurs tâches async avec `async_status`
8. Protéger contre les échecs / gérer le timeout
9. Mesurer le temps gagné
10. Appliquer les bonnes pratiques et valider

---

## 🛠️ Étapes

### Étape 0 : Prérequis

Assurez-vous de disposer d'une machine cible Ansible. Pour simplifier, utilisez
un conteneur Incus avec Ubuntu :

```bash
incus launch images:ubuntu/24.04/cloud host1 --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:ubuntu/24.04/cloud host2 --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:ubuntu/24.04/cloud host3 --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

### Etape 1 – Exécution asynchrone en ad-hoc

Dans le terminal :

```bash
ansible all -B 3600 -P 0 -a "sleep 600" -i host1, -c community.general.incus
```

Cette commande s'exécute  en arrière-plan sur l’hôte local, sans
attendre la fin (`-P 0`).

---

### Etape 2 – Suivi de la tâche async

Dans la tâche précédente, récupérez l’`ansible_job_id` retourné, puis :

```bash
ansible all -m async_status -a "jid=<JOB_ID>" -P 5 -i host1, -c community.general.incus
```

Vérifiez les statuts `running`, `finished`.

---

### Etape 3 – Async dans un playbook

Créez un playbook `async_playbook.yml` avec une tâche qui exécute une commande
longue en mode asynchrone. Utilisez `async` et `poll: 0` pour ne pas bloquer.

```yaml
- name: Exécution asynchrone dans un playbook
  hosts: all
  connection: community.general.incus
  gather_facts: false
  tasks:
    - name: Tâche longue en arrière-plan
      ansible.builtin.shell: sleep 30
      async: 600
      poll: 0
      register: job
```

Lancez le playbook avec :

```bash
ansible-playbook async_playbook.yml
```

Normalement, il ne bloque pas et retourne immédiatement. La tâche
s'exécute en arrière-plan.

---

### Etape 4 – Attendre la tâche

Ajoutez une tâche `async_status` avec `until: job.finished` et `retries` pour
attendre sa fin.

```yaml
- name: Attendre la fin de la tâche asynchrone
  ansible.builtin.async_status:
    jid: "{{ job.ansible_job_id }}"
  register: job_status
  until: job_status.finished
  retries: 30
  delay: 10
```

Cette fois le playbook attendra la fin de la tâche avant de continuer.

---

### Etape 5 – Contrôler le parallélisme avec `throttle`

Ajoutez `throttle: 2` sur la tâche async pour limiter à 2 hôtes en même temps.

```yaml
- name: Exécution asynchrone dans un playbook
  hosts: all
  connection: community.general.incus
  gather_facts: false
  tasks:
    - name: Tâche longue en arrière-plan
      ansible.builtin.shell: sleep 30
      async: 600
      poll: 0
      register: job
      throttle: 2

    - name: Attendre la fin de la tâche asynchrone
      ansible.builtin.async_status:
        jid: "{{ job.ansible_job_id }}"
      register: job_status
      until: job_status.finished
      retries: 30
      delay: 10
```

Lancez le playbook et observez que seules 2 tâches s'exécutent en même temps.

---

### Etape 6 – Comparer avec `forks`

Retirez `throttle` et lancez le playbook avec `ANSIBLE_FORKS=2` pour
comparer le comportement. Notez que `forks` contrôle le nombre de tâches
concurrentes à l'échelle du playbook, tandis que `throttle` s'applique
à une tâche spécifique.

---

### Etape 7 – Gérer le timeout et les échecs

Testez un `sleep 100` avec `async: 10`, `poll: 0`. Vérifiez que la tâche échoue
après 10 s.

Ajoutez `failed_when: job.rc != 0` pour gérer explicitement.

---

## 🧩 Challenge à valider

Voir `challenge/README.md`

---

## ✅ Compétences acquises

* Lancement de tâches async en ad-hoc et playbook
* Suivi avec `async_status`
* Contrôle de la concurrence (`throttle`)
* Gestion des échecs/timings
* Optimisation des déploiements en non-blocking
