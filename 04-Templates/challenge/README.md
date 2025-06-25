# Challenge : Génération du fichier index.html avec un template Jinja2

Dans ce challenge, vous allez créer un **template Jinja2** permettant de générer
dynamiquement un fichier `index.html` affichant les caractéristiques de la
machine cible (hostname, OS, uptime, CPU, RAM, etc.). Ce fichier sera déployé
dans le dossier `/var/www/monsite`.

---

## 📊 Objectif

* Créer un template `index.html.j2` dans `templates/`
* Utiliser les facts Ansible pour afficher les informations du système
* Déployer le fichier `index.html` dans `/var/www/monsite`

---

## 🔹 Contraintes et consignes

* Le fichier HTML doit afficher au minimum :

  * Le nom de la machine (`ansible_facts.hostname`)
  * Le système d'exploitation (`ansible_facts.distribution`,
    `ansible_facts.distribution_version`)
  * Le temps de fonctionnement (`ansible_facts.uptime_seconds`)
  * La mémoire totale (`ansible_facts.memtotal_mb`)
  * Le nombre de CPU (`ansible_facts.processor_cores`) et leur type
    (`ansible_facts.processor[0]`)
* Le fichier `index.html` doit être copié à l'aide du module `template`
* Le répertoire `/var/www/monsite` doit exister et avoir les droits `0755`
* Le fichier doit être propriété de `root:root` avec les droits `0644`

Exemple de contenu attendu dans `index.html` :

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Informations système</title>
</head>
<body>
  <h1>Bienvenue sur webserver1</h1>
  <ul>
    <li><strong>OS :</strong> Ubuntu 24.04</li>
    <li><strong>Uptime :</strong> 0 heures</li>
    <li><strong>Mémoire totale :</strong> 15706 MB</li>
    <li><strong>Nombre de CPU :</strong> 7 cœurs (0)</li>
  </ul>
</body>
</html>
```

## 🧰 Validation du challenge

Les tests automatiques vérifient que :

* Le template `index.html.j2` existe
* Il contient bien les données dynamiques attendues

Lancez les tests avec :

```bash
pytest -v
```

Vous devriez voir un rapport indiquant que tous les tests passent.

```bash
=== test session starts ===
platform linux -- Python 3.12.3, pytest-8.4.0, pluggy-1.6.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/perso/ansible-training/03-Templates
plugins: testinfra-10.2.2
collected 1 item

challenge/tests/test_indexhtml.py::test_template_contains_required_facts PASSED                                                      [100%]

=== 1 passed in 0.01s ===
```

Bonne chance ! 🚀
