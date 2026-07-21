# 🎯 Challenge : écrire les tests testinfra du rôle webserver

## ✅ Mission

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

## 🧩 Indices

- La fixture `host` est injectée par le plugin pytest-testinfra : chaque
  fonction de test la reçoit en paramètre.
- API : `host.package("nginx").is_installed`, `host.service("nginx").is_running`,
  `host.socket("tcp://0.0.0.0:8080").is_listening`, `host.run("nginx -t").rc`.
- Exécution réelle contre l'instance :

  ```bash
  cd labs/tests/testinfra
  ANSIBLE_ROLES_PATH=$PWD/roles molecule test    # nécessite Podman
  ```

## 📓 Journal de commandes

Quand vos tests sont prêts, consignez dans `challenge/solution.sh` les
commandes exécutées (`molecule verify`...). Ce journal doit exister pour
que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/tests/testinfra/challenge/tests/
```

Le test analyse votre fichier Python (AST : vraies fonctions de test
utilisant `host`, vraies assertions) et vérifie que pytest sait le
collecter.

## 🧹 Reset

```bash
dsoxlab clean tests-testinfra
```

## 💡 Pour aller plus loin

- `host.file(...).content_string` : asserter sur le contenu d'un fichier.
- Paramétrer un même test sur plusieurs paquets avec `@pytest.mark.parametrize`.
- Comparer avec le verifier Ansible du lab 62 : quand préférer l'un ou l'autre ?
