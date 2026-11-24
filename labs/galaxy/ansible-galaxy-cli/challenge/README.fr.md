# Toute l'équipe cherche la même commande chaque semaine

## La situation

`ansible-galaxy` fait sept métiers différents et personne dans l'équipe n'en
retient plus de trois. L'un réinvente à la main un squelette de rôle en ayant
oublié qu'`init` existe. L'autre installe une collection dans le mauvais chemin.
Un troisième tente de publier et découvre, au pire moment, qu'il faut d'abord
builder un tarball. Deux nouveaux arrivent lundi, et la réponse d'onboarding ne
peut plus être « demande sur le chat ».

Votre mission, depuis le répertoire du projet :

1. Produire la référence de l'équipe pour la CLI : **générer** un rôle et une
   collection, **installer** depuis Galaxy et depuis Git, **lister** ce qui est
   réellement présent en local.
2. Couvrir le chemin de publication de bout en bout : **builder** le tarball, le
   **publier** avec un token API, et **vérifier** l'intégrité de ce qui redescend.
3. Pour chaque commande, préciser où elle écrit : c'est là qu'est le piège, rôles
   et collections n'atterrissent pas au même endroit.
4. Confronter votre référence au binaire réel plutôt qu'à vos souvenirs.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-galaxy-cli/

## 🎯 Challenge : piloter réellement la CLI `ansible-galaxy`

### ✅ Mission

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

### 🧩 Bloqué ?

```bash
dsoxlab hint galaxy-ansible-galaxy-cli
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🧪 Validation

```bash
chmod +x challenge/solution.sh
pytest -v labs/galaxy/ansible-galaxy-cli/challenge/tests/
```

Pytest exécute `challenge/solution.sh` puis contrôle chaque effet
(structure du rôle, galaxy.yml, archive, MANIFEST.json de la collection
installée, sortie de `collection list`).

### 🧹 Reset

```bash
dsoxlab clean galaxy-ansible-galaxy-cli
```

### 💡 Pour aller plus loin

- `ansible-galaxy collection verify` : comparer une collection installée à
  sa source Galaxy (nécessite le réseau).
- `ANSIBLE_COLLECTIONS_PATH` : faire pointer Ansible vers votre dossier
  d'installation custom.
- `ansible-galaxy collection list --format json` : sortie parsable en CI.
