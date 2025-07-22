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

* **Phase 1** : le fichier de template doit afficher au minimum :
  * Le nom de la machine (`ansible_facts.hostname`)
  * Le système d'exploitation (`ansible_facts.distribution`,
    `ansible_facts.distribution_version`)
  * Le temps de fonctionnement (`ansible_facts.uptime_seconds`)
  * La mémoire totale (`ansible_facts.memtotal_mb`)
  * Le nombre de CPU (`ansible_facts.processor_cores`) et leur type
    (`ansible_facts.processor[0]`)

* **Phase 2** : le playbook doit respecter les étapes suivantes :
  * Le répertoire `/var/www/monsite` doit être créé à l'aide du module `file`
  * Le répertoire doit être propriété de `www-data:www-data` et avoir les droits `0755`
  * Le fichier `index.html` doit être copié à l'aide du module `template`
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

### Phase 1

Les tests automatiques vérifient que :

* Le template `index.html.j2` existe
* Il contient bien les données dynamiques attendues

Lancez les tests avec :

```bash
pytest -v challenge/tests/test_indexhtml.py
```

Vous devriez voir un rapport indiquant que tous les tests passent.

```bash
=== test session starts ===
platform linux -- Python 3.12.3, pytest-8.4.0, pluggy-1.6.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/perso/ansible-training/04-Templates
plugins: testinfra-10.2.2
collected 1 item

challenge/tests/test_indexhtml.py::test_template_contains_required_facts PASSED                                                      [100%]

=== 1 passed in 0.01s ===
```

### Phase 2

Les tests automatiques vérifient la phase 1 :

* Le template `index.html.j2` existe
* Il contient bien les données dynamiques attendues

Les tests automatiques vérifient ensuite la phase 2 :

* Le répertoire `/var/www/monsite` existe.
* Le répertoire est bien un dossier.
* Le répertoire appartient à l'utilisateur `www-data`.
* Le répertoire appartient au groupe `www-data`.
* Les droits sur le répertoire sont bien `0755`
* Le fichier `/var/www/monsite/index.html` existe.
* Le fichier est bien de type `fichier`.
* Le fichier appartient à l'utilisateur `root`.
* Le fichier appartient au groupe `root`.
* Les droits sur Le fichier sont bien `0644`

Lancez les tests avec :

```bash
pytest -v challenge/tests/test_indexhtml_v2.py
```

Vous devriez voir un rapport indiquant que tous les tests passent.

```bash
==================================================================== test session starts =====================================================================
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /home/ansible/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/ansible/ansible-training/04-Templates
plugins: testinfra-10.2.2
collected 5 items

challenge/tests/test_indexhtml.py::test_template_contains_required_facts PASSED                  [ 20%]
challenge/tests/test_indexhtml_v2.py::test_remote_directory_exists PASSED                        [ 40%]
challenge/tests/test_indexhtml_v2.py::test_remote_directory_permissions_and_owner PASSED         [ 60%]
challenge/tests/test_indexhtml_v2.py::test_remote_file_exists PASSED                             [ 80%]
challenge/tests/test_indexhtml_v2.py::test_remote_file_permissions_and_owner PASSED              [100%]

=== 5 passed in 2.90s ===
```

**Attention** : Assurez-vous que le service `ssh` est en cours d'exécution
sur la machine webserver1, et que vous avez accès à la machine via SSH avec une clé
publique. Pour copier votre clé publique, utilisez les commandes suivantes :

```bash
incus exec webserver1 -- mkdir -p /home/admin/.ssh
incus file push ~/.ssh/id_ed25519.pub webserver1/home/admin/.ssh/authorized_keys
```

---

Bonne chance ! 🚀
