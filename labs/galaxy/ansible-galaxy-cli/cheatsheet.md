# ansible-galaxy CLI — cheatsheet 2026

Commandes essentielles à connaître pour le RHCE EX294 et au quotidien.

## Initialisation

```bash
# Créer un rôle vide avec la structure standard
ansible-galaxy role init nginx

# Créer dans un dossier spécifique
ansible-galaxy role init --init-path roles/ nginx

# Créer une collection
ansible-galaxy collection init stephrobert.networking
```

## Recherche

```bash
# Rechercher un rôle sur Galaxy
ansible-galaxy search nginx --author geerlingguy

# Info détaillée d'un rôle
ansible-galaxy info geerlingguy.nginx
```

## Installation

```bash
# Rôle depuis Galaxy
ansible-galaxy role install geerlingguy.nginx

# Rôle depuis Git (avec branche/tag)
ansible-galaxy role install git+https://github.com/geerlingguy/ansible-role-nginx.git,master

# Depuis requirements.yml
ansible-galaxy role install -r requirements.yml
ansible-galaxy collection install -r requirements.yml
```

## Listing

```bash
# Lister tous les rôles installés
ansible-galaxy role list

# Lister les collections installées
ansible-galaxy collection list

# Filtrer par namespace
ansible-galaxy collection list community.general
```

## Suppression

```bash
ansible-galaxy role remove geerlingguy.nginx
```

## Publication

```bash
# Build une collection (génère .tar.gz)
ansible-galaxy collection build

# Publier sur Galaxy avec un token API
ansible-galaxy collection publish stephrobert-networking-1.0.0.tar.gz --api-key=$GALAXY_TOKEN
```

## Vérification

```bash
# Vérifier l'intégrité d'une collection installée vs Galaxy
ansible-galaxy collection verify community.general
```
