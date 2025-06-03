
# Ansible Training

Bienvenue dans ce projet **Ansible Training** !

Ce dépôt propose un parcours didactique et progressif pour découvrir et maîtriser **Ansible**, de l’automatisation basique à l’orchestration avancée. À travers des exercices pratiques et des exemples concrets, vous apprendrez à gérer vos infrastructures, déployer des applications et orchestrer des environnements complexes.

Ce n’est pas un cours académique, mais plutôt un guide pour vous accompagner dans votre montée en compétences sur Ansible.

## 🎯 Objectifs

- **Comprendre les concepts fondamentaux** d’Ansible : inventaire, ad-hoc, modules, playbooks.
- **Apprendre à écrire des playbooks** clairs et modulaires en utilisant les bonnes pratiques YAML.
- **Structurer et réutiliser votre code** via les rôles et les collections.
- **Gérer la sécurité et les données sensibles** avec Ansible Vault.
- **Orchestrer des environnements complexes** et automatiser des déploiements multi-niveaux.
- **Intégrer Ansible dans un workflow DevOps**, avec des pipelines CI/CD.
- **Mettre en place des tests automatisés** pour garantir la qualité de vos automatisations.

---

## 📚 Structure du Projet

- [`00-Introduction-Ansible`](./00-Introduction-Ansible) — Présentation d’Ansible, concepts fondamentaux (inventaires, modules, ad-hoc, YAML).
- [`01-Inventaires-Statiques`](./01-Inventaires-Statiques) — Introduction à Ansible, installation, configuration de l’inventaire, commandes ad-hoc.
- [`02-Playbooks`](./02-Playbooks) — Rédaction de playbooks simples, tâches, variables, gestion des handlers et conditions.
- [`03-Templates`](./03-Templates) — Utilisation avancée des variables (groupes, hôtes, fichiers vars), Jinja2 et templates pour la génération dynamique de fichiers.
- [`04-Roles`](./04-Roles) — Structuration du code : création, organisation et réutilisation de rôles Ansible, bonnes pratiques.
- [`05-Collection-modules`](./05-Collection-modules) — Création et publication de collections personnalisées, développement de modules Ansible en Python.
- [`06-Galaxy-et-Community`](./06-Galaxy-et-Community) — Utilisation d’Ansible Galaxy, import de rôles existants et contribution à la communauté.
- [`07-Sécurité-et-Vault`](./07-Sécurité-et-Vault) — Chiffrement des données sensibles avec Ansible Vault, bonnes pratiques de sécurisation.
- [`08-Orchestration-Avancée`](./08-Orchestration-Avancée) — Scénarios multi-niveaux, orchestration de clusters (Docker, Kubernetes), déploiements blue/green, rolling updates.
- [`09-CI-CD-Integration`](./09-CI-CD-Integration) — Intégration d’Ansible dans des pipelines CI/CD (GitLab CI, GitHub Actions, Jenkins), bonnes pratiques DevOps.
- [`10-Tests-et-Validation`](./10-Tests-et-Validation) — Tests de playbooks avec Molecule et Testinfra, validation automatique, intégration continue pour l’assurance qualité.

---

## 🔧 Prérequis

Avant de commencer, assurez-vous d’avoir :

- **Python** (3.6+) et `pip` :

  ```bash
  sudo apt-get install python3 python3-pip
  ```

- **Pipx** pour installer Ansible et ses dépendances de manière isolée :

  ```bash
  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
  pipx install ansible
  pipx install ansible-lint
  ```

- **Incus** pour tester localement vos playbooks sans impacter votre infrastructure de production.

---

## 🚀 Démarrage rapide

1. **Cloner le dépôt** :

   ```bash
   git clone https://github.com/votre-utilisateur/ansible-training.git
   cd ansible-training
   ```

2. **Explorer les premiers exemples** (dans `00-Introduction-Ansible`) pour vous familiariser avec l’inventaire et les commandes Ad-hoc.
3. **Lancer un playbook exemple** depuis `01-Playbooks` :

   ```bash
   ansible-playbook -i inventaire/hosts.ini 01-Playbooks/exemple.yml
   ```

---

## 🔄 Mise à jour du dépôt

Je continuerai à enrichir ce dépôt avec de nouveaux exercices, exemples et améliorations. Pour récupérer les dernières modifications depuis la branche `main`, exécutez :

```bash
git pull origin main
```

---

## 🤝 Contribuer

Vos retours, corrections et suggestions sont les bienvenus !

1. Créez une **issue** pour signaler un bug, proposer une amélioration ou poser une question.
2. Forkez le dépôt et ouvrez une **pull request** pour soumettre vos modifications (nouvelle section, corrections orthographiques, nouveaux exercices, etc.).

Consultez le fichier [`CONTRIBUTING.md`](./contributing.md) pour en savoir plus sur les bonnes pratiques de contribution.

---

## ☕ Me soutenir

Si vous trouvez ce guide utile et souhaitez me soutenir, vous pouvez me offrir un café :

[![Ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/votre-identifiant)

---

## © Copyright et licence

- **Auteur** : Stéphane Robert (2025)
- **Licence** : [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

![Creative Commons BY-SA](https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-sa.png)
