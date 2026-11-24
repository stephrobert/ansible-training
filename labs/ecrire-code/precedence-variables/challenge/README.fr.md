# « j'ai changé la valeur et il ne se passe rien »

## La situation

Deux heures perdues hier. Un collègue a posé la valeur dans le fichier de
vars, lancé le playbook sur **db1.lab**, et récupéré l'ancienne. Il l'a posée
à nouveau, dans un autre fichier : même résultat. Il a fini par modifier le
play lui-même, exactement ce que personne ne veut voir dans le dépôt. Ansible
résout un même nom de variable à travers **vingt-deux niveaux**, et il n'y a
là rien de mystérieux : soit vous connaissez l'ordre, soit vous y passez vos
après-midi. Vous tranchez expérimentalement, depuis **control-node.lab**.

Votre mission :

1. Déclarer la **même variable** dans les `vars:` du play et dans un fichier
   chargé par `vars_files:`.
2. Lancer sans rien passer et enregistrer la valeur résolue sur db1 :
   `vars_files:` (niveau 14) **gagne** contre les `vars:` du play (niveau 12),
   tout l'inverse de l'intuition.
3. Écraser les deux depuis la ligne de commande avec **`--extra-vars`** et
   regarder le niveau le plus haut l'emporter sur tout le reste.
4. Expliquer le résultat plutôt que l'apprendre par cœur : pourquoi
   `--extra-vars` est le bon outil d'une surcharge ponctuelle, et le mauvais
   d'un réglage permanent.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/

## 🎯 Challenge — Précédence : deux duels à trancher

### ✅ Objectif

Démontrer **deux** choses d'un seul run, avec **deux** variables :

1. **`winner`** : `--extra-vars` (niveau 22) est plus fort que `vars:` du play
   (niveau 12) **et** que `vars_files:` (niveau 14).
2. **`duel`** : entre `vars:` du play (niveau 12) et `vars_files:` (niveau 14),
   **`vars_files:` gagne**. C'est le résultat contre-intuitif du lab, et
   personne ne passe `--extra-vars` sur `duel` : il se joue seul.

Vous allez donc superposer ces variables à plusieurs niveaux, lancer le play
avec `--extra-vars` sur **`winner` seulement**, et lire les deux résultats.

### 🧩 Fichiers à créer

#### 1) `challenge/vars/loader.yml`

```yaml
---
winner: "vars_files"
duel: "vars_files"
```

#### 2) `challenge/solution.yml`

Squelette à compléter :

```yaml
---
- name: Challenge - precedence des variables
  hosts: ???
  become: ???

  vars:
    winner: "play_vars"               # niveau 12
    duel: "play_vars"                 # niveau 12

  vars_files:
    - ???                             # vars/loader.yml : niveau 14

  tasks:
    - name: Poser /tmp/precedence-result.txt avec les valeurs résolues
      ansible.builtin.copy:
        dest: ???
        content: |
          winner={{ ??? }}
          duel={{ ??? }}
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Niveau 22 = top du top** : `--extra-vars` gagne sur **toutes** les
>   autres sources (vars:, vars_files:, group_vars, host_vars,
>   set_fact…). C'est ce qui rend les paramètres CLI parfaits pour un
>   override ponctuel sans toucher au code.
> - **Le test attend `winner=extra_vars_wins`**. Le conftest passe
>   `--extra-vars "winner=extra_vars_wins"` automatiquement. Si vous
>   lancez sans, `winner` vaudra `vars_files` (et non `play_vars` :
>   voir le piège suivant).
> - **`vars_files:` (14) est plus FORT que `vars:` du play (12)** :
>   exactement l'inverse de l'intuition naïve, qui voudrait que ce qui est
>   écrit dans le play l'emporte sur un fichier annexe. C'est **ça** qu'il
>   faut mémoriser pour l'EX294, et c'est ce que prouve `duel` : le test
>   attend `duel=vars_files`.
> - **Ne trichez pas sur `duel`** : la seule façon d'obtenir
>   `duel=vars_files` est de le déclarer **aux deux endroits** et de
>   laisser la précédence trancher. Le déclarer uniquement dans
>   `vars/loader.yml` ferait passer le test sans rien démontrer.

### 🚀 Lancement (avec --extra-vars)

```bash
ansible-playbook labs/ecrire-code/precedence-variables/challenge/solution.yml \
    --extra-vars "winner=extra_vars_wins"
```

🔍 Vérifiez :

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/precedence-result.txt"
# Doit afficher :
#   winner=extra_vars_wins
#   duel=vars_files
```

Deux lectures dans ce fichier :

- `winner=extra_vars_wins` : `--extra-vars` (niveau 22) **écrase** à la fois
  `vars:` du play (12) et `vars_files:` (14). Rien ne lui résiste.
- `duel=vars_files` : sans `--extra-vars` pour arbitrer, **`vars_files:` (14)
  bat `vars:` du play (12)**. Voilà le vrai enseignement du lab.

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/precedence-variables/challenge/tests/
```

> ⚠️ Le `conftest.py` racine joue automatiquement votre `solution.yml` avec
> `--extra-vars "winner=extra_vars_wins"` (cf. `_EXTRA_ARGS`).

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-precedence-variables
```

### 💡 Pour aller plus loin

- **Sans `--extra-vars`** : relancez sans le flag. `winner` bascule alors sur
  `vars_files`, pour la même raison que `duel` : **`vars_files:` (14) gagne**
  sur `vars:` du play (12). Cf. la table de précédence officielle de la doc.
- **Comment faire gagner le play, alors ?** Pas avec `vars:`. Il faut monter
  au-dessus de 14 : `set_fact` (19), ou des `task vars` (17) sur la tâche.
- **`set_fact`** : niveau 19 (au-dessus de `vars:`, de `vars_files:` et
  d'`include_vars`, mais sous `--extra-vars`). Posez un
  `set_fact: duel: "set_fact_wins"` dans une tâche **avant** celle qui pose le
  fichier, et observez.
- **`include_vars`** vs `vars_files:` : `include_vars` est niveau 18, donc
  **plus fort** que `vars_files:` (14). Mais il reste **sous** `set_fact` (19),
  et ce même si l'`include_vars` s'exécute après : le niveau prime sur l'ordre
  chronologique.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/precedence-variables/challenge/solution.yml
   ```
