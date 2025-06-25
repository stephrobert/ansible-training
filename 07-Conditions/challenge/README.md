# Challenge Ansible : Conditions `when`

Bienvenue dans le challenge final du TP 07 sur l'utilisation des **conditions
avec Ansible**.

Vous allez devoir écrire un playbook qui **exécute une tâche uniquement si deux
conditions sont remplies** sur la machine cible `myhost` (créée via Incus).

---

## 📚 Contexte de test

La machine cible s'appelle `myhost` et doit être lancée avec la commande suivante :

```bash
incus rm myhost --force
incus launch images:ubuntu/24.04/cloud myhost --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus file push ~/.ssh/id_ed25519.pub myhost/home/admin/.ssh/authorized_keys
```

**Note**: Remplacez `~/.ssh/id_ed25519.pub` par le chemin de votre clé publique SSH si
vous utilisez une autre clé.

## 🎓 Objectif

Votre playbook nommé `challenge.yml` devra :

1. Créer le group `developers` s'il n'existe pas
2. Installer le serveur ssh sur la machine cible
   (utilisez le module `ansible.builtin.package` avec `name: openssh-server`)
3. **Créer un fichier `/tmp/flag_condition.txt`** si deux conditions sont
   remplies :
    * Le fact `ansible_os_family` de la vm est **Debian**
    * Le groupe `developers` existe
  Sinon, le fichier **ne doit pas exister**.

**Note** : Vous pouvez détruire et recréer la machine cible à chaque
exécution du playbook pour vous assurer que les conditions sont bien vérifiées.

## 🧪 Validation automatique

Des tests automatisés sont disponibles.

Ils vérifient que :

* Que nous sommes bien en présence d'une distribution Ubuntu
* Le fichier est bien créé

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
collected 3 items

challenge/tests/test_conditions.py::test_file_exists PASSED       [ 33%]
challenge/tests/test_conditions.py::test_distribution PASSED      [ 66%]
challenge/tests/test_conditions.py::test_group_exists PASSED      [100%]

=== 3 passed in 0.85s ===
```

## ✅ Conseils

* Utilisez le module `ansible.builtin.group` pour créer le groupe `developers`
* Utilisez la commande `getent` pour vérifier la présence du groupe
* Ajoutez un `debug:` pour tester vos expressions avant exécution
* Utilisez `when:` avec une condition combinée (et logique)

---

Bonne chance ! 🎉
