# 🎯 Challenge — Migrer un rôle standalone vers une collection avec redirect

## ✅ Objectif

Migrer un rôle standalone `legacy_role` (avec un module `lab97_check`) vers la collection `student.lab97_migrated`. Configurer un **`plugin_routing.redirect`** qui maintient la rétrocompatibilité, et **prouver** que les deux noms fonctionnent.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab97-migration.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Une ligne `legacy: lab97-migrated-OK` (appel par l'ancien nom) **et** une ligne `new: lab97-migrated-OK` (appel par le nouveau FQCN) |
| Collection cible | `student.lab97_migrated` (namespace `student`, name `lab97_migrated`) |
| Module migré | `plugins/modules/lab97_check.py` |
| `plugin_routing` | redirect `lab97_status` → `student.lab97_migrated.lab97_check` |
| Deprecation warning | présent au runtime |

> ⚠️ **La route part de l'ANCIEN nom.** Le module s'appelait `lab97_status`
> dans le `library/` du rôle standalone ; il s'appelle `lab97_check` dans la
> collection. La clé de `plugin_routing.modules` est le nom à faire survivre,
> la cible est le nom réel. **Les deux doivent différer** : une entrée
> `lab97_check: {redirect: student.lab97_migrated.lab97_check}` se redirige
> vers elle-même, et ansible-core la rejette au runtime avec
> `plugin redirect loop resolving lab97_check`.
>
> Aucun fichier `plugins/modules/lab97_status.py` ne doit exister : si l'ancien
> nom répond, c'est **la redirection** qui l'a résolu, et rien d'autre. C'est
> exactement ce que les tests vérifient.

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
    ???:                                         # ← l'ANCIEN nom (celui du library/)
      redirect: ???                              # ← FQCN cible (le nouveau nom)
      deprecation:
        removal_version: ???
        warning_text: ???
```

### Étape 4 — Squelette `solution.yml`

```yaml
---
- hosts: ???
  become: ???
  tasks:
    - name: Test ancien nom, servi par la redirection (deprecation attendue)
      student.lab97_migrated.???:                # ← l'ancien nom, redirigé
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
dsoxlab clean collections-migration-role
```

## 💡 Pour aller plus loin

- **`ANSIBLE_DEPRECATION_WARNINGS=False`** pour tester en CI sans bruit.
- **`ansible-lint --profile production`** doit retourner vert sur la collection cible.
- **Antsibull-changelog** : générer un `CHANGELOG.rst` qui mentionne la migration comme `breaking_changes` (au bump majeur).
