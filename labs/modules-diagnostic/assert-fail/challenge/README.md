# 🎯 Challenge — Validation défensive avec `assert:` + `fail:`

## ✅ Objectif

Sur **db1.lab**, écrire un play qui **valide les prérequis** avant d'écrire un
fichier marker `/tmp/lab-assert-validated.txt`. Les validations doivent :

1. Vérifier l'OS (AlmaLinux/RedHat/Rocky **uniquement**) — `assert:`.
2. Vérifier la version majeure ≥ 9 — `assert:`.
3. Vérifier qu'**au moins** 512Mo de RAM — `assert:`.
4. **Échouer explicitement** via `fail:` si l'inventory_hostname n'est pas
   `db1.lab` (le play est conçu uniquement pour db1).

## 🧩 Étapes

1. **`assert:`** avec 3 conditions et `fail_msg:` clair.
2. **`fail:`** avec `when:` sur `inventory_hostname != 'db1.lab'`.
3. **`copy: content:`** pour écrire `/tmp/lab-assert-validated.txt` après
   validation.

## 🧩 Squelette

```yaml
---
- name: Challenge - assert + fail validation
  hosts: db1.lab
  become: true

  pre_tasks:
    - name: Refuser tout host autre que db1.lab
      ansible.builtin.fail:
        msg: ???
      when: ???

    - name: Valider OS + version + memoire
      ansible.builtin.assert:
        that:
          - ???
          - ???
          - ???
        fail_msg: ???
        success_msg: ???

  tasks:
    - name: Marker - validation OK
      ansible.builtin.copy:
        content: |
          Validations OK
          OS : {{ ansible_distribution }} {{ ansible_distribution_version }}
          Memoire : {{ ansible_memtotal_mb }} Mo
        dest: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`assert:`** = pré-condition. Si fausse, le play s'arrête (failed).
>   Pour avertir sans bloquer : `assert:` + `ignore_errors: true` (mais
>   pas idiomatique — préférer `fail:` conditionnel).
> - **`that:`** = liste de conditions. **Toutes** doivent être vraies.
>   Format : strings ou listes. Pour OR : `or` Jinja dans une string.
> - **`fail:` + `when:`** : alternative à `assert:`. Plus flexible si la
>   condition vient d'un `register` complexe.
> - **`success_msg`** vs **`fail_msg`** : message custom selon le résultat.
>   Améliore énormément la lisibilité du log.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lab-assert-validated.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-diagnostic/assert-fail/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-assert-validated.txt state=absent"
```

## 💡 Pour aller plus loin

- **`pre_tasks:` vs `tasks:`** : les `pre_tasks:` tournent **avant** tout
  rôle inclus, utile pour valider les prérequis avant que les rôles importent.
- **`quiet: true`** : silence les `assert:` qui passent (utile sur 50+ assertions).
- **`force_handlers: true`** : déclencher les handlers même en cas de
  `assert: failed` (rare mais utile pour notifier d'un échec de précondition).
- **Pattern `set_fact +  assert`** : calculer une valeur, l'asserter ensuite.
- **Lint** :

   ```bash
   ansible-lint labs/modules-diagnostic/assert-fail/challenge/solution.yml
   ```
