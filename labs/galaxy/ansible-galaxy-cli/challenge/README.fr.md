# 🎯 Challenge : piloter réellement la CLI `ansible-galaxy`

## ✅ Mission

Fini la lecture de cheatsheet : vous écrivez un script
`challenge/solution.sh` qui **exécute** les commandes `ansible-galaxy`,
et pytest **lance votre script** puis vérifie les effets sur le disque.
Tout se passe hors ligne (scaffolding, build et install depuis une archive
locale), aucun compte Galaxy n'est nécessaire.

Votre script, lancé depuis la racine du lab, doit produire dans
`challenge/build/` :

| Effet attendu | Commande de la famille |
| --- | --- |
| Un rôle `demo_web` scaffoldé dans `challenge/build/roles/` | `ansible-galaxy role init` |
| Une collection `acme.tools` scaffoldée dans `challenge/build/collections/` | `ansible-galaxy collection init` |
| L'archive de la collection dans `challenge/build/dist/` | `ansible-galaxy collection build` |
| La collection installée dans `challenge/build/installed/` **depuis l'archive locale** | `ansible-galaxy collection install` |
| La collection visible par `ansible-galaxy collection list -p challenge/build/installed` | `ansible-galaxy collection list` |

Contraintes :

- Le script doit être **rejouable** : pytest supprime `challenge/build/`
  avant de l'exécuter, votre script recrée tout à chaque run.
- `set -euo pipefail` en tête : la moindre commande qui échoue doit faire
  échouer le script.

## 🧩 Indices

- `role init` et `collection init` acceptent `--init-path <dossier>`.
- `collection init` attend un nom complet `namespace.nom`.
- `collection build` se lance depuis le dossier de la collection et accepte
  `--output-path`.
- `collection install` accepte un chemin d'archive `.tar.gz` et `-p` pour
  choisir le dossier d'installation.
- La cheatsheet livrée à la racine (`cheatsheet.md`) reste votre
  aide-mémoire : chaque commande dont vous avez besoin y figure.

## 🧪 Validation

```bash
chmod +x challenge/solution.sh
pytest -v labs/galaxy/ansible-galaxy-cli/challenge/tests/
```

Pytest exécute `challenge/solution.sh` puis contrôle chaque effet
(structure du rôle, galaxy.yml, archive, MANIFEST.json de la collection
installée, sortie de `collection list`).

## 🧹 Reset

```bash
dsoxlab clean galaxy-ansible-galaxy-cli
```

## 💡 Pour aller plus loin

- `ansible-galaxy collection verify` : comparer une collection installée à
  sa source Galaxy (nécessite le réseau).
- `ANSIBLE_COLLECTIONS_PATH` : faire pointer Ansible vers votre dossier
  d'installation custom.
- `ansible-galaxy collection list --format json` : sortie parsable en CI.
