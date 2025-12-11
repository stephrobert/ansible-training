# Challenge Ansible : Conditions `when`

Bienvenue dans le challenge final du TP 07 sur l'utilisation des **conditions
avec Ansible**.

Vous allez devoir écrire un playbook qui **exécute une tâche uniquement si deux
conditions sont remplies** sur la machine cible `myhost` (créée via Incus).

---

## 📚 Contexte de test

La machine cible s'appelle `myhost` et doit être lancée avec les commandes suivantes à partir du dossier `/challenge` :

```bash
incus rm myhost --force
incus launch images:ubuntu/24.04/cloud myhost --config=cloud-init.user-data="$(cat ../../cloud-config.yaml)"
incus file push ~/.ssh/id_ed25519.pub myhost/home/admin/.ssh/authorized_keys
```

**Note**:
- Remplacez `~/.ssh/id_ed25519.pub` par le chemin de votre clé publique SSH si vous utilisez une autre clé.
- Une autre solution consiste à réutiliser votre playbook de configuration de ssh de la partie `03-Handlers`.

## 🎓 Objectif

Votre playbook nommé `challenge.yml` devra :

1. Tester vos expressions avant exécution
2. Créer le group `developers` s'il n'existe pas
3. **Créer un fichier `/tmp/flag_condition.txt`** si deux conditions sont
   remplies :
    * Le fact `ansible_distribution` de la vm est **Ubuntu**
    * La tâche de création du groupe `developers` s'est bien exécutée.
  Sinon, le fichier **ne doit pas exister**.

**Note** : Vous pouvez détruire et recréer la machine cible à chaque
exécution du playbook pour vous assurer que les conditions sont bien vérifiées.

## 🧪 Validation automatique

Des tests automatisés sont disponibles.

Ils vérifient que :

* Le fichier `challenge.yml` contient bien les éléments suivants:
  * Une vérification des variables avec `ansible.builtin.debug:`
  * La création du groupe avec `ansible.builtin.group`
  * L'utilisation de `register`pour enregistrer le resultat de l'execution d'une tâche
  * L'utilisation de conditions avec `when`
  * La recherche de `Ubuntu` dans la variable `ansible_distribution`
* Nous sommes bien en présence d'une distribution `Ubuntu`
* Le groupe `developers` existe bien
* Le fichier `/tmp/flag_condition.txt` est bien créé

Lancez la validation avec :

```bash
pytest -v
```

Vous devriez obtenir un résultat similaire à :

```bash
=== test session starts ===
platform linux -- Python 3.10.12, pytest-8.3.5, pluggy-1.5.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/ansible-training/07-Conditions
plugins: testinfra-10.2.2
collected 4 items

challenge/tests/test_conditions.py::test_local_challenge_contains_required_facts PASSED       [ 25%]
challenge/tests/test_conditions.py::test_remote_distribution PASSED                           [ 50%]
challenge/tests/test_conditions.py::test_remote_group_exists PASSED                           [ 75%]
challenge/tests/test_conditions.py::test_remote_file_exists PASSED                            [100%]

=== 4 passed in 1.24s ===
```

## ✅ Conseils

* Utilisez un `ansible.builtin.debug:` pour tester vos expressions avant exécution
* Utilisez le module `ansible.builtin.group:` pour créer le groupe `developers`
* Utilisez `register:` pour définir une variable qui va stocker le résultat de la tache
* Utilisez `when:` avec une condition combinée (et logique)

---

Bonne chance ! 🎉

<details>
  <summary>Cliquer pour de l'aide supplémentaire</summary>
  
  #### Ressource supplémentaire :
  
  - 🔗 [Aide Ansible - conditions pour les variables enregistrées](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_conditionals.html#conditions-based-on-registered-variables)

* Utilisez `register:` pour définir une variable qui va stocker le résultat de la tâche.
* Dans la clause `when:` controler la distribution **et** vérifier que la tache s'est bien exécutée grace à cette variable.
* La clause `is succeeded` peut servir a vérifier que la tâche s'est bien déroulée.

</details>
