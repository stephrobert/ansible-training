# 06 – Utilisation des Conditions (`when`) avec Ansible

Bienvenue dans le sixième TP de la formation Ansible ! Ce TP vous apprendra à
**contrôler l'exécution des tâches en fonction de conditions**. C’est une
fonctionnalité essentielle pour rendre vos playbooks dynamiques et adaptés à
différents environnements.

---

## 🧠 Lecture recommandée

Avant de commencer, je vous recommande de lire cette section du guide : 🔗
[Conditions Ansible
(`when`)](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecriture-de-playbooks-ansible/#utilisations-des-conditions-dansible-when)

Vous y apprendrez :

* Comment utiliser la directive `when`
* Comment tester des variables, des faits (facts), ou des expressions logiques
* Comment combiner des conditions avec `and`, `or`, et `not`

---

## 🎯 Objectifs du TP

1. Utiliser la directive `when` pour exécuter une tâche uniquement si une
   condition est remplie
2. Tester des variables et des faits (facts) système
3. Écrire une condition complexe avec combinaison de `and` et `or`

---

## ⚙️ Étapes du TP

### Étape 0 : Prérequis

Assurez-vous que vous avez au moins **une machine cible** (locale ou distante).
Pour simplifier, vous pouvez utiliser un conteneur Incus ou une machine
virtuelle Ubuntu.

```bash
incus launch images:ubuntu/24.04/cloud myhost --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus alias add login 'exec @ARGS@ -- su -l admin'
```

### Étape 1 : Créer un playbook avec conditions

Créez le fichier `conditions.yml` :

```yaml
---
- name: TP Conditions - Tester des conditions avec when
  hosts: all
  gather_facts: true
  tasks:

    - name: Afficher le système d'exploitation
      ansible.builtin.debug:
        msg: "Le système est {{ ansible_distribution }} {{ ansible_distribution_version }}"

    - name: Créer un fichier uniquement sur Ubuntu
      ansible.builtin.copy:
        content: "Ce fichier est uniquement créé sur Ubuntu."
        dest: /tmp/ubuntu_only.txt
        mode: "0644"
      when: ansible_distribution == "Ubuntu"
```

Exécutez le playbook :

```bash
ansible-playbook conditions.yml
```

Vérifiez les fichiers créés dans `/tmp/` :

```bash
ls /tmp/ubuntu_only.txt
```

---

### Étape 3 : Ajouter des conditions supplémentaires

Nous allons ajouter des conditions pour vérifier si la distribution est Ubuntu
et si la version d'Ubuntu est supérieure ou égale à 24.04.

```yaml

    - name: Créer un fichier si le système est Ubuntu *et* la version est >= 24.04
      ansible.builtin.copy:
        content: "Ce fichier est créé uniquement si le système est Ubuntu et la version >= 24.04."
        dest: /tmp/ubuntu_24_plus.txt
        mode: "0644"
      when:
        - ansible_distribution == "Ubuntu"
        - ansible_distribution_version is version_compare('24.04', '>=', strict=True)
```

Exécutez le playbook :

```bash
ansible-playbook conditions.yml
```

Vérifiez les fichiers créés dans `/tmp/` :

```bash
ls /tmp/ubuntu_24_plus.txt
```

---

### Étape 4 : Nettoyage

```bash
incus delete myhost --force
```

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : Vous devrez
écrire une condition qui exécute une tâche **uniquement si le système est Red
Hat et que le groupe `developers` existe**. Validez cette logique avec un test
`pytest` + `testinfra`.

---

## ✅ Compétences acquises

* Utilisation de `when` pour conditionner l'exécution des tâches
* Utilisation des faits (facts) système (`ansible_distribution`,
  `ansible_distribution_version`)
* Comparaison de versions avec `version_compare`
* Création de conditions complexes avec `and`, `or`, `not`

---

🚀 En route vers le TP 07 sur **les variables Ansible** et leur gestion avancée
!