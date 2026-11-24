# Le même projet, deux machines, deux résultats

## La situation

Le déploiement marchait en juillet et échoue aujourd'hui, sur le même commit.
Rien n'a bougé dans le dépôt : un rôle amont a publié une nouvelle version majeure
cette nuit, et le projet l'installe sans épinglage, donc chaque machine tire ce
qui est le plus récent au moment où elle tourne. Votre poste, le runner de CI et
le collègue arrivé la semaine dernière exécutent trois bases de code différentes
depuis des checkouts Git identiques.

Votre mission, depuis le répertoire du projet :

1. Déclarer **toutes** les dépendances du projet dans un manifeste unique : rôles
   Galaxy, rôles tirés directement de **Git**, et collections, pour que plus rien
   ne s'installe par tradition orale.
2. Les **épingler** toutes, en choisissant l'épinglage adapté à chaque cas : une
   version exacte là où la surprise est interdite, une plage bornée ailleurs.
3. Distinguer les deux chemins d'installation : rôles et collections
   n'atterrissent pas au même endroit, et aucun des deux n'est versionné par le
   dépôt.
4. **Vendoriser** dans le projet le seul rôle que vous ne pouvez pas perdre, et
   justifier pourquoi celui-là et pas les autres.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/installer-roles-galaxy/

## 🎯 Challenge : écrire un requirements.yml et l'installer réellement

### ✅ Mission

Deux temps, tous deux vérifiés par pytest :

1. **Écrire** `requirements.yml` (à la racine du lab, livré en squelette) :

   | Attente | Détail |
   | --- | --- |
   | Section `roles:` | au moins 2 rôles, TOUS avec `version:` épinglée |
   | Source Git | au moins 1 rôle avec `src:` pointant github.com |
   | Source Galaxy | au moins 1 rôle sans `src:` (résolu via Galaxy) |
   | Section `collections:` | au moins 1 collection épinglée en version EXACTE (X.Y.Z) |

2. **Installer** ce manifeste dans le lab (nécessite le réseau) :

   ```bash
   cd labs/galaxy/installer-roles/
   ansible-galaxy role install -r requirements.yml -p challenge/deps/roles
   ansible-galaxy collection install -r requirements.yml -p challenge/deps/collections
   ```

   Pytest vérifie que **chaque rôle déclaré est réellement présent** dans
   `challenge/deps/roles/` et que la collection épinglée est installée
   **dans la version exacte demandée** (lecture du MANIFEST.json).

### 🧩 Bloqué ?

```bash
dsoxlab hint galaxy-installer-roles
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes d'installation
exécutées. Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/galaxy/installer-roles/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean galaxy-installer-roles
```

### 💡 Pour aller plus loin

- `signatures:` sur les collections : vérification GPG cryptographique.
- `ansible-galaxy install -r ... --force` : forcer la réinstallation.
- Vendoriser `challenge/deps/` ou pas ? Le débat lockfile appliqué à Ansible.
