# 🎯 Challenge — Fix d'une variable manquante via le débogueur

## ✅ Objectif

Écrire un playbook qui **échoue volontairement** sur une variable `target_dir` non définie, puis utiliser le **débogueur Ansible** pour **injecter la variable au runtime** (`task_vars['target_dir'] = '/tmp'`) et faire passer la tâche **sans modifier le YAML**.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab90-debug.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | "Debugger fix au runtime — lab 90 OK" |
| Mécanisme | `debugger: on_failed` activé sur la task qui copie |

> ⚠️ **Mode interactif** : ce challenge nécessite un terminal interactif.
> Pour la **validation pytest**, le `solution.yml` final doit avoir
> `target_dir` correctement défini en `vars:` (pas la version cassée
> avec débogueur — pytest tournera après votre fix).

## 🧩 Indices

### Étape 1 — Squelette `solution.yml`

```yaml
---
- name: Challenge 90 — debugger fix runtime
  hosts: ???
  become: ???
  gather_facts: false
  vars:
    target_dir: ???                 # ← après votre debug, fixer ici à /tmp

  tasks:
    - name: Déposer la preuve
      ansible.builtin.copy:
        dest: "{{ target_dir }}/lab90-debug.txt"
        content: "???"
        mode: ???
```

### Étape 2 — Workflow recommandé

1. **Phase 1 (debug interactif)** : commencer **sans** `vars: { target_dir: /tmp }`,
   activer `debugger: on_failed`, observer l'échec, injecter au runtime via
   `task_vars['target_dir'] = '/tmp'` + `update_task` + `redo`.

2. **Phase 2 (fix permanent)** : une fois la cause comprise, **éditer le YAML**
   pour définir `vars: { target_dir: /tmp }` proprement et **retirer**
   `debugger: on_failed` (qui n'a pas sa place en code de prod).

### Étape 3 — Commandes du REPL

| Commande | Effet |
| --- | --- |
| `p task_vars['target_dir']` | inspecte (devrait dire `undefined`) |
| `task_vars['target_dir'] = '/tmp'` | injecte la variable |
| `update_task` ou `u` | recrée la tâche avec les nouvelles vars |
| `redo` ou `r` | rejoue la tâche |
| `continue` ou `c` | passe à la suivante |
| `quit` ou `q` | abandonne |

> 💡 **Pièges** :
>
> - **`debugger: on_failed`** déclenche le debug interactif **seulement
>   si** la tâche échoue. Pour debug même en succès : `debugger:
>   always`.
> - **Niveau task vs play** : `debugger:` peut être au play-level (toutes
>   les tâches) ou task-level (cette tâche seulement). Préférer
>   task-level — moins intrusif.
> - **REPL bloqué en CI** : `debugger:` ne fonctionne **que** dans un
>   terminal interactif (TTY). En CI/cron, désactiver via
>   `ANSIBLE_DEBUGGER_IGNORE_ERRORS=true` ou supprimer la directive.
> - **Variables modifiées via `task_vars[...]`** ne persistent pas
>   au-delà de la tâche. Pour persister : `set_fact` dans une tâche
>   suivante.

## 🚀 Lancement

Depuis la racine du repo :

```bash
ansible-playbook labs/troubleshooting/debugger/challenge/solution.yml
```

(la version finale **avec** `vars: { target_dir: /tmp }`, sans débogueur).

## 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/debugger/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/troubleshooting/debugger/ clean
```

## 💡 Pour aller plus loin

- Activer le débogueur **globalement** : `ANSIBLE_ENABLE_TASK_DEBUGGER=True ansible-playbook lab.yml`.
- `debugger: always` : ouvre le REPL **après chaque tâche** (lent, utile en TDD).
- **`ansible-lint`** : `ansible-lint --profile production challenge/solution.yml` doit retourner vert.
