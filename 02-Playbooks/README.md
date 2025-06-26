# 02 – Écriture de Playbooks Ansible

Bienvenue dans le deuxième TP de la formation Ansible !

---

## 🧠 Rappel et lecture recommandée

Avant de commencer, je vous invite à lire :

* ce guide complet sur la rédaction, l’exécution et le débogage de playbooks
Ansible : 🔗 [Écriture de playbooks Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecriture-de-playbooks-ansible/)
* ce guide sur [la création et l'utilsations des variables](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/variables/)
* ce guide sur les présentations des principaux modules Ansible : 🔗 [Modules Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/)

Ces guide couvrent :

* la structure YAML d’un playbook
* les principaux modules, les variables, les conditionnels
* l’utilisation de `--check`, `-vvv`, `ansible-console` pour du debug avancé

---

## 🌟 Objectifs du TP

1. Structurer un playbook YAML minimum
2. Installer un paquet et gérer un service sur l’hôte `localhost`
3. Utiliser variables et conditions (`when`)
4. Apprendre les bases du debug avec `--check` et verbosité

---

## 📁 Arborescence

```bash
02-Playbooks/
├── README.md          ← ce fichier
├── playbook.yml       ← votre playbook principal
├── fichiers/
│   └── sample.txt     ← fichier à copier (optionnel)
└── challenge/
    ├── README.md
    └── tests/
        └── test_playbook.py
```

---

## ⚙️ Exercices pratiques

### Exercice 1 : Création d’un playbook minimal

Créez à la racine du TP le fichier `playbook.yml` contenant :

```yaml
---
- name: TP - Manipulation de fichiers simples
  hosts: localhost
  connection: local
  become: false
  vars:
    target_path: /tmp/sample_copie.txt
    user_owner: "{{ lookup('env','USER') }}"
  tasks:
    - name: Copier un fichier dans /tmp
      ansible.builtin.copy:
        src: fichiers/sample.txt
        dest: "{{ target_path }}"
        owner: "{{ user_owner }}"
        group: "{{ user_owner }}"
        mode: '0644'

    - name: Ajouter une ligne à la fin du fichier copié
      ansible.builtin.lineinfile:
        path: "{{ target_path }}"
        line: "# Ligne ajoutée par Ansible"
        create: true
        owner: "{{ user_owner }}"
        group: "{{ user_owner }}"
        mode: '0644'

    - name: Lire le contenu du fichier copié
      ansible.builtin.slurp:
        src: "{{ target_path }}"
      register: file_content

    - name: Afficher le contenu du fichier
      ansible.builtin.debug:
        msg: "{{ file_content.content | b64decode }}"
```

Ce playbook effectue les actions suivantes :

1. Copie avec le module [`copy`](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/gestion-fichiers/#le-module-ansible-copy) le fichier `fichiers/sample.txt` dans `/tmp/sample_copie.txt`
2. Ajoute une ligne à la fin du fichier copié avec le module [`lineinfile`](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/gestion-fichiers/#le-module-ansible-lineinfile) si le fichier n'existe pas, il le crée
3. Lit le contenu du fichier copié avec le module [`slurp`](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/gestion-fichiers/#le-module-ansible-slurp) et l'affiche dans la sortie avec le module [`debug`](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/debug/).

### Exercice 2 : Simulation avec `--check`

Lancez la commande suivante pour simuler l’exécution du playbook sans apporter de modifications réelles : :

```bash
ansible-playbook playbook.yml --check
```

### Exercice 3 : Exécution réelle

Lancez la commande suivante pour exécuter réellement le playbook :

```bash
ansible-playbook playbook.yml
```

Vérifiez que le fichier `sample.txt` a bien été copié dans `/tmp/sample_copie.txt` et que la ligne a été ajoutée.

## 🧪 Challenge à valider

Voir `challenge/README.md`.

---

Bonne écriture de playbooks ! 🚀
