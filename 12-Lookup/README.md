# 12 – TP Lookups Ansible : puisez dans l’externe

Bienvenue dans le douzuième TP de la formation Ansible ! Vous allez apprendre à
utiliser les **lookups**, qui permettent de **récupérer des données externes au
playbook** (fichiers, variables d’environnement, résultats de commandes,
APIs...).

---

## 🧠 Lecture recommandée

Avant de commencer, lisez ce guide : [Les lookup
Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/lookup/)

Vous y découvrirez :

* Qu’est-ce qu’un lookup et comment il fonctionne
* Quand l’utiliser (dans tâches, variables, templates)
* Principaux plugins de lookup : `file`, `env`, `password`, `csvfile`, `first_found`, `json`, etc.
* Bonnes pratiques

---

## 🌟 Objectifs du TP

1. Lire un fichier local via `lookup('ansible.builtin.file', ...)`
2. Récupérer une variable d’environnement avec `lookup('ansible.builtin.env', ...)`
3. Générer un mot de passe sécurisé avec `lookup('ansible.builtin.password', ...)`
4. Lister des fichiers selon un pattern avec `lookup('ansible.builtin.fileglob', ...)`
5. Extraire une valeur depuis un CSV avec `lookup('ansible.builtin.csvfile', ...)`
6. Récupérer une clé depuis un JSON avec `lookup('ansible.builtin.json', ...)`
7. Tester la cascade avec `lookup('ansible.builtin.first_found', ...)`
8. Utiliser un lookup dans un template
9. Charger une configuration depuis `vars` via lookup
10. Appliquer les bonnes pratiques

---

## 💧 Étapes

### Exercice 1 – Lire un fichier local

Placez-vous dans le dossier `12-Lookup` :

Commencez par créer le playbook `playbook.yml` :

```yaml
- name: Utiliser les lookups Ansible
  connection: local
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Afficher le README.md local
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.file', './README.md') }}"
```

Exécutez-le avec :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir le contenu du fichier `README.md` s'afficher dans la sortie.

---

### Exercice 2 – Lire une variable d’environnement

Ajoutez le tâche suivante dans votre playbook :

```yaml
    - name: Afficher le contenu d'une variable d'environnement
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.env', 'HOME') }}"
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir le chemin de votre répertoire personnel s'afficher.

---

### Exercice 3 – Générer un mot de passe

Ajoutez la tâche suivante pour générer un mot de passe sécurisé :

```yaml
    - name: Générer un mot de passe de 16 caractères
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.password', '/dev/null length=16') }}"

```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir un mot de passe aléatoire de 16 caractères s'afficher.

---

### Exercice 4 – Lister des fichiers

Ajoutez la tâche suivante pour générer une liste de fichiers de configuration :

```yaml
    - name: Lister les fichiers *.conf
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.fileglob', '/etc/*.conf') }}"
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir une liste des fichiers `.conf` présents dans `/etc`.

---

### Exercice 5 – Extraire dans un CSV

Créez un fichier `data.csv` dans le répertoire courant :

```csv
key,value
foo,123
bar,456
```

Ajoutez la tâche suivante pour extraire la valeur associée à la clé `bar` :

```yaml
    - name: Extraire la valeur de 'bar' dans le CSV
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.csvfile', 'bar', file='data.csv', delimiter=',', col=1, keycol=0) }}"
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir la valeur `456` s'afficher.

---

### Exercice 6 – Lire une clé JSON

Sur la machine ou sera executé le playbook, il faut d'abord installer la libraire jmespath :

```bash
pipx inject ansible jmespath
```

Créez ensuite un fichier `info.json` :

```json
{"app":"MyApp","version":"1.2.3"}
```

Ajoutez la tâche suivante pour lire la version de l'application :

```yaml
    - name: Lire la version
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.file', 'info.json') | from_json | json_query('version') }}"
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir la version `1.2.3` s'afficher.

---

### Exercice 7 – Utiliser `first_found`

Regardez dans le dossier `conf.d` si vous avez des fichiers de configuration.
Vous devriez en avoir au moins un, le fichier `default.cfg`.

Ajoutez la tâche suivante pour trouver le premier fichier de configuration présent :

```yaml
    - name: Trouver le premier fichier de configuration
      ansible.builtin.debug:
        msg: "{{ lookup('ansible.builtin.first_found', files=['conf.d/prod.cfg', 'conf.d/default.cfg']) }}"
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir le chemin du premier fichier trouvé s'afficher, par exemple `conf.d/default.cfg`.

Créez un fichier `conf.d/prod.cfg` vide pour tester le cas où il existe, et
relancez le playbook pour voir le changement. Notez que si les deux fichiers
existent, c'est le premier trouvé qui sera utilisé.

---

### Exercice 8 – Lookup dans un template

Créez un fichier `templates/config.ini.j2` :

```jinja
password = {{ lookup('ansible.builtin.password',  '/dev/null length=16') }}
```

Ajoutez la tâche suivante pour générer un fichier de configuration à partir du template :

```yaml
    - name: Générer un fichier de configuration
      ansible.builtin.template:
        src: config.ini.j2
        dest: /tmp/config.ini
        mode: '0644'
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir le fichier `/tmp/config.ini` créé avec le contenu :

```bash
password = "p3WyONGU07m:MbV9"
```

Le mot de passe sera différent à chaque exécution.

---

### Exercice 9 – Lookup dans `vars:`

Dans le même playbook, ajoutez la section `vars:` avant les tâches :

```yaml
  vars:
    app_data: "{{ lookup('ansible.builtin.csvfile', 'foo', file='data.csv', delimiter=',', col=1, keycol=0) }}"
```

Ajoutez une tâche pour extraire la valeur de `foo` :

```yaml
    - name: Extraire la valeur de 'foo' depuis vars
      ansible.builtin.debug:
        msg: "{{ app_data }}"
```

Relancez le playbook :

```bash
ansible-playbook playbook.yml
```

Vous devriez voir la valeur `123` s'afficher, extraite depuis le CSV via `vars`.

Note: Privilégier les modules (ex: `slurp`) si le fichier est distant

---

## 🧪 Challenge à valider

Voir `challenge/README.md` :

---

## ✅ Compétences acquises

* Utilisation des lookups courants : `file`, `env`, `password`, `fileglob`, `csvfile`, `json`, `first_found`
* Intégration dans tâches, vars, templates

