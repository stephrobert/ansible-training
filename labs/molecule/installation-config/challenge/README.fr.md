# La suite de tests qui passe sur un mensonge

## La situation

Votre scénario Molecule est vert, et il ne prouve presque rien. L'instance
démarre nue : le rôle installe lui-même ses prérequis et le test n'éprouve jamais
l'état de départ réel. Le run ne tire aucune collection : il passe en local et
explose en CI. Personne ne sait quelle tâche mange les quatre minutes. Et le
cycle ne rejoue jamais le rôle : un rôle qui modifie quelque chose à chaque
passage se déclare quand même en succès. Une suite verte incapable d'échouer
n'est qu'une décoration.

Votre mission, depuis le répertoire du projet :

1. Préconditionner l'instance avant l'application du rôle, pour que le test
   parte de l'état d'un vrai serveur, et déclarer les dépendances Galaxy du
   scénario au lieu de compter sur ce qui traîne déjà installé.
2. Donner à chaque instance ses propres variables, pour que le scénario cesse de
   supposer que toutes les plateformes se ressemblent.
3. Figer explicitement l'ordre des étapes du cycle, et y inclure l'étape
   d'**idempotence** : la suite doit pouvoir attraper un rôle qui ne se
   stabilise jamais.
4. Activer le chronométrage des tâches, et désigner la plus lente.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-installation-config/

## 🎯 Challenge : enrichir la configuration Molecule

### ✅ Mission

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
| `molecule.yml` : callbacks | `callbacks_enabled` avec `profile_tasks` et `timer` |
| Le tout | `molecule syntax` passe (pytest l'exécute réellement) |

Attention : `verify.yml` (livré) vérifie que nginx écoute sur le port
surchargé. Si votre `host_vars` est absent ou faux, un `molecule test`
complet échouera.

### 🧩 Bloqué ?

```bash
dsoxlab hint molecule-installation-config
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand votre configuration est prête, consignez dans `challenge/solution.sh`
les commandes Molecule exécutées. Ce journal doit exister pour que pytest
s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/installation-config/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean molecule-installation-config
```

### 💡 Pour aller plus loin

- `MOLECULE_PLAYBOOK` : variable d'environnement pour substituer le
  playbook converge (pattern `${MOLECULE_PLAYBOOK:-converge.yml}`).
- `molecule test --destroy=never` : garder l'instance pour inspection.
