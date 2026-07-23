# 🎯 Challenge — `--check --diff` puis exécution réelle

## ✅ Objectif

Écrire `challenge/solution.yml` qui pose un fichier `/etc/lab-checkmode.txt` sur
**db1.lab** contenant la chaîne **`Lab checkmode validé`**.

Le but pédagogique : démontrer le **workflow audit → exécution** :

1. **Audit** : on lance d'abord en `--check --diff` pour visualiser ce qui *va*
   changer, sans rien écrire.
2. **Exécution réelle** : une fois le diff validé, on relance sans `--check`.

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-checkmode-diff
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement en deux temps

### 1. Audit en `--check --diff`

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/challenge/solution.yml \
    --check --diff
```

🔍 **Ce que vous devez voir** :

- `PLAY RECAP` : `changed=1` (intention)
- Un bloc diff montrant `before:` (vide) → `after:` (votre contenu)
- **Côté db1**, le fichier n'existe **pas encore** :

   ```bash
   ansible db1.lab -b -m ansible.builtin.command -a "ls /etc/lab-checkmode.txt"
   # Doit retourner: ls: cannot access ...: No such file or directory
   ```

### 2. Exécution réelle

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/challenge/solution.yml --diff
```

🔍 **Ce que vous devez voir** :

- `PLAY RECAP` : `changed=1` (cette fois pour de vrai)
- Le diff identique à celui de l'audit
- Le fichier est posé sur db1 :

   ```bash
   ansible db1.lab -m ansible.builtin.command -a "cat /etc/lab-checkmode.txt"
   ```

### 3. Vérifier l'idempotence

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/challenge/solution.yml --diff
```

🔍 `changed=0`, **pas de diff** affiché. C'est l'état stationnaire.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/checkmode-diff/challenge/tests/
```

Le test vérifie sur db1 :

- `/etc/lab-checkmode.txt` existe.
- Son contenu inclut `Lab checkmode validé`.

> ⚠️ Le `conftest.py` racine joue automatiquement votre `solution.yml` avant
> les tests (fixture `_apply_lab_state`). Si pytest **skippe** avec un message
> *"Aucun challenge/solution.yml ni solution.sh trouvé"*, c'est qu'il faut
> d'abord écrire `solution.yml` !

## 🧹 Reset (rejouer le scénario depuis zéro)

```bash
dsoxlab clean ecrire-code-checkmode-diff
```

Cette cible supprime `/etc/lab-checkmode.txt` côté db1 pour rejouer l'audit
diff "à blanc" (le diff doit re-montrer un ajout).

## 🚀 Pour aller plus loin

- **Reproduire l'audit** : faites `dsoxlab clean <id-du-lab>` puis ré-exécutez `--check --diff`
  pour bien voir le diff "création depuis rien". Comparez avec un `--check
  --diff` quand le fichier est déjà posé (idempotence : aucun diff).
- **`check_mode: false`** : ajoutez une tâche `command:` qui lit la version d'un
  binaire (`openssl version`) avec `check_mode: false` et `changed_when: false`.
  Vérifiez qu'elle s'exécute même en `--check` (preuve : la sortie est
  capturable via `register:` et utilisable dans un `debug:`).
- **Lint avec `ansible-lint`** : avant de lancer votre playbook, validez sa
  qualité avec :

   ```bash
   ansible-lint labs/ecrire-code/checkmode-diff/challenge/solution.yml
   ```

   Si `ansible-lint` retourne sans erreur, le YAML est conforme aux bonnes
   pratiques (FQCN, `name:` sur chaque tâche, modes en chaîne, etc.). Vous
   pouvez aussi lancer le profil `production` (le plus strict) :

   ```bash
   ansible-lint --profile production \
       labs/ecrire-code/checkmode-diff/challenge/solution.yml
   ```
