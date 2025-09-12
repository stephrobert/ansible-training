# 🎯 Challenge - Bloc d’instructions dans un fichier

Dans ce challenge, vous allez prouver votre capacité à manipuler un fichier
texte à l’aide d’un **playbook Ansible** en utilisant notamment le module
`blockinfile`.

---

## ✅ Objectif

Votre playbook doit :

1. Créer un fichier `/tmp/config_ansible.txt` s’il n’existe pas
2. Ajouter un bloc de texte bien délimité contenant des paramètres de
   configuration fictifs
3. S’assurer que ce bloc est idempotent (aucune modification à la deuxième
   exécution)
4. Appliquer les permissions `0600` à ce fichier et s’assurer que son
   propriétaire est l’utilisateur courant

---

## 📄 Bloc attendu

Le bloc ajouté doit être exactement comme ceci :

```plaintext
# BEGIN ANSIBLE MANAGED BLOCK
param1 = valeur1
param2 = valeur2
# END ANSIBLE MANAGED BLOCK
```

Utilisez les paramètres par défaut du module `blockinfile` pour cela.

---

## 🧩 Consignes

1. Le playbook doit s’appeler `playbook2.yml`
2. Il doit utiliser le module `blockinfile` pour insérer le bloc
3. Le fichier `/tmp/config_ansible.txt` doit appartenir à l’utilisateur courant et avoir les permissions `0600`
4. Il ne doit pas dépendre des exercices précédents

---

## 🧪 Validation

Pour valider votre playbook, exécutez-le et lancez ensuite les tests avec la
commande suivante :

```bash
pytest -v
```
Assurez-vous d’avoir installé python3-testinfra pour pouvoir utiliser la commande ci-dessus.

Pour l’installer, voici les commandes dont vous avez besoin :           

```bash
sudo apt update
```

```bash
sudo apt install -y python3-testinfra
```


Résultat attendu :

```bash
=== test session starts ===
platform linux -- Python 3.10.12, pytest-8.3.5, pluggy-1.5.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/ansible-training/02-Playbooks
plugins: testinfra-10.2.2
collected 3 items

challenge/tests/test_playbook.py::test_file_exists[local] PASSED                                         [ 33%]
challenge/tests/test_playbook.py::test_file_content[local] PASSED                                        [ 66%]
challenge/tests/test_playbook.py::test_file_permissions_and_owner[local] PASSED                          [100%]

=== 3 passed in 0.02s ===
```

Bonne rédaction de playbook ! Et pensez à tester l’idempotence ! 🚀
