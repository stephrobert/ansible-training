# 🎯 Challenge — Conditions `when` ciblées

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose **3 fichiers
conditionnels** et **n'en pose pas un 4ème** (preuve qu'un `when` faux skippe
proprement la tâche).

| Fichier à poser | Condition `when` | Contenu attendu |
| --- | --- | --- |
| `/tmp/cond-redhat.txt` | `ansible_os_family == "RedHat"` | `famille=redhat` |
| `/tmp/cond-alma10.txt` | `AlmaLinux` ET version ≥ 10 | `os=AlmaLinux10` |
| `/tmp/cond-feature.txt` | `enable_feature` est défini ET truthy | `feature=enabled` |

| Fichier à **NE PAS** poser | Condition `when` |
| --- | --- |
| `/tmp/cond-debian.txt` | `ansible_os_family == "Debian"` (faux sur AlmaLinux) |

## 🧩 Indices

- Activez `gather_facts: true` au niveau du play (sinon `ansible_os_family`
  n'existe pas).
- `when:` accepte une **chaîne** (une seule condition) ou une **liste**
  (toutes ANDées) :

  ```yaml
  when:
    - condition_1
    - condition_2
  ```

- Pour `cond-feature`, vous avez besoin de **2 vérifications** :
  1. `enable_feature is defined` (sinon erreur de variable indéfinie)
  2. `enable_feature | bool` (force la conversion en booléen)

## 🧩 Squelette

```yaml
---
- name: Challenge - conditions when
  hosts: db1.lab
  become: true
  gather_facts: true

  tasks:
    - name: cond-redhat (uniquement si famille RedHat)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when: ???

    - name: cond-alma10 (AlmaLinux >= 10)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when:
        - ???
        - ???

    - name: cond-feature (extra-vars enable_feature=true)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when:
        - ???
        - ???

    - name: cond-debian (ne sera PAS exécuté sur AlmaLinux)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when: ???
```

> 💡 **Pièges** :
>
> - **`when:` accepte une expression Jinja2 sans `{{ }}`** : écrire
>   `when: my_var == "x"` directement, **pas** `when: "{{ my_var == 'x' }}"`.
> - **Bool depuis `--extra-vars`** : `enable_feature=true` est une
>   **string**. Comparer avec `enable_feature | bool` ou
>   `enable_feature == "true"`.
> - **`when:` sur loop** : la condition s'évalue **par item** (loop
>   filtré). Pour skipper toute la loop, utiliser `when:` sur la tâche
>   parent + `block:`.
> - **`is defined`** vs **`is not none`** : `defined` teste la présence
>   de la variable, `not none` teste sa valeur. Différence subtile mais
>   importante.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/conditions-when/challenge/solution.yml \
    --extra-vars "enable_feature=true"
```

🔍 Sortie attendue : `ok=4, changed=3, skipped=1` (la tâche debian est
skippée).

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/conditions-when/challenge/tests/
```

> ⚠️ Le `conftest.py` racine joue automatiquement votre `solution.yml` avec
> `--extra-vars "enable_feature=true"` (cf. `_EXTRA_ARGS`).

## 🧹 Reset

```bash
make -C labs/ecrire-code/conditions-when clean
```

## 💡 Pour aller plus loin

- **`when:` sur un `block:`** : applique la condition à toutes les tâches du
  block. DRY quand on a 5 tâches qui partagent la même condition.
- **`is search` / `is match`** : tests Jinja2 pour conditions sur des regex
  (ex : `when: ansible_kernel is search('rhel|alma')`).
- **`failed_when` / `changed_when`** : conditions qui modifient l'**état** de
  la tâche (lab 23).
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/conditions-when/challenge/solution.yml
   ```
