# 01 – Inventaires Statiques

Bienvenue dans le premier TP pratique de la formation Ansible ! 🌟

---

## 🧠 Rappel et lecture recommandée

Avant de plonger dans la partie pratique, je vous invite à consulter la documentation sur les inventaires Ansible :

🔗 [**Les Inventaires Ansible (fichiers statiques INI/YAML, organisation en groupes, variables...)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/)

Ce contenu explique les points suivants :

* Définition des inventaires : fichiers INI ou YAML listant les hôtes et groupes
* Organisation en groupes, sous-groupes et variables (groupes et hôtes)
* Comparatif des formats INI vs YAML, et bonnes pratiques à suivre

---

## 🌟 Objectif du TP

Ce TP vise à :

1. Créer un inventaire statique local au format INI
2. Utiliser le plugin **local** pour tester Ansible sur la machine de contrôle
3. Vérifier la connectivité et structure de l’inventaire via Ansible
4. Découvrir l'alternative YAML pour déclarer l'inventaire
5. Utiliser un fichier de configuration Ansible (`ansible.cfg`) pour simplifier les appels

---

## ⚙️ Arborescence

Placez-vous dans le dossier :

```
01-Inventaires-Statiques/
├── README.md         ← ce fichier
├── ansible.cfg       ← fichier de configuration Ansible
├── fichiers/
│   ├── hosts.ini     ← fichier d’inventaire INI
│   └── hosts.yml     ← fichier d’inventaire YAML
└── challenge/
    ├── README.md
    └── tests/
        └── test_inventory.py
```

---

## ⚙️ Exercices pratiques

### Exercice 1 : création de l'inventaire (format INI)

Dans `fichiers/hosts.ini`, créez le contenu suivant :

```ini
[local]
localhost ansible_connection=local

[webservers]
web1.local ansible_connection=local
web2.local ansible_connection=local

[webservers:vars]
http_port=8080
```

* Le groupe `[local]` utilisera le plugin `local` pour exécuter les tâches sur la machine elle-même.
* La section `[webservers]` contient deux hôtes, avec une variable de groupe `http_port`.

### Exercice 2 : inspection de l’inventaire (INI)

Exécutez les commandes suivantes :

```bash
ansible-inventory -i fichiers/hosts.ini --list -y
ansible-inventory -i fichiers/hosts.ini --graph
```

👉 Analysez la sortie : les groupes, hôtes et variables doivent être visibles.

### Exercice 3 : test de connectivité (INI)

Testez la connexion via Ansible ad-hoc :

```bash
ansible -i fichiers/hosts.ini all -m ping
ansible -i fichiers/hosts.ini webservers -m ping
```

Vous devriez obtenir une réponse de `pong` pour chaque hôte ciblé.

### Exercice 4 : création de l'inventaire (format YAML)

Dans `fichiers/hosts.yml`, créez le contenu suivant :

```yaml
#fichiers/hosts.yml
---
all:
  children:
    local:
      hosts:
        localhost:
          ansible_connection: local
    webservers:
      hosts:
        web1.local:
          ansible_connection: local
        web2.local:
          ansible_connection: local
      vars:
        http_port: 8080
```

* Ce format utilise une structure hiérarchique et explicite compatible avec le plugin YAML.

### Exercice 5 : inspection et test (YAML)

```bash
ansible-inventory -i fichiers/hosts.yml --list -y
ansible -i fichiers/hosts.yml all -m ping
```

Comparez les résultats avec l'inventaire INI.

### Exercice 6 : utilisation du fichier de configuration `ansible.cfg`

🔗 [Lire la documentation sur la configuration Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/configuration/)

Dans `ansible.cfg` à la **racine du TP**, ajoutez le contenu suivant :

```ini
[defaults]
inventory = fichiers/hosts.ini
```

Ensuite, vous pouvez exécuter les commandes **sans préciser `-i`** :

```bash
ansible all -m ping
ansible-inventory --list -y
```

Vous pouvez ainsi centraliser les paramètres Ansible pour simplifier tous vos appels.

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour les consignes du challenge final, incluant des tests automatisés avec `pytest` et `testinfra`.

---

Bonne automatisation ! 🚀
