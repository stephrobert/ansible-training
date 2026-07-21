# 🎯 Challenge : enrichir la configuration Molecule

## ✅ Mission

Le scénario `molecule/default/` est livré dans sa version **minimale** du
lab 62 (converge.yml, verify.yml, create.yml et destroy.yml sont fournis).
Votre travail : les enrichissements de configuration, que vous écrivez
vous-même.

`prepare.yml`, lui, est le seul playbook du banc que vous devez écrire :
c'est précisément l'objet de ce lab. Sans lui, l'instance reste nue et le
`converge` échoue.

État attendu (c'est ce que pytest vérifie) :

| Élément | Attente |
| --- | --- |
| `molecule/default/requirements.yml` | À créer : collections nécessaires au scénario (ansible.posix, containers.podman...) avec contrainte de version |
| `molecule.yml` : `dependency` | `dependency.options.requirements-file` câblé vers votre `requirements.yml` |
| `molecule/default/prepare.yml` | À créer : play de préparation de l'instance (prérequis hors du périmètre du rôle) |
| `molecule.yml` : `host_vars` | `provisioner.inventory.host_vars` surcharge `webserver_listen_port: 8080` pour l'instance |
| `molecule.yml` : `test_sequence` | séquence personnalisée sous `scenario:`, incluant `prepare`, `converge`, `idempotence` et `verify` |
| `molecule.yml` : callbacks | `callback_enabled` avec `profile_tasks` et `timer` |
| Le tout | `molecule syntax` passe (pytest l'exécute réellement) |

Attention : `verify.yml` (livré) vérifie que nginx écoute sur le port
surchargé. Si votre `host_vars` est absent ou faux, un `molecule test`
complet échouera.

## 🧩 Indices

- `dependency.name: galaxy` accepte `options.requirements-file` pour
  pointer un fichier de dépendances du scénario.
- `prepare.yml` est joué une seule fois après `create`, avant `converge` :
  parfait pour installer `procps-ng` et `iproute` (diagnostic) qui ne sont
  pas du ressort du rôle.
- Deux prérequis, pas un seul. `verify.yml` a besoin de `ss` (paquet
  `iproute`) pour constater le port d'écoute, mais le **rôle lui-même** a
  besoin de `firewalld` : il ouvre son port avec `ansible.posix.firewalld`.
  Sur une VM le démon tourne déjà ; dans un conteneur, non, et le
  `converge` meurt sur « firewalld is not running ». Installer le paquet ne
  suffit pas, il faut aussi démarrer le service. Un rôle qui **configure**
  un pare-feu n'a pas à en **installer** un : c'est au banc de test de
  fournir la machine dans l'état attendu.
- Contrairement à une idée répandue, la séquence par défaut de Molecule
  joue déjà `prepare`. Déclarer votre `test_sequence` ne sert donc pas à
  l'activer, mais à retirer les étapes que vous n'avez pas (`cleanup`,
  `side_effect`) et à rendre le contrat explicite.
- La séquence par défaut se surcharge ainsi :

  ```yaml
  scenario:
    name: default
    test_sequence:
      - ...
  ```

- Testez au fur et à mesure :

  ```bash
  cd labs/molecule/installation-config
  ANSIBLE_ROLES_PATH=$PWD/roles molecule syntax
  ```

## 📓 Journal de commandes

Quand votre configuration est prête, consignez dans `challenge/solution.sh`
les commandes Molecule exécutées. Ce journal doit exister pour que pytest
s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/molecule/installation-config/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean molecule-installation-config
```

## 💡 Pour aller plus loin

- `MOLECULE_PLAYBOOK` : variable d'environnement pour substituer le
  playbook converge (pattern `${MOLECULE_PLAYBOOK:-converge.yml}`).
- `molecule test --destroy=never` : garder l'instance pour inspection.
