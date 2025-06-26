# Challenge Ansible : Utilisation avancée des blocs imbriqués avec fail2ban

Bienvenue dans le challenge final du TP 09. Cette fois, vous allez devoir écrire
un **playbook Ansible** (et non un rôle) mettant en œuvre des **blocs (`block`)
imbriqués**, avec gestion d’erreurs, déclenchement de handlers, et configuration
de sécurité réelle.

---

## 🔧 Environnement

Lancez quelques conteneurs incus si nécessaire :

```bash
incus launch images:debian/12/cloud server1  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:almalinux/9/cloud server2  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

Lancez le playbook de base pour configurer les conteneurs :

```bash
ansible-playbook init.yml
```

**Note** : Attention, attendez que les conteneurs soient en ligne avant de lancer le playbook. Pour vérifier, utilisez :

```bash
incus exec <nom_du_conteneur> -- cloud-init status
```

---

## 🎓 Objectif

Rédigez un playbook Ansible nommé `block.yml` qui :

1. Copie votre clé publique SSH dans le fichier `/home/admin/.ssh/authorized_keys` pour permettre l'accès root via SSH.
2. Copie le fichier de configuration `/etc/fail2ban/jail.conf` vers `/etc/fail2ban/jail.local`.
3. Modifie la ligne `backend = %(sshd_backend)s` du fichier `/etc/fail2ban/jail.local` par `backend = systemd`.
4. Redémarre le service `fail2ban` via un handler si la configuration est modifiée.
5. Gère les erreurs d’installation ou de configuration avec un bloc rescue affichant un message explicite.
6. Vérifie que le service `fail2ban` est actif dans un bloc séparé, avec gestion d’erreur (rescue) si le service ne démarre pas.
7. Crée toujours un fichier `/tmp/fail2ban_status.log` indiquant le succès de l’exécution, grâce à un bloc always.

Pour vous aider sur la syntaxe de la regexp de la tache de modification (3), voici un exemple :

```yaml
regexp: '^backend = %\(sshd_backend\)s'
replace: 'backend = systemd'
```

### Contraintes

* Utilisez des blocs imbriqués (block, rescue, always) pour structurer votre playbook.
* Le handler doit s’appeler "Redémarrer `fail2ban`".

---

Cette commande doit retourner `done` ou `error` pour chaque conteneur.

---

## ✏️ Structure attendue

Créez un fichier `block.yml` avec une structure ressemblant à celle-ci :

```yaml
    - name: Bloc principal
      block:
        - name: Bloc installation et configuration
          block:
            - name: Installer fail2ban

            - name: Déployer jail.local personnalisé
              notify: Redémarrer fail2ban

          rescue:
            - name: Échec installation ou configuration fail2ban

        - name: Bloc vérification du service
          block:
            - name: Vérifier que fail2ban est actif

          rescue:
            - name: Service fail2ban injoignable

      always:
        - name: Écrire le statut final dans /tmp/fail2ban_status.log
          ansible.builtin.copy:
```

---

## 🧪 Validation automatique

Un test `testinfra` est fourni dans `challenge/tests/test_block_structure.py`.

Il vérifie que :

* `fail2ban` est installé
* Le service `fail2ban` est actif ou inactif en fonction du conteneur
* Le fichier `/tmp/fail2ban_status.log` est bien présent

Lancez le test avec :

```bash
pytest -v
```

Vous devriez obtenir un résultat similaire à :

```bash
=== test session starts ===
platform linux -- Python 3.10.12, pytest-8.3.5, pluggy-1.5.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/ansible-training/09-Blocks
plugins: testinfra-10.2.2
collected 4 items

challenge/tests/test_block.py::test_fail2ban_service_not_running_on_server1 PASSED     [ 25%]
challenge/tests/test_block.py::test_file_exists_on_server1 PASSED                      [ 50%]
challenge/tests/test_block.py::test_fail2ban_service_not_running_on_server2 PASSED     [ 75%]
challenge/tests/test_block.py::test_file_exists_on_server2 PASSED                      [100%]

=== 4 passed in 3.04s ===
```

---

Bonne chance pour ce challenge avancé et réaliste ✨
