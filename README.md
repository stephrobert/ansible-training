
# Ansible Training

Bienvenue dans ce projet **Ansible Training** !

Ce dépôt propose un parcours didactique et progressif pour découvrir et
maîtriser **Ansible**, de l’automatisation basique à l’orchestration avancée. À
travers des exercices pratiques et des exemples concrets, vous apprendrez à
gérer vos infrastructures, déployer des applications et orchestrer des
environnements complexes.

Ce n’est pas un cours académique, mais plutôt un guide pour vous accompagner
dans votre montée en compétences sur Ansible.

## 🎯 Objectifs

- [**Comprendre les concepts fondamentaux
  d’Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/)
  : inventaire, ad-hoc, modules, playbooks.
- [**Apprendre à écrire des
  playbooks**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecriture-de-playbooks-ansible/)
  clairs et modulaires en utilisant les bonnes pratiques YAML.
- [**Structurer et réutiliser votre
code**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/)
via les rôles et les collections. -[ **Gérer la sécurité et les données
sensibles**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/vault/)
avec Ansible Vault.
- [**Mettre en place des tests
  automatisés**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/molecule-tox/)
  pour garantir la qualité de vos automatisations.
- ...

---

## 📚 Structure du Projet

**TP Existants :**

- [`00-Introduction-Ansible`](./00-Introduction-Ansible) — Présentation
  d’Ansible, concepts fondamentaux (inventaires, modules, ad-hoc, YAML).
- [`01-Inventaires-Statiques`](./01-Inventaires-Statiques) — Introduction à
  Ansible, installation, configuration de l’inventaire, commandes ad-hoc.
- [`02-Playbooks`](./02-Playbooks) — Rédaction de playbooks simples, tâches,
  variables, gestion des handlers et conditions.
- [`03-Handlers`](./03-Handlers) — Utilisation des handlers pour exécuter des
  actions conditionnelles, gestion des modifications de configuration.
- [`04-Templates`](./04-Templates) — Utilisation avancée des variables (groupes,
  hôtes, fichiers vars), Jinja2 et templates pour la génération dynamique de
  fichiers.
- [`05-Inventaires-Dynamiques`](./05-Inventaires-Dynamiques) — Création
  d’inventaires dynamiques, intégration avec des services cloud (AWS, Azure,
  GCP), gestion des groupes dynamiques.
- [`06-Conditions`](./06-Conditions) — Utilisation des conditions (`when`) pour
  contrôler l’exécution des tâches en fonction de variables et de faits système.
- [`07-Roles`](./07-Roles) — Structuration du code : création, organisation et
  réutilisation de rôles Ansible, bonnes pratiques.
- [`08-Blocks`](./08-Blocks) — Utilisation des blocks pour regrouper des tâches
  et gérer les erreurs.
- [`09-Vault`](./09-Vault) — Chiffrement des données sensibles avec Ansible
  Vault, bonnes pratiques de sécurisation.
- [`10-Customs-Facts`](./10-Customs-Facts) — Définition et utilisation de faits
  personnalisés (custom facts) pour adapter les playbooks aux caractéristiques
  des hôtes.
-
**TP à venir :**

Voici une idée de futurs TP !

- [`11-Collection-modules`](./11-Collection-modules) — Création et publication
  de collections personnalisées, développement de modules Ansible en Python.
- [`12-Galaxy-et-Community`](./12-Galaxy-et-Community) — Utilisation d’Ansible
  Galaxy, import de rôles existants et contribution à la communauté.
- [`13-Orchestration-Avancée`](./13-Orchestration-Avancée) — Scénarios
  multi-niveaux, orchestration de clusters (Docker, Kubernetes), déploiements
  blue/green, rolling updates.
- [`14-CI-CD-Integration`](./14-CI-CD-Integration) — Intégration d’Ansible dans
  des pipelines CI/CD (GitLab CI, GitHub Actions, Jenkins), bonnes pratiques
  DevOps.
- [`15-Tests-et-Validation`](./15-Tests-et-Validation) — Tests de playbooks avec
  Molecule et Testinfra, validation automatique, intégration continue pour
  l’assurance qualité.

---

## 🔧 Prérequis

Ansible ne peut être installé, en théorie, que sur des ordinateurs fonctionnant
sur les systèmes d’exploitation **Linux** et **MacOS**. Pour ces TP, nous utiliserons
une machine Linux.

La manière la plus propre pour installer Ansible se fait avec `pipx`. `pipx`
est un gestionnaire de paquets Python qui permet d'installer des applications
Python dans des environnements isolés, ce qui est particulièrement utile pour
éviter les conflits de dépendances entre différentes applications Python.

### Installation de `pipx`

Pour installer `pipx`, vous devez d'abord installer `pip` si ce n'est pas déjà
fait. `pip` est le gestionnaire de paquets Python standard. Vous pouvez
installer `pip` en utilisant le gestionnaire de paquets de votre système
d'exploitation.

* **Sur MacOS** :

```bash
brew install pipx
pipx ensurepath
sudo pipx ensurepath --global # optional to allow pipx actions with --global argument
```

* **Sur Debian/Ubuntu** :

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
sudo pipx ensurepath --global # optional to allow pipx actions with --global argument
```

* **Sur Fedora** :

```bash
sudo dnf install pipx
pipx ensurepath
sudo pipx ensurepath --global # optional to allow pipx actions with --global argument
```

* **Sur Arch Linux** :

```bash
sudo pacman -S python-pipx
pipx ensurepath
sudo pipx ensurepath --global # optional to allow pipx actions with --global argument
```

### Installation d' Ansible avec `pipx`

Maintenant que `pipx` est installé, vous pouvez installer Ansible en utilisant
la commande suivante :

```bash
pipx install --include-deps ansible
```

### Test après installation d’Ansible

Comment exécuter Ansible ? Il suffit de taper la commande suivante qui va
simplement lancer en local (-c local) un shell qui exécutera la commande `echo
'salut B0B'`:

```bash
ansible all -i "localhost," -c local -m shell -a 'echo Salut B0B'

localhost | success | rc=0 >>
salut B0B
```

### Installation d'Incus

L'installation d'**Incus** est assez simple et peut être effectuée sur plusieurs
distributions Linux, telles qu'Ubuntu, Fedora et Gentoo. Voici les étapes de
base pour installer Incus sur les systèmes les plus courants.

* **Installation sur Ubuntu** :

Si vous utilisez une version récente d'Ubuntu (24.04 LTS ou ultérieure), vous
pouvez installer Incus directement à partir des dépôts officiels. Voici les
étapes :

1. Mettez à jour vos paquets :

   ```bash
   sudo apt update
   ```

2. Installez **Incus** avec la commande suivante :

   ```bash
   sudo apt install incus
   ```

3. Pour pouvoir gérer les machines virtuelles, installez également **QEMU** :

   ```bash
   sudo apt install qemu-system
   ```

4. Si vous migrez depuis **LXD**, vous pouvez installer l’outil de migration :

   ```bash
   sudo apt install incus-tools
   ```

* **Installation sur Fedora** :

1. Installez le plugin **COPR** pour dnf :

   ```bash
   sudo dnf install 'dnf-command(copr)'
   ```

2. Activez le dépôt COPR pour Incus :

   ```bash
   sudo dnf copr enable ganto/lxc4
   ```

3. Installez **Incus** :

   ```bash
   sudo dnf install incus
   ```

#### Autoriser `incus` pour votre utilisateur

Pour autoriser votre utilisateur à utiliser `incus` sans être forcé de passer par l'utilisateur `root`, vous pouvez exécuter les
commande suivante :

1. Ajouter les groupes nécessaires pour `incus`

   ```bash
   # Penser à remplacer <username> par votre utilisateur 
   sudo usermod -a -G incus <username>
   sudo usermod -a -G incus-admin <username>
   ```

2. Redémarrer la machine pour prendre en compte l'ajout dans les groupes

   Le redémarrage du service ne semble pas suffisant pour prendre en compte les changements de groupes. Cependant, suivant la distribution cette commande devrait suffire.

   ```bash
   sudo systemctl restart incus
   # Sinon
   sudo init 6
   ```

3. Après redémarrage, initialiser `incus`

   ```bash
   incus admin init
   ```

4. Vérifier la prise en compte des droits

   ```bash
   incus list

   +------+-------+------+------+------+-----------+
   | NAME | STATE | IPV4 | IPV6 | TYPE | SNAPSHOTS |
   +------+-------+------+------+------+-----------+
   ```

#### Vérification de l'installation

Pour vérifier que l'installation s'est bien déroulée, vous pouvez exécuter la
commande suivante :

```bash
incus version

Client version: 6.0.0
Server version: 6.0.0
```

---

## 🚀 Démarrage rapide

1. **Cloner le dépôt** :

   ```bash
   git clone https://github.com/stephrobert/ansible-training.git
   cd ansible-training
   ```

2. **Commencez par le dossier `00-Introduction-Ansible` pour vous familiariser
   avec les concepts et le vocabulaire propre à Ansible.**
3. **Ensuite poursuivez avec les autres dossiers dans l’ordre indiqué.**

---

## 🔄 Mise à jour du dépôt

Je continuerai à enrichir ce dépôt avec de nouveaux exercices, exemples et
améliorations. Pour récupérer les dernières modifications depuis la branche
`main`, exécutez :

```bash
git pull origin main
```

---

## 🤝 Contribuer

Vos retours, corrections et suggestions sont les bienvenus !

1. Créez une **issue** pour signaler un bug, proposer une amélioration ou poser
   une question.
2. Forkez le dépôt et ouvrez une **pull request** pour soumettre vos
   modifications (nouvelle section, corrections orthographiques, nouveaux
   exercices, etc.).

Consultez le fichier [`CONTRIBUTING.md`](./contributing.md) pour en savoir plus
sur les bonnes pratiques de contribution.

---

## ☕ Me soutenir

Si vous trouvez ce guide utile et souhaitez me soutenir, vous pouvez me offrir
un café :

[![Ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/votre-identifiant)

---

## © Copyright et licence

- **Auteur** : Stéphane Robert (2025)
- **Licence** : [Creative Commons BY-SA
  4.0](https://creativecommons.org/licenses/by-sa/4.0/)

![Creative Commons
BY-SA](https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-sa.png)
