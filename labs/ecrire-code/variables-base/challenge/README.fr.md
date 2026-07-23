# 🎯 Challenge — Variables et override par `--extra-vars`

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** combine **3 sources** de
variables et démontre la **précédence** d'`--extra-vars` (niveau 22, le plus haut).

Vous allez créer **deux fichiers** :

1. `challenge/vars/db.yml` — un fichier de variables externe.
2. `challenge/solution.yml` — le playbook qui charge `vars_files:` + `vars:`.

À l'exécution, on passe `--extra-vars` pour forcer 2 valeurs et observer
qu'elles **écrasent** celles du play.

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-variables-base
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

### Premier run — sans `--extra-vars`

```bash
ansible-playbook labs/ecrire-code/variables-base/challenge/solution.yml
```

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/challenge-vars.txt"
```

🔍 Vous devez voir les 4 valeurs **par défaut** (cf. tableau ci-dessus).

### Second run — avec `--extra-vars`

```bash
ansible-playbook labs/ecrire-code/variables-base/challenge/solution.yml \
    --extra-vars "service_name=production-api db_max_connections=500"
```

🔍 Le fichier doit contenir :

```text
service_name=production-api    ← écrasé par --extra-vars
service_port=8000              ← du play (non surchargé)
db_engine=postgresql           ← du vars_files: (non surchargé)
db_max_connections=500         ← écrasé par --extra-vars
```

> 💡 **Pièges** :
>
> - **`--extra-vars` (priorité 22)** gagne sur **tout**. C'est ce qui rend
>   les params CLI parfaits pour des overrides ponctuels.
> - **Format `--extra-vars "k1=v1 k2=v2"`** : les valeurs **simples** se
>   passent au format clé=valeur. Pour des valeurs complexes (listes,
>   dicts), utiliser le format JSON avec `--extra-vars '{"k": [1,2]}'`.
> - **Boolean `--extra-vars "flag=true"`** est lu comme **string**, pas
>   bool. Comparer avec `flag | bool` ou `flag == "true"`, pas `flag is true`.
> - **`vars_files:` (14)** > **`vars:` du play (12)** : le fichier chargé
>   **gagne** sur ce qui est écrit dans le play. Contre-intuitif, et à
>   retenir pour l'EX294. Ici les deux sources ne portent pas les mêmes
>   variables, donc le piège ne se déclenche pas ; le lab
>   `precedence-variables` le met en scène et le mesure.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/variables-base/challenge/tests/
```

> ⚠️ Le `conftest.py` racine joue automatiquement votre `solution.yml` avec
> `--extra-vars "service_name=production-api db_max_connections=500"` (cf.
> `_EXTRA_ARGS` dans le conftest). C'est ce qui rend les 5 assertions vertes.

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-variables-base
```

## 💡 Pour aller plus loin

- **Tester `group_vars/all.yml`** : posez `service_port: 9999` dans
  `inventory/group_vars/all.yml` et relancez sans `--extra-vars`. Quelle valeur
  gagne ? Qui est plus prioritaire entre `vars:` du play et `group_vars/all.yml` ?
  (Spoiler : `vars:` du play ; cf. lab 15 pour la table de précédence complète.)
- **Format JSON pour `--extra-vars`** :

   ```bash
   --extra-vars '{"service_port": 9090, "tags": ["v1", "stable"]}'
   ```

   Indispensable pour passer des **listes** ou des **dicts** complexes.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/variables-base/challenge/solution.yml
   ```
