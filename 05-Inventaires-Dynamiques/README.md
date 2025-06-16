# 05 – Inventaires dynamiques avec Ansible

Bienvenue dans le cinquième TP de la formation Ansible ! Ce TP vous initie à
l’utilisation des **inventaires dynamiques**, un mécanisme permettant à Ansible
de découvrir automatiquement les hôtes à gérer, sans avoir à les lister dans un
fichier d'inventaire.

---

## 🧠 Lecture recommandée

Avant de commencer, je vous recommande de lire cette section du guide : 🔗
[Inventaires dynamiques](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/#activation-des-plugins-dinventaire-dynamique)

Vous y apprendrez :

* Ce qu’est un plugin d’inventaire dynamique
* Comment les configurer
* Comment ils s’intègrent dans les workflows Ansible

---

## 🎯 Objectifs du TP

1. Configurer un inventaire dynamique basé sur les conteneurs Incus
2. Lister dynamiquement les hôtes disponibles
3. Exécuter un playbook simple sur ces hôtes

---

## 📁 Arborescence

```bash
05-Inventaires-Dynamiques/
├── README.md
├── ansible.cfg
├── incus.yaml
├── playbook.yml
└── challenge/
    ├── README.md
    └── tests/
        └── test_inventory.py
```

---

## ⚙️ Étapes du TP

### Étape 0 : Préparation de l’environnement

Installez la collection Incus :

```bash
ansible-galaxy collection install git+https://github.com/kmpm/ansible-collection-incus.git
```

Lancez quelques conteneurs si nécessaire :

```bash
incus launch images:debian/12/cloud web01  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:debian/12/cloud db01  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

### Étape 1 : Configuration d’Ansible

Commencez par créer le fichier d'inventaire dynamique `incus.yml` dans le
répertoire `05-Inventaires-Dynamiques/` avec le contenu suivant :

```yaml
plugin: kmpm.incus.incus
```

Testons que le plugin est bien installé en exécutant :

```bash
ansible-inventory -i incus.yml --list
```

Pour éviter de devoir spécifier l'inventaire à chaque commande, nous allons
configurer Ansible pour utiliser cet inventaire dynamique par défaut. Pour cela,
créez un fichier `ansible.cfg` dans le même répertoire avec le contenu suivant :

```ini
[defaults]
inventory = ./incus_inventory.yaml
host_key_checking = False
retry_files_enabled = False
interpreter_python = auto_silent
```

Testons que tout fonctionne correctement en utilisant la commande
adhoc pour ping les hôtes :

```bash
ansible all -m ansible.builtin.ping
```

Vous devriez voir une réponse de type `pong` pour chaque conteneur Incus en cours
d’exécution.

```bash
web01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.11"
    },
    "changed": false,
    "ping": "pong"
}
db01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.11"
    },
    "changed": false,
    "ping": "pong"
}
```

## Étape 2 : Création des groupes d’hôtes

Pour organiser les hôtes, nous allons créer des groupes dans notre inventaire
dynamique.

Pour obtenir de la documentation sur les options de groupement, vous pouvez
consulter la documentation du plugin.

```bash
ansible-doc -t inventory kmpm.incus.incus
```

Modifiez le fichier `incus.yml` pour y ajouter des groupes avec le code suivant
:

```yaml
---
plugin: kmpm.incus.incus
groupby:
  debian:
    type: os
    attribute: Debian
  web:
    type: pattern
    attribute: '^web'
  deb:
    type: pattern
    attribute: '^db'
```

Testez à nouveau l'inventaire avec :

```bash
ansible-inventory -i incus.yml --graph
```

Vous devriez voir une structure d'inventaire avec les groupes `debian`, `web` et
`deb` contenant les hôtes correspondants.

On peut aussi tester les groupes avec la commande adhoc :

```bash
ansible web -m ansible.builtin.ping

web01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.11"
    },
    "changed": false,
    "ping": "pong"
}
```

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : vous devrez
créer un inventaire dynamique filtrant uniquement les conteneurs dont le nom
commence par `web`, et exécuter une tâche sur ceux-ci uniquement. Le test
`test_inventory.py` vérifiera que seuls les bons hôtes sont ciblés.

---

## ✅ Compétences acquises

* Utilisation d’un plugin d’inventaire dynamique
* Intégration d’un plugin externe dans Ansible
* Filtrage dynamique des hôtes

🚀 En route vers le TP 06 sur **l'écriture de rôles** !
