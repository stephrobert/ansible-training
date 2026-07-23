# Versionner ses playbooks avec Git

> 💡 **Vous arrivez directement à ce lab ?** Il est **autonome** et **local** :
> tout se joue sur votre poste de contrôle, aucune VM n'est nécessaire. Seul
> `git` doit être installé (`git --version`).

## 🧠 Rappel

🔗 [**Versionner ses playbooks avec Git**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/versionner-git/)

Un playbook qui n'est pas versionné est un playbook qu'on finit par casser sans
pouvoir revenir en arrière. L'objectif officiel de l'EX294 « Manage content in a
git repository » est **basique et concret** : savoir initialiser un dépôt, y
suivre ses fichiers, committer, et pousser vers un remote. Rien de plus.

Ce lab tient dans quatre commandes du quotidien :

| Commande | Ce qu'elle fait |
| --- | --- |
| `git init` | crée un dépôt vide (le dossier `.git/`) |
| `git add` | met des fichiers sous suivi (les indexe) |
| `git commit` | enregistre un instantané dans l'historique |
| `git push` | envoie l'historique vers un remote |

Pas besoin de GitHub ni de GitLab pour pratiquer « push » : un **dépôt bare
local** (`git init --bare`) joue exactement le rôle d'une forge, sur le même
hôte, sans réseau. C'est ce que vous allez monter.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Initialiser** un dépôt Git pour un projet de playbooks (`git init -b main`).
2. **Poser une identité** d'auteur sur le dépôt (`git config user.name/email`).
3. **Suivre et committer** vos playbooks (`git add`, `git commit -m`).
4. **Construire un historique** avec plusieurs commits successifs.
5. **Pousser** vers un remote bare local (`git init --bare`, `git remote add`,
   `git push -u origin main`).

## 🔧 Préparation

Aucune VM. Placez-vous à la racine du repo :

```bash
cd $ANSIBLE_TRAINING
```

Vérifiez que Git est là :

```bash
git --version   # 2.x attendu
```

## 📚 Exercice 1 — Initialiser un dépôt

Créez un dossier de projet et initialisez-y un dépôt sur la branche `main` :

```bash
mkdir -p /tmp/mes-playbooks && cd /tmp/mes-playbooks
git init -b main
git status
```

🔍 **Observation** : `git status` annonce « No commits yet » et liste vos
fichiers comme *untracked*. Le dossier `.git/` vient d'apparaître : c'est le
dépôt.

## 📚 Exercice 2 — Poser une identité

Git refuse de committer sans savoir qui vous êtes. Posez une identité **locale**
à ce dépôt :

```bash
git config user.name "Votre Nom"
git config user.email "vous@exemple.fr"
```

🔍 **Observation** : `--local` (le défaut ici) écrit dans `.git/config`. Cette
identité ne vaut que pour ce dépôt, indépendamment de votre config globale.

## 📚 Exercice 3 — Suivre et committer

Écrivez un premier playbook, indexez-le, committez :

```bash
cat > site.yml <<'EOF'
---
- name: Point d entree
  hosts: all
  tasks:
    - name: Ping
      ansible.builtin.ping:
EOF

git add site.yml
git commit -m "Projet Ansible initial"
git log --oneline
```

🔍 **Observation** : `git add` fait passer `site.yml` de *untracked* à *staged*,
`git commit` l'enregistre. `git log` montre désormais un commit.

## 📚 Exercice 4 — Construire un historique

Ajoutez un second playbook et committez-le séparément :

```bash
cat > webserver.yml <<'EOF'
---
- name: Deployer le serveur web
  hosts: web
  tasks:
    - name: Installer httpd
      ansible.builtin.package:
        name: httpd
        state: present
EOF

git add webserver.yml
git commit -m "Ajout du playbook webserver"
git log --oneline
```

🔍 **Observation** : deux commits, du plus récent au plus ancien. C'est
l'historique. Chaque commit est un instantané complet, pas une simple diff.

## 📚 Exercice 5 — Pousser vers un remote bare local

Pas de forge sous la main ? Un dépôt **bare** en tient lieu :

```bash
git init --bare -b main /tmp/mes-playbooks.git
git remote add origin /tmp/mes-playbooks.git
git push -u origin main
git ls-remote /tmp/mes-playbooks.git
```

🔍 **Observation** : `git ls-remote` affiche `refs/heads/main` pointant sur le
**même SHA** que votre `git rev-parse HEAD` local. Le push a bien transféré
l'historique. Un dépôt bare n'a pas d'arbre de travail : c'est normal, il ne
sert qu'à recevoir des commits.

## 🔍 Observations à noter

- `git init` ne crée **rien d'autre** que le dossier `.git/` : vos fichiers ne
  sont suivis qu'après un `git add`.
- Un fichier oublié au commit reste visible dans `git status` : un arbre
  « propre » (`git status --porcelain` vide) est la preuve que tout est enregistré.
- Un dépôt bare est la bonne cible d'un `push` : le pousser en local prouve le
  geste sans dépendre du réseau. En production, l'`origin` serait une URL
  `https://` ou `git@`, mais la mécanique est identique.

## 🤔 Questions de réflexion

1. Pourquoi Git refuse-t-il de committer tant que `user.email` n'est pas posé ?
2. Quelle différence entre un dépôt bare et un dépôt normal, et pourquoi une
   forge sert-elle toujours des dépôts bare ?
3. Vous committez un `.retry` d'Ansible par erreur. Comment l'empêcher à
   l'avenir, et pourquoi versionner un `.gitignore` ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'écrire un
`solution.sh` qui **automatise** tout le cycle : init, identité, add, deux
commits, puis push vers un bare local. Les tests inspectent l'**état réel** du
dépôt produit.

```bash
pytest -v labs/pratiques/versionner-git/challenge/tests/
```
