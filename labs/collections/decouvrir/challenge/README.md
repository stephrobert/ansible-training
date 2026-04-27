# 🎯 Challenge — Inventaire des collections installées

## ✅ Objectif

Déposer sur `db1.lab` un fichier `/tmp/lab93-collections.txt` qui contient l'inventaire des collections installées avec leurs **versions** et leur **path**, généré dynamiquement par Ansible.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab93-collections.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Au moins 3 collections listées (`ansible.posix`, `community.general`, `kubernetes.core` ou autres présentes dans l'EE) |
| Format | Une collection par ligne, format `<FQCN_namespace.name> <version>` (ex: `community.general 10.5.0`) |
| Méthode | Utiliser `ansible.builtin.command` pour invoquer `ansible-galaxy collection list` puis `register:` + `copy` |

## 🧩 Indices

### Étape 1 — Capturer la liste avec `ansible-galaxy`

```yaml
- name: Lister les collections installées
  ansible.builtin.command: ???                # ← commande qui liste les collections
  register: ???
  changed_when: ???                            # ← lecture seule
```

### Étape 2 — Filtrer la sortie pour ne garder que les lignes utiles

La sortie brute contient des en-têtes (`Collection`, `-----`) qu'il faut filtrer. Vous pouvez :

- Soit utiliser `awk` / `grep` dans un shell (mais alors `ansible.builtin.shell`).
- Soit utiliser des **filtres Jinja2** Ansible (`split`, `select`, `reject`).

Squelette possible avec filtres Jinja2 :

```yaml
- name: Filtrer pour ne garder que les collections
  ansible.builtin.set_fact:
    collections_clean: "{{ collections_raw.stdout_lines
                            | reject('match', '^(#|Collection|---|$)')
                            | list }}"
```

### Étape 3 — Déposer le fichier

```yaml
- name: Déposer l'inventaire
  ansible.builtin.copy:
    dest: /tmp/lab93-collections.txt
    content: "???"                             # ← join les lignes
    owner: ???
    group: ???
    mode: ???
```

> 💡 **Pièges** :
>
> - **`ansible-galaxy collection list`** affiche TOUTES les collections
>   installées (control node), pas celles **utilisées** par un play.
>   Pour voir les collections utilisées : `ansible-doc -t module -l |
>   grep <namespace>`.
> - **FQCN obligatoire** depuis Ansible 2.10+ : `ansible.builtin.copy`,
>   pas juste `copy`. Le profil `ansible-lint production` le vérifie.
> - **`collections:`** au play-level : permet d'utiliser les modules sans
>   FQCN dans ce play. Pratique mais cache la dépendance — préférer FQCN.
> - **`~/.ansible/collections/`** : où vont les collections installées
>   par user. Pour install system-wide : `-p /usr/share/ansible/collections`.

## 🚀 Lancement

Depuis la racine du repo :

```bash
ansible-playbook labs/collections/decouvrir/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/decouvrir/challenge/tests/
```

Le test pytest+testinfra valide :

- `/tmp/lab93-collections.txt` existe avec mode `0644`, owner `root`.
- Au moins 3 lignes non vides.
- Au moins une ligne contient un FQCN avec un point (ex: `community.general`).

## 🧹 Reset

```bash
make -C labs/collections/decouvrir/ clean
```

## 💡 Pour aller plus loin

- **Lab 94** : `requirements.yml` pour reproduire l'environnement.
- **`ansible-galaxy collection list --format json`** : sortie scriptable pour intégration CI.
- **`ansible-lint --profile production`** : zéro warning attendu.
