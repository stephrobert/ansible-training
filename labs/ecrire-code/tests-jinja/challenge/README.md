# 🎯 Challenge — Tests Jinja2 dans un fichier conditionnel

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** pose `/tmp/tests-jinja.txt`
contenant 4 lignes, chacune produite par un **test Jinja2** différent (`is
defined`, `is mapping`, `is sequence`, `is undefined`).

## 🧩 Données d'entrée

```yaml
user: { name: alice, age: 30 }
config:
  app: nginx
  port: 80
ports: [80, 443, 8080]
# optional_var n'est volontairement pas définie
```

## 🧩 Sortie attendue

```text
user_defined=yes
config_mapping=yes
ports_sequence=yes
optional_undefined=yes
```

Chaque ligne n'apparaît **que si** son test correspondant retourne vrai.

## 🧩 4 tests Jinja2 à utiliser

| Test | Vrai si… |
| --- | --- |
| `is defined` | la variable existe (par opposition à `is undefined`) |
| `is mapping` | la valeur est un dict (`{}`) |
| `is sequence` | la valeur est une liste (`[]`) ou un tuple |
| `is undefined` | la variable n'a jamais été définie |

> ⚠️ Différence **filtre** vs **test** : les **filtres** se mettent après `|`
> (`var | upper`), les **tests** après `is` (`var is defined`). N'inversez pas.

## 🧩 Squelette

```yaml
---
- name: Challenge - tests Jinja2
  hosts: db1.lab
  become: true

  vars:
    user: { name: alice, age: 30 }
    config:
      app: nginx
      port: 80
    ports: [80, 443, 8080]

  tasks:
    - name: Poser /tmp/tests-jinja.txt avec lignes conditionnelles
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          {% if ??? %}user_defined=yes
          {% endif %}
          {%- if ??? %}config_mapping=yes
          {% endif %}
          {%- if ??? %}ports_sequence=yes
          {% endif %}
          {%- if ??? %}optional_undefined=yes
          {% endif %}
```

> 💡 **Whitespace control** : les `{%- ... %}` (avec tiret en début) suppriment
> le whitespace avant la balise. C'est ce qui permet d'éviter une ligne vide
> entre chaque `{% if %}` … `{% endif %}`.

**Pièges** :

> - **Tests Jinja** : `is defined`, `is mapping`, `is sequence`, `is
>   string`, `is number`, `is divisibleby(N)`, `is even/odd`.
> - **`is mapping`** matche un **dict** (pas une liste). `is sequence`
>   matche une liste OU un tuple OU un range — mais aussi une **string**
>   (chaque caractère). Vérifier `is iterable` est plus large.
> - **`is defined`** vs **`is none`** : `defined` = la variable existe.
>   `is not none` = elle existe ET sa valeur n'est pas `null`.
> - **`is divisibleby`** : `42 is divisibleby 7` → `true`. Utile pour
>   itérations sélectives (chaque 5ᵉ élément, etc.).

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/tests-jinja/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/tests-jinja.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/tests-jinja/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/tests-jinja clean
```

## 💡 Pour aller plus loin

- **Tests numériques** : `is even`, `is odd`, `is divisibleby(N)`.
- **Tests string** : `is iterable`, `is string`, `is integer`, `is float`,
  `is boolean`.
- **`is failed` / `is changed` / `is succeeded`** sur un résultat `register:`
  — extrêmement utile dans les `when:`.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/tests-jinja/challenge/solution.yml
   ```
