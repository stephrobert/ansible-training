# 🎯 Challenge — Migrate a standalone role to a collection with redirect

## ✅ Objective

Migrate a standalone role `legacy_role` (with a module `lab97_check`) to the collection `student.lab97_migrated`. Configure a **`plugin_routing.redirect`** that maintains backward compatibility, and **prove** that both names work.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab97-migration.txt` |
| Permissions | `0644`, owner `root` |
| Content | A line `legacy: lab97-migrated-OK` (call by the old name) **and** a line `new: lab97-migrated-OK` (call by the new FQCN) |
| Target collection | `student.lab97_migrated` (namespace `student`, name `lab97_migrated`) |
| Migrated module | `plugins/modules/lab97_check.py` |
| `plugin_routing` | redirect `lab97_status` → `student.lab97_migrated.lab97_check` |
| Deprecation warning | present at runtime |

> ⚠️ **The route starts from the OLD name.** The module was named `lab97_status`
> in the `library/` of the standalone role; it is named `lab97_check` in the
> collection. The key of `plugin_routing.modules` is the name to keep alive,
> the target is the real name. **Both must differ**: an entry
> `lab97_check: {redirect: student.lab97_migrated.lab97_check}` redirects
> to itself, and ansible-core rejects it at runtime with
> `plugin redirect loop resolving lab97_check`.
>
> No file `plugins/modules/lab97_status.py` must exist: if the old
> name responds, it is **the redirect** that resolved it, and nothing else. This is
> exactly what the tests check.

## 🧩 Hints

### Step 1 — Initialize the target collection

```bash
cd labs/collections/migration-role/challenge/
mkdir -p ansible_collections
ansible-galaxy collection init student.lab97_migrated --init-path ansible_collections/
```

### Step 2 — Create the migrated module

`ansible_collections/student/lab97_migrated/plugins/modules/lab97_check.py` (skeleton to complete with DOCUMENTATION + EXAMPLES + RETURN, see lab 95).

### Step 3 — Configure the `meta/runtime.yml`

```yaml
---
requires_ansible: ???

plugin_routing:
  modules:
    ???:                                         # ← the OLD name (the one from library/)
      redirect: ???                              # ← target FQCN (the new name)
      deprecation:
        removal_version: ???
        warning_text: ???
```

### Step 4 — `solution.yml` skeleton

```yaml
---
- hosts: ???
  become: ???
  tasks:
    - name: Test ancien nom, servi par la redirection (deprecation attendue)
      student.lab97_migrated.???:                # ← the old name, redirected
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

> 💡 **Pitfalls**:
>
> - **Role → collection migration**: `roles/<role>/` → `roles/<role>/`
>   in `ansible_collections/<ns>/<col>/`. Identical internal structure,
>   different external path.
> - **Role FQCN**: `<ns>.<col>.<role>`. E.g. `mycollection.webserver`.
>   Lets you have 2 `webserver` roles from different namespaces.
> - **`include_role:`** vs **`roles:`**: the 2nd syntax loads the role
>   at parsing, the 1st at runtime. For FQCN both work.
> - **`ansible-galaxy collection install`** of custom collections: may
>   require `-p` to point to the right `collections_path`.

## 🚀 Launch

```bash
cd labs/collections/migration-role/
ANSIBLE_COLLECTIONS_PATH=challenge/ansible_collections \
  ansible-playbook challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/migration-role/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean collections-migration-role
```

## 💡 Going further

- **`ANSIBLE_DEPRECATION_WARNINGS=False`** to test in CI without noise.
- **`ansible-lint --profile production`** must return green on the target collection.
- **Antsibull-changelog**: generate a `CHANGELOG.rst` that mentions the migration as `breaking_changes` (at the major bump).
