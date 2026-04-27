# 🎯 Challenge — Migrer un rôle standalone vers une collection avec redirect

## ✅ Objectif

Migrer un rôle standalone `legacy_role` (avec un module `lab97_check`) vers la collection `student.lab97_migrated`. Configurer un **`plugin_routing.redirect`** qui maintient la rétrocompatibilité, et **prouver** que les deux noms fonctionnent.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab97-migration.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Doit contenir `lab97-migrated-OK` (résultat du nouveau FQCN) |
| Collection cible | `student.lab97_migrated` (namespace `student`, name `lab97_migrated`) |
| Module migré | `plugins/modules/lab97_check.py` |
| `plugin_routing` | redirect `lab97_check` → `student.lab97_migrated.lab97_check` |
| Deprecation warning | présent au runtime |

## 🧩 Indices

### Étape 1 — Initialiser la collection cible

```bash
cd labs/collections/migration-role/challenge/
mkdir -p ansible_collections
ansible-galaxy collection init student.lab97_migrated --init-path ansible_collections/
```

### Étape 2 — Créer le module migré

`ansible_collections/student/lab97_migrated/plugins/modules/lab97_check.py` (squelette à compléter avec DOCUMENTATION + EXAMPLES + RETURN, voir lab 95).

### Étape 3 — Configurer le `meta/runtime.yml`

```yaml
---
requires_ansible: ???

plugin_routing:
  modules:
    lab97_check:
      redirect: ???                              # ← FQCN cible
      deprecation:
        removal_version: ???
        warning_text: ???
```

### Étape 4 — Squelette `solution.yml`

```yaml
---
- hosts: ???
  become: ???
  collections:
    - student.lab97_migrated                     # ← déclare la collection (rétro-compat)
  tasks:
    - name: Test ancien nom court (avec deprecation)
      lab97_check:
      register: ???

    - name: Test nouveau FQCN explicite
      student.lab97_migrated.lab97_check:
      register: ???

    - name: Déposer la preuve
      ansible.builtin.copy:
        dest: ???
        content: |
          legacy: {{ ???.msg }}
          new: {{ ???.msg }}
        mode: ???
```

> 💡 **Pièges** :
>
> - **Migration rôle → collection** : `roles/<role>/` → `roles/<role>/`
>   dans `ansible_collections/<ns>/<col>/`. Structure interne identique,
>   chemin externe différent.
> - **FQCN du rôle** : `<ns>.<col>.<role>`. Ex `mycollection.webserver`.
>   Permet d'avoir 2 rôles `webserver` de namespaces différents.
> - **`include_role:`** vs **`roles:`** : la 2ᵉ syntaxe charge le rôle
>   au parsing, la 1ᵉ au runtime. Pour FQCN les deux marchent.
> - **`ansible-galaxy collection install`** des collections custom : peut
>   nécessiter `-p` pour pointer le bon `collections_path`.

## 🚀 Lancement

```bash
cd labs/collections/migration-role/
ANSIBLE_COLLECTIONS_PATH=challenge/ansible_collections \
  ansible-playbook challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/migration-role/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/collections/migration-role/ clean
```

## 💡 Pour aller plus loin

- **`ANSIBLE_DEPRECATION_WARNINGS=False`** pour tester en CI sans bruit.
- **`ansible-lint --profile production`** doit retourner vert sur la collection cible.
- **Antsibull-changelog** : générer un `CHANGELOG.rst` qui mentionne la migration comme `breaking_changes` (au bump majeur).
