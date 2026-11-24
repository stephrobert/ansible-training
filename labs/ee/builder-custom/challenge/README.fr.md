# Aucune image publique ne convient, et l'audit veut savoir ce qui tourne

## La situation

Aucun EE officiel ne fait l'affaire. Le minimal n'a pas les collections que vos
playbooks appellent ; les gros embarquent des centaines de mégaoctets dont vous
ne ferez rien et un `ansible-core` que vous ne maîtrisez pas. Pendant ce temps,
l'équipe sécurité pose une question légitime : qu'est-ce qui s'exécute exactement
sur les hôtes d'automatisation ? « Ce vers quoi pointait `:latest` le jour du
build » n'est pas une réponse qu'elle acceptera, et ce n'en est pas une que vous
sauriez reproduire.

Votre mission, depuis le répertoire du projet :

1. Écrire la recette d'un **EE sur mesure**, au schéma courant, basée sur une
   image minimale et construite avec Podman.
2. **Tout épingler** : `ansible-core`, chaque collection, chaque dépendance Python
   à une version exacte, et déclarer les dépendances système nécessaires.
3. Inspecter le fichier de construction généré par le build : savoir ce qui est
   assemblé plutôt que faire confiance à une boîte noire.
4. Tester l'image obtenue, puis la pousser sur un **registre privé** pour que
   l'équipe consomme une version, et non un tag mouvant.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/ee-builder/

## 🎯 Challenge — Builder un EE custom avec `ansible-builder`

### ✅ Objectif

Produire les 5 fichiers requis pour builder un EE custom **schéma v3**. Un sixième fichier, `configs/ansible.cfg`, est livré et doit être conservé tel quel :

| Fichier | Attente |
| --- | --- |
| `execution-environment.yml` | `version: 3`. `images.base_image.name` contient `community-ee-minimal`. `dependencies.ansible_core.package_pip` pinné avec `==`. |
| `requirements.yml` | Toutes les collections déclarent `version:` (pas de plage `>=` flottante). |
| `requirements.txt` | Toutes les dépendances Python pinnées avec `==`. |
| `bindep.txt` | Contient `[platform:rpm]` (system deps RHEL). |
| `build-ee.sh` | Exécutable. Utilise `--container-runtime podman`. |
| `configs/ansible.cfg` | Livré. Conserver `host_key_checking = False` (injecté dans l'EE). |

### 🧩 Bloqué ?

```bash
dsoxlab hint ee-builder-custom
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
cd labs/ee/builder-custom/
./build-ee.sh
podman run --rm localhost/lab86-custom-ee:latest ansible --version
```

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées (build,
vérifications podman). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/builder-custom/challenge/tests/
```

Les tests contrôlent la sémantique de vos 5 fichiers et, si
ansible-builder est installé, exécutent `ansible-builder create` pour
prouver que la définition est acceptée par l'outil.

### 🧹 Reset

```bash
dsoxlab clean ee-builder-custom
```

### 💡 Pour aller plus loin

- **`additional_build_steps`** dans `execution-environment.yml` :
  injecter des commandes `RUN` arbitraires (custom CA cert, debug tools).
- **Multi-stage build** : `builder_image` séparée pour réduire la
  taille de l'image finale.
- **Signer l'image** : `cosign sign localhost/lab86-custom-ee:latest`
  après build (cf. lab 87 CI).
