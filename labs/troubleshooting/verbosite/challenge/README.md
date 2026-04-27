# 🎯 Challenge — Profiler 3 tâches sur `db1.lab`

## ✅ Objectif

Écrire un playbook qui exécute **3 tâches mesurables** sur `db1.lab`, activer le callback `profile_tasks`, et déposer un fichier `/tmp/lab89-profile.txt` qui contient les **noms** des 3 tâches dans l'ordre où elles ont été exécutées.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab89-profile.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Les 3 noms de tâches séparés par `\n` (un par ligne) |
| Callbacks activés | `ansible.posix.profile_tasks` (visible dans la sortie) |

## 🧩 Indices

### Étape 1 — Créer `ansible.cfg` au niveau du lab

```ini
[defaults]
stdout_callback = ???
callbacks_enabled = ansible.posix.profile_tasks, ???

[callback_profile_tasks]
task_output_limit = ???
```

### Étape 2 — Squelette de `solution.yml`

```yaml
---
- name: Challenge 89 — profile 3 tâches
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: ???                                   # tâche 1
      ansible.builtin.shell: sleep 1
      changed_when: false

    - name: ???                                   # tâche 2
      ansible.builtin.shell: ???
      changed_when: false

    - name: ???                                   # tâche 3 : dépose le fichier preuve
      ansible.builtin.copy:
        dest: /tmp/lab89-profile.txt
        content: |
          ???
          ???
          ???
        owner: ???
        group: ???
        mode: ???
```

### Étape 3 — Activer le profile via `ANSIBLE_CONFIG`

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

> 💡 **Pièges** :
>
> - **`-v` à `-vvvv`** : 4 niveaux. `-v` = recap par hôte ; `-vv` = +
>   variables ; `-vvv` = + commands SSH ; `-vvvv` = + connection
>   establishment.
> - **`ANSIBLE_DEBUG=1`** : output massif (debug interne Ansible). À
>   utiliser **uniquement** quand `-vvvv` ne suffit pas.
> - **Callback plugins** : `yaml`, `default`, `unixy`, `dense`, `null`,
>   `oneline`, `selective`. Définir dans `ansible.cfg` via
>   `stdout_callback = yaml`.
> - **`no_log: true`** masque la sortie même en `-vvvv` — protection des
>   secrets. À garder en prod.

## 🚀 Lancement

Depuis la racine du repo :

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/verbosite/challenge/tests/
```

Le test pytest+testinfra valide :

- `/tmp/lab89-profile.txt` existe sur `db1.lab` avec mode `0644`.
- Le fichier contient **exactement 3 lignes** non vides (les 3 noms de tâches).

## 🧹 Reset

```bash
make -C labs/troubleshooting/verbosite/ clean
```

## 💡 Pour aller plus loin

- **Plusieurs callbacks combinés** : ajouter `ansible.posix.timer` pour le temps total.
- **Capture de timing** : rediriger la sortie `ansible-playbook` vers un fichier, parser avec `grep -E 'TASK execution time'`.
- **`ansible-lint`** : `ansible-lint --profile production challenge/solution.yml` doit retourner vert.
