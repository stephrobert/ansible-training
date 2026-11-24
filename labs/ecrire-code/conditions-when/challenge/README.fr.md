# Un seul playbook, des hôtes qui ne se ressemblent pas

## La situation

Le playbook doit tourner sur tout le parc, et le parc n'est pas homogène :
certains hôtes sont de la famille RedHat, d'autres non, certains tournent sur
une version trop ancienne pour la fonctionnalité, et une option ne doit être
activée que là où l'équipe l'a explicitement demandée. Aujourd'hui, il existe
trois playbooks quasi identiques, copiés-collés les uns des autres. Ils ont
divergé le jour où quelqu'un a corrigé un bug dans exactement l'un d'eux. Vous
ramenez la logique à un seul play sur `db1.lab`, piloté par des conditions.

Votre mission :

1. Conditionner une tâche sur un **fact** : elle s'applique à la famille
   RedHat et se saute partout ailleurs.
2. **Combiner deux conditions** pour la tâche liée à la version : la bonne
   distribution et un numéro de version assez élevé.
3. Traiter un drapeau qui peut ne pas exister du tout : vérifier qu'il est
   **défini** avant de le lire, puis le convertir, car un drapeau passé en
   ligne de commande est une chaîne, pas un booléen, et il est vrai dans les
   deux cas.
4. Prouver que le saut est propre : la tâche Debian doit être **skippée, pas en
   échec**, et son fichier ne doit exister nulle part sur db1.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/conditions-when/

## 🎯 Challenge — Conditions `when` ciblées

### ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose **3 fichiers
conditionnels** et **n'en pose pas un 4ème** (preuve qu'un `when` faux skippe
proprement la tâche).

| Fichier à poser | Condition `when` | Contenu attendu |
| --- | --- | --- |
| `/tmp/cond-redhat.txt` | `ansible_os_family == "RedHat"` | `famille=redhat` |
| `/tmp/cond-alma9.txt` | `AlmaLinux` ET version ≥ 9 | `os=AlmaLinux9` |
| `/tmp/cond-feature.txt` | `enable_feature` est défini ET truthy | `feature=enabled` |

| Fichier à **NE PAS** poser | Condition `when` |
| --- | --- |
| `/tmp/cond-debian.txt` | `ansible_os_family == "Debian"` (faux sur AlmaLinux) |

### 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-conditions-when
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🧩 Squelette

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

    - name: cond-alma9 (AlmaLinux >= 9)
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

### 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/conditions-when/challenge/solution.yml \
    --extra-vars "enable_feature=true"
```

🔍 Sortie attendue : `ok=4, changed=3, skipped=1` (la tâche debian est
skippée).

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/conditions-when/challenge/tests/
```

> ⚠️ Le `conftest.py` racine joue automatiquement votre `solution.yml` avec
> `--extra-vars "enable_feature=true"` (cf. `_EXTRA_ARGS`).

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-conditions-when
```

### 💡 Pour aller plus loin

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
