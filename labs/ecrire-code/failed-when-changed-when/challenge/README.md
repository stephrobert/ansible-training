# 🎯 Challenge — Mapper un code retour à la sémantique Ansible

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** fait passer une commande
retournant **rc=1** (donc *échec* par défaut Ansible) pour un succès — mais
marquée comme `changed`.

Pourquoi ? Certaines commandes utilisent rc=1 comme **signal métier** (`grep`
qui ne trouve rien, `diff` qui détecte des différences, etc.). Sans
`failed_when`, le play s'arrêterait à tort.

## 🧩 Sémantique attendue

| Code retour | Sémantique Ansible souhaitée |
| --- | --- |
| `rc=0` | `ok` (rien à faire) |
| `rc=1` | `changed` (modification métier détectée — pas un échec) |
| `rc=2,3,…` | `failed` (vraie erreur) |

## 🧩 Mots-clés à combiner

- **`register: result`** : capture le résultat (notamment `result.rc`).
- **`failed_when:`** : redéfinit ce qui est considéré comme un échec.
- **`changed_when:`** : redéfinit ce qui est considéré comme un changement.

```yaml
- name: ...
  ansible.builtin.command: ???
  register: result
  failed_when: result.rc not in [???]    # liste des rc considérés OK
  changed_when: result.rc == ???          # quel rc déclenche "changed"
```

## 🧩 Squelette

```yaml
---
- name: Challenge - failed_when et changed_when
  hosts: db1.lab
  become: true

  tasks:
    - name: Commande qui retourne rc=1
      ansible.builtin.command: /bin/sh -c 'exit 1'
      register: result
      failed_when: ???
      changed_when: ???

    - name: Marqueur (atteint = preuve que la 1ère tâche n'a pas planté)
      ansible.builtin.copy:
        dest: /tmp/failed-when-result.txt
        content: "rc={{ result.rc }} ok=changed\n"
        mode: "0644"
```

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/failed-when-changed-when/challenge/solution.yml
```

🔍 **Sortie attendue** :

- 1ère tâche : `changed` (non `failed`).
- 2ème tâche : `changed` (le fichier est posé).
- `PLAY RECAP` : `changed=2, failed=0`.

> 💡 **Pièges** :
>
> - **`failed_when:`** redéfinit la condition d'échec. Par défaut, une
>   tâche échoue si `rc != 0`. Avec `failed_when: result.rc not in [0, 2]`,
>   les codes 0 et 2 sont OK.
> - **`changed_when:`** redéfinit la condition `changed`. Sans, une
>   `command:` ou `shell:` est **toujours** marquée `changed=1` (anti-
>   idempotence). Pour une lecture-seule : `changed_when: false`.
> - **`changed_when:` + `failed_when:` ensemble** : `failed_when` est
>   évalué en premier ; si la tâche échoue, `changed_when` n'est pas
>   évalué.
> - **Boolean expression** : `failed_when: result.stdout != ""` (string
>   non vide), `failed_when: "'ERROR' in result.stderr"` (substring).

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/failed-when-changed-when/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/failed-when-changed-when clean
```

## 💡 Pour aller plus loin

- **`failed_when: result.stderr`** : on échoue si stderr est non vide
  (utile pour des commandes qui retournent rc=0 mais écrivent un warning
  bloquant en stderr).
- **`changed_when: '"already exists" not in result.stdout'`** : on n'est
  changed que si la sortie n'indique pas que la chose existe déjà
  (équivalent d'un `creates:` mais via parsing de stdout).
- **Différence avec `block/rescue`** : `failed_when`/`changed_when`
  réinterprètent **une** tâche. `block/rescue` orchestre **plusieurs**
  tâches autour d'un échec.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/failed-when-changed-when/challenge/solution.yml
   ```
