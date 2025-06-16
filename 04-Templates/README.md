# 04 - Templates Jinja2 avec Ansible

Bienvenue dans le quatrième TP de la formation Ansible 🚀

---

## 🧠 Rappel et lecture recommandée

Avant de démarrer, consultez ce guide complet pour comprendre l’utilisation des templates Jinja dans Ansible :
🔗 [Utiliser Jinja avec Ansible (guide Stéphane Robert)](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/templates-jinja/)

Ce guide couvre notamment :

* Le module `template` pour générer des fichiers de configuration dynamiques
* La syntaxe Jinja2 : variables, filtres, boucles, conditions
* La gestion des permissions, propriétaires, et sensibilité des fichiers (`mode`, `owner`, `group`)
* Bonnes pratiques et sécurisation des templates

---

## 🌟 Objectifs du TP

1. Créer un template Jinja (`.j2`) utilisant variables, boucles ou conditions
2. Déployer un fichier de configuration depuis ce template
3. Appliquer les bons droits au fichier généré
4. Utiliser les filtres Jinja pour formater ou sécuriser les contenus
5. Tester avec un premier playbook simple et réutilisable

---

## 📁 Arborescence

```bash
03-Templates/
├── README.md           ← ce fichier
├── templates/
│   └── motd.j2         ← template Jinja à créer
├── playbook.yml        ← playbook principal
└── challenge/
    ├── README.md
    └── tests/
        └── test_templates.py
```

---

## ⚙️ Exercice : Génération d’un fichier `motd` personnalisé

### Etape 0 : Prérequis

Commençons par créer un conteneur Incus pour ce TP. Assurez-vous d’avoir
installé Incus comme indiqué dans le README à la racine du projet.

```bash
incus launch images:ubuntu/24.04/cloud webserver1  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus alias add login 'exec @ARGS@ -- su -l admin'
```

### Étape 1 : Créer un template

Commencez par créer un fichier `apache_vhost.conf.j2` dans le dossier
`templates/` avec le contenu suivant :

```plaintext
<VirtualHost *:80>
    ServerAdmin {{ server_admin | default('webmaster@localhost') }}
    ServerName {{ server_name }}
    ServerAlias www.{{ server_name }}

    DocumentRoot {{ document_root }}

    <Directory {{ document_root }}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/{{ server_name }}_error.log
    CustomLog ${APACHE_LOG_DIR}/{{ server_name }}_access.log combined
</VirtualHost>
```

### Étape 2 : Rédiger un playbook

Créer un fichier `template.yml` à la racine du dossier `03-Templates/` avec le contenu suivant :

```yaml
- name: Déployer un virtualhost Apache
  hosts: tp
  connection: community.general.incus
  vars:
    server_name: monsite.local
    document_root: /var/www/monsite
  tasks:
    - name: Installer Apache
      become: true
      ansible.builtin.apt:
        update_cache: true

    - name: Installer les modules Apache nécessaires
      become: true
      ansible.builtin.apt:
        name:
          - apache2
          - libapache2-mod-wsgi-py3
          - python3-pip
        state: present

    - name: Créer le dossier du site
      become: true
      ansible.builtin.file:
        path: "{{ document_root }}"
        state: directory
        mode: '0755'
        owner: www-data
        group: www-data

    - name: Création d'un fichier index.html
      become: true
      ansible.builtin.copy:
        dest: "{{ document_root }}/index.html"
        content: "<html><body><h1>Bienvenue sur {{ server_name }}</h1></body></html>"
        mode: '0644'
        owner: www-data
        group: www-data

    - name: Générer le fichier de conf Apache
      become: true
      ansible.builtin.template:
        src: templates/apache_vhost.conf.j2
        dest: "/etc/apache2/sites-available/{{ server_name }}.conf"
        mode: '0644'
        owner: root
        group: root

    - name: Activer le site
      become: true
      ansible.builtin.command: a2ensite {{ server_name }}.conf
      notify: Reload Apache

    - name: Ajout du nom de domaine dans /etc/hosts
      become: true
      delegate_to: localhost
      ansible.builtin.lineinfile:
        path: /etc/hosts
        line: "{{ ansible_default_ipv4.address }} {{ server_name }}"
        state: present

  handlers:
    - name: Reload Apache
      become: true
      ansible.builtin.service:
        name: apache2
        state: reloaded
```

Quelques explications sur le playbook :

* **hosts** : Cible le conteneur `webserver1` créé précédemment.
* **Connection** : Utilisation de `community.general.incus` pour se connecter à des conteneurs Incus.
* **Tasks** :
  * Installation d'Apache et des packages nécessaires.
  * Création du dossier racine du site avec les permissions appropriées.
  * Création d'un fichier `index.html` de test dans le dossier du site.
  * Génération du fichier de configuration Apache à partir du template `apache_vhost.conf.j2`.
  * Ajout du nom de domaine dans `/etc/hosts` pour la résolution locale.
  * Activation du site et rechargement d'Apache via un handler.

**Remarque** : La tache de création de la ligne dans `/etc/hosts` est déléguée à
`localhost` pour lancer le test depuis votre machine hôte.

### Étape 3 : Exécution du playbook

Avant d'exécuter le playbook, assurez-vous que le conteneur Incus est en cours d'exécution. Vous pouvez vérifier son état avec :

```bash
incus list
```

Ensuite, exécutez le playbook avec la commande suivante :

```bash
ansible-playbook template.yml -i webserver1,
```

Lancez la commande suivante pour vérifier que la configuration a été appliquée correctement :

```bash
curl monsite.local
```

Vous devriez voir le message "Bienvenue sur monsite.local" s'afficher dans votre
navigateur ou en ligne de commande.

```bash
<html><body><h1>Bienvenue sur monsite.local</h1></body></html>
```

### Etape 4 : nettoyage

Après avoir terminé le challenge, vous pouvez nettoyer le conteneur incus pour éviter les
conflits futurs :

```bash
incus delete webserver1 --force
```

---

## 🧪 Challenge

Vous pouvez maintenant vous attaquer au challenge proposé dans le fichier `challenge/README.md`.

---


Ce TP est un excellent pont vers l’écriture de rôles (TP04) et la gestion avancée des configurations !

Bonne création de templates ! 🎨
