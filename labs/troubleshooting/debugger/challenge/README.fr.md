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

## 🧩 Bloqué ?

```bash
dsoxlab hint troubleshooting-debugger
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

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
dsoxlab clean troubleshooting-debugger
```

## 💡 Pour aller plus loin

- Activer le débogueur **globalement** : `ANSIBLE_ENABLE_TASK_DEBUGGER=True ansible-playbook lab.yml`.
- `debugger: always` : ouvre le REPL **après chaque tâche** (lent, utile en TDD).
- **`ansible-lint`** : `ansible-lint --profile production challenge/solution.yml` doit retourner vert.
