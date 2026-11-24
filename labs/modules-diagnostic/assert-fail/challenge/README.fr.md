# Arrêter le playbook avant qu'il n'abîme la mauvaise machine

## La situation

Le retour d'incident a été sans détour. Un playbook écrit pour la famille RHEL a
tourné sur un hôte qui n'en était pas, a échoué à mi-parcours, et a laissé le
système dans un état que personne ne savait décrire : à moitié configuré, à
moitié intact. Il ne vérifiait rien avant de démarrer. Celui-ci ne refera pas la
même erreur. Il est prévu pour **db1.lab**, pour une distribution récente de la
famille RHEL, sur une machine dotée d'assez de mémoire, et il doit **refuser de
s'exécuter** ailleurs plutôt que d'échouer en cours de route.

Votre mission :

1. Depuis **control-node.lab**, faire **refuser au play tout hôte autre que
   db1.lab**, avec un message qui dit pourquoi, vérifié **avant** toute autre
   exécution.
2. **Valider les prérequis** d'un seul bloc : une distribution de la famille
   RHEL, une version majeure supérieure ou égale à 9, et au moins 512 Mo de RAM.
3. Rendre l'échec **lisible** : un message personnalisé en cas d'échec, un autre
   en cas de succès, pour que le log raconte ce qui s'est passé au lieu de
   cracher un booléen brut.
4. Ne poser qu'**après** validation le marqueur qui prouve que l'hôte a passé le
   filtre.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-assert-fail/

## 🎯 Challenge — Validation défensive avec `assert:` + `fail:`

### ✅ Objectif

Sur **db1.lab**, écrire un play qui **valide les prérequis** avant d'écrire un
fichier marker `/tmp/lab-assert-validated.txt`. Les validations doivent :

1. Vérifier l'OS (AlmaLinux/RedHat/Rocky **uniquement**) — `assert:`.
2. Vérifier la version majeure ≥ 9 — `assert:`.
3. Vérifier qu'**au moins** 512Mo de RAM — `assert:`.
4. **Échouer explicitement** via `fail:` si l'inventory_hostname n'est pas
   `db1.lab` (le play est conçu uniquement pour db1).

### 🧩 Étapes

1. **`assert:`** avec 3 conditions et `fail_msg:` clair.
2. **`fail:`** avec `when:` sur `inventory_hostname != 'db1.lab'`.
3. **`copy: content:`** pour écrire `/tmp/lab-assert-validated.txt` après
   validation.

### 🧩 Squelette

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

### 🚀 Lancement

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lab-assert-validated.txt"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-diagnostic/assert-fail/challenge/tests/
```

### 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-assert-validated.txt state=absent"
```

### 💡 Pour aller plus loin

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
