# Le playbook que seul votre poste sait exécuter

## La situation

La mise en production a échoué à 2h du matin et l'astreinte n'a pas pu prendre le
relais. Le playbook tourne sur votre machine et sur elle seule : vous avez une
collection installée que personne d'autre n'a, une bibliothèque Python épinglée par
accident il y a trois mois, et une version d'`ansible-core` qui ne correspond plus
à celle du runner de CI. Chaque passage de main finit pareil : une page de wiki qui
liste les prérequis, et un collègue bloqué au milieu. Le runtime doit voyager avec
le playbook.

Votre mission, depuis le répertoire du projet :

1. Tirer une image **Execution Environment** officielle avec Podman : tout le
   runtime Ansible devient un artefact versionné au lieu d'une page de wiki.
2. Le déclarer comme **environnement par défaut** du projet, et scripter la
   vérification des prérequis pour qu'un nouvel arrivant démarre sans rien demander.
3. Lancer un playbook **dans** l'EE contre **web1.lab** et **db1.lab**, et prouver
   que le conteneur atteint les managed nodes aussi bien qu'un run local.
4. Comparer les deux exécutions, classique et conteneurisée, et nommer ce qui a
   réellement changé : ce qui est désormais garanti, et ce que cela coûte.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/presentation/

## 🎯 Challenge — Lancer un premier playbook dans un EE

### ✅ Objectif

À la racine du lab, produire 4 fichiers qui démontrent l'utilisation
d'`ansible-navigator` avec un Execution Environment officiel
(`community-ansible-dev-tools`).

| Fichier | Attente |
| --- | --- |
| `setup-ee.sh` | Exécutable. Vérifie/installe `podman` et `ansible-navigator`. |
| `inventory.yml` | YAML valide. Hôtes `web1.lab` et `db1.lab` dans le groupe `all`, chacun déclarant son `ansible_host` (IP joignable). |
| `ping.yml` | Module FQCN `ansible.builtin.ping`. |
| `ansible-navigator.yml` | Référence l'image `community-ansible-dev-tools` dans `execution-environment.image:`. |

### 🧩 Bloqué ?

```bash
dsoxlab hint ee-hello
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
cd labs/ee/hello/
./setup-ee.sh
ansible-navigator run ping.yml -i inventory.yml --mode stdout
```

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées (setup,
run navigator). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/hello/challenge/tests/
```

Les tests exécutent réellement `bash -n` sur votre script,
`ansible-inventory` sur votre inventaire et `ansible-playbook
--syntax-check` sur votre playbook. Seul le run dans l'EE (Podman + pull
de community-ansible-dev-tools) reste manuel.

### 🧹 Reset

```bash
dsoxlab clean ee-hello
```

### 💡 Pour aller plus loin

- `ansible-navigator --mode interactive` : interface TUI navigable au
  clavier (`:run`, `:doc`, `:collections`).
- `--pp always` : force un pull à chaque exécution (utile en CI quand
  on push souvent l'EE).
- `~/.ansible-navigator.yml` : config globale au lieu de par-projet.
