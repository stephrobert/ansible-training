# 🎯 Challenge — Précédence : `--extra-vars` gagne sur tout

## ✅ Objectif

Démontrer que **`--extra-vars` (niveau 22)** est plus fort que **`vars:` du
play (niveau 14)** et que **`vars_files:` (niveau 13)**.

Vous allez créer la **même variable `winner`** à 3 endroits différents, puis
lancer le play avec `--extra-vars` et observer quelle valeur **gagne**.

## 🧩 Fichiers à créer

### 1) `challenge/vars/loader.yml`

```yaml
---
winner: "vars_files"
```

### 2) `challenge/solution.yml`

Squelette à compléter :

```yaml
---
- name: Challenge - precedence des variables
  hosts: ???
  become: ???

  vars:
    winner: "play_vars"               # niveau 14

  vars_files:
    - ???                             # vars/loader.yml — niveau 13

  tasks:
    - name: Poser /tmp/precedence-result.txt avec la valeur résolue
      ansible.builtin.copy:
        dest: ???
        content: "winner={{ ??? }}\n"
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Niveau 22 = top du top** : `--extra-vars` gagne sur **toutes** les
>   autres sources (vars:, vars_files:, group_vars, host_vars,
>   set_fact…). C'est ce qui rend les paramètres CLI parfaits pour un
>   override ponctuel sans toucher au code.
> - **Le test attend `extra_vars_wins`** comme valeur. Le conftest passe
>   `--extra-vars "winner=extra_vars_wins"` automatiquement. Si vous
>   lancez sans, vous obtenez `play_vars` (la valeur du `vars:`).
> - **`vars_files:` est plus faible que `vars:` du play** dans Ansible
>   moderne — exactement l'inverse de l'intuition naïve. À mémoriser pour
>   l'EX294.

## 🚀 Lancement (avec --extra-vars)

```bash
ansible-playbook labs/ecrire-code/precedence-variables/challenge/solution.yml \
    --extra-vars "winner=extra_vars_wins"
```

🔍 Vérifiez :

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/precedence-result.txt"
# Doit afficher : winner=extra_vars_wins
```

`--extra-vars` (niveau 22) **écrase** à la fois `vars:` du play (14) et
`vars_files:` (13).

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/precedence-variables/challenge/tests/
```

> ⚠️ Le `conftest.py` racine joue automatiquement votre `solution.yml` avec
> `--extra-vars "winner=extra_vars_wins"` (cf. `_EXTRA_ARGS`).

## 🧹 Reset

```bash
make -C labs/ecrire-code/precedence-variables clean
```

## 💡 Pour aller plus loin

- **Sans `--extra-vars`** : relancez sans le flag. Quelle valeur gagne entre
  `play_vars` et `vars_files` ? Ansible récents : **`vars:` du play gagne**
  sur `vars_files:`. Cf. la table de précédence officielle de la doc.
- **`set_fact`** : niveau 18 (au-dessus de `vars:` mais sous `--extra-vars`).
  Posez un `set_fact: winner: "set_fact_wins"` dans une tâche **avant** la
  tâche qui pose le fichier, et observez.
- **`include_vars`** vs `vars_files:` : `include_vars` est niveau 19 (plus haut
  que `set_fact`). C'est **plus fort** que `vars_files:` qui est niveau 13.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/precedence-variables/challenge/solution.yml
   ```
