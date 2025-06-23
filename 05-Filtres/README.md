# 04 – TP Progressif : Filtres Jinja avec Ansible

Bienvenue dans ce TP Ansible où vous allez apprendre à utiliser les **filtres
Jinja** de manière progressive à travers plusieurs exercices. L'objectif est de
générer dynamiquement un fichier de configuration `/etc/myapp/config.ini` à
partir de variables, tout en les manipulant avec des filtres.

---

## 📚 Contexte

Vous déployez une application nommée **MyApp** sur un hôte cible. Cette
application utilise un fichier de configuration de type INI contenant plusieurs
paramètres : port, environnement, debug, modules, chemins, etc.

Nous allons construire un playbook `playbook.yml` et un template Jinja2
`config.ini.j2` que nous ferons évoluer à chaque exercice.

---

## ⚙️ Préparation

### Lancer un conteneur Ubuntu avec Incus :

```bash
incus launch images:ubuntu/24.04/cloud myhost --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

---

## 🎓 Exercice 1 – Templates et Playbook sans aucun filtre

Créez un fichier `templates/config.ini.j2` :

```jinja
[server]
port = {{ app_port }}
debug = {{ debug }}

[application]
environment = {{ app_environment }}
modules = {{ modules }}
```

Et le playbook minimal :

```yaml
- name: Exemple de playbook avec filtres Jinja2
  hosts: myhost
  connection: community.general.incus
  vars:
    app_port: 8080
    debug: true
    app_environment: production
    modules: ['auth', 'web', 'api']
    mode: '0755'
  tasks:
    - name: Générer le fichier de conf
      ansible.builtin.template:
        src: templates/config.ini.j2
        dest: /tmp/config.ini
        mode: "{{ mode }}"
        owner: root
        group: root
```

Exécutez le playbook :

```bash
ansible-playbook playbook.yml -i myhost,
```

Vérifiez le contenu du fichier `/tmp/config.ini` sur le conteneur :

```bash
incus exec myhost -- cat /tmp/config.ini
```

---

## ✨ Exercice 2 – Ajouter des valeurs par défaut

Remplacez `app_port` dans le template `config.ini.j2` par une valeur par défaut
si elle n'est pas définie :

```jinja
port = {{ app_port | default(8080) }}
```

Dans le playbook, supprimez `app_port` du `vars:`.

Re-exécutez le playbook et vérifiez que le port est bien défini à 8080 par
défaut.

---

## ✉️ Exercice 3 – Variables facultatives avec `omit`

Dans le playbook:

1. Commentez la ligne `mode: '0644'` dans `vars:`.
2. Dans la tache de template, utilisez `| default(omit)` pour ignorer le mode si
   non défini :

  ```yaml
  mode: {{ mode | default(omit) }}
  ```

Re-exécutez le playbook et vérifiez les permissions du fichier.

```bash
ansible-playbook playbook.yml -i myhost,
incus exec myhost -- ls -l /tmp/config.ini
```

---

## ⛔️ Exercice 4 – Rendre `environment` obligatoire

1. Dans le playbook, commentez `environment: production` dans `vars:`.
2. Dans le template `config.ini.j2`, utilisez le filtre `mandatory` :

  ```jinja
  environment = {{ environment | mandatory }}
  ```

3. Exécutez le playbook. Vous devriez obtenir une erreur indiquant que `environment`
   est obligatoire.
4. Décommentez `environment: production` dans `vars:` et réexécutez le playbook.

---

## 🔄 Exercice 5 – Forcer les types

1. Dans la section `vars:` du playbook mettez `port: "8080"` (chaîne).

Dans le template :

```jinja
port = {{ port | default(8080) | int }}
```

Ajoutez aussi :

```jinja
debug = {{ debug | default(false) | bool }}
```

---

## 📃 Exercice 6 – Travailler avec les listes

Dans le template :

```jinja
modules = {{ modules | join(',') }}
```

Et essayez de relancer le playbook. Vous devriez voir un changement dans
`/tmp/config.ini`.

```ini
modules = auth,web,api
```

---

## 🔑 Exercice 7 – Manipuler les dictionnaires

Ajoutez `tags:` dans `vars:` :

```yaml
tags:
  owner: devops
  service: myapp
```

Dans le template :

```jinja
{% for tag in tags | dict2items %}
tag_{{ tag.key }} = {{ tag.value }}
{% endfor %}
```

Cela va générer des lignes comme :

```ini
tag_owner = devops
tag_service = myapp
```

---

## 🔢 Exercice 8 – Export YAML avec `to_nice_yaml`

Ajoutez une tâche pour générer le YAML des variables :

```yaml
- name: Sauvegarder les variables YAML
  ansible.builtin.copy:
    content: "{{ vars | to_nice_yaml(indent=2) }}"
    dest: /tmp/variables.yaml
    mode: '0644'
    owner: root
    group: root
```

Exécutez le playbook et vérifiez le contenu de `/tmp/variables.yaml` :

```bash
incus exec myhost -- cat /tmp/variables.yaml
```

Vous devriez voir toutes les variables Ansible formatées en YAML.

---

## 🧪 Challenge à valider

Voir `challenge/README.md` : exporter la configuration en YAML et vérifier
qu'elle contient bien `modules` avec au moins 2 éléments uniques, un `port` >
1024 et un champ `debug` de type booléen.

---

## ✅ Compétences acquises

* Application progressive des filtres Jinja
* Manipulation de types, listes, dictionnaires
* Production de templates robustes, adaptatifs et lisibles

---

🚀 En route vers le TP 05 : Templates Jinja avancés !
