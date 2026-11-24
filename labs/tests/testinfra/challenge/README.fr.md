# Les assertions YAML ont dépassé les limites du YAML

## La situation

Votre `verify.yml` est devenu un mur. Vérifier huit paquets impose huit blocs
quasi identiques, chacun avec son `register` et son `assert`. Quand l'un tombe,
le rapport annonce qu'une tâche a échoué, pas quel paquet manque. Le relecteur
réclame en plus la couverture du service, de la socket, du fichier de conf et des
utilisateurs, et le YAML est déjà plus long que le rôle qu'il teste. Les
assertions ne sont pas fausses : elles ont dépassé les limites de leur langage.

Votre mission, depuis le répertoire du projet :

1. Basculer le **verifier** du scénario sur celui en Python, et faire exécuter
   les nouvelles assertions par le cycle à la place des anciennes.
2. Réécrire les vérifications contre l'instance vivante : paquet installé,
   service démarré, socket en écoute, fichier de conf présent, utilisateurs et
   groupes conformes.
3. Replier les cas répétitifs dans un **unique test paramétré** : huit paquets
   coûtent un seul test, et chaque échec nomme son propre cas.
4. Argumenter l'arbitrage : quand le verifier YAML reste le bon choix, et quand
   Python mérite la dépendance qu'il coûte.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-testinfra/

## 🎯 Challenge : écrire les tests testinfra du rôle webserver

### ✅ Mission

Le rôle `webserver` et `converge.yml` sont livrés. À vous d'écrire la
couche de vérification en Python :

| Élément | Attente |
| --- | --- |
| `molecule/default/molecule.yml` | déclarer le verifier `testinfra` (remplacez le `???`) |
| `molecule/default/tests/test_webserver.py` | au moins 4 fonctions `test_*(host)` qui prouvent l'état du serveur |

Les 4 preuves minimales attendues :

1. paquet nginx installé,
2. service nginx démarré et activé au boot,
3. socket en écoute sur le port 8080,
4. `nginx -t` retourne 0 (configuration valide).

### 🧩 Bloqué ?

```bash
dsoxlab hint tests-testinfra
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand vos tests sont prêts, consignez dans `challenge/solution.sh` les
commandes exécutées (`molecule verify`...). Ce journal doit exister pour
que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/tests/testinfra/challenge/tests/
```

Le test analyse votre fichier Python (AST : vraies fonctions de test
utilisant `host`, vraies assertions) et vérifie que pytest sait le
collecter.

### 🧹 Reset

```bash
dsoxlab clean tests-testinfra
```

### 💡 Pour aller plus loin

- `host.file(...).content_string` : asserter sur le contenu d'un fichier.
- Paramétrer un même test sur plusieurs paquets avec `@pytest.mark.parametrize`.
- Comparer avec le verifier Ansible du lab 62 : quand préférer l'un ou l'autre ?
