# 🎯 Challenge - Handler avec le service rsyslog

Dans ce challenge, vous allez mettre en pratique l'‘utilisation des **handlers**
Ansible en modifiant un fichier de configuration d'un service et en
**déclenchant un redémarrage conditionnel** du service.

## ✅ Objectif

* Modifier le fichier `/etc/rsyslog.conf`
* Déclencher le handler `restart rsyslog` **uniquement si la modification a
  lieu**

## 🧹 Consignes

1. Créez un playbook `rsyslog-cron.yml`
2. Ajoutez une tâche qui utilise le module `lineinfile` pour decommenter la ligne
   `#cron.* /var/log/cron.log` dans le fichier `/etc/rsyslog.d/50-default.conf`. La tâche doit
   ressembler à :
3. Assurez-vous que cette tâche notifie un handler `Restart rsyslog`
4. Dans la section `handlers`, définissez le handler `Restart rsyslog` qui
   redémarre le service `rsyslog`

## 👍 Critères de réussite

Le test `test_rsyslog.py` vérifiera que :

* Le fichier `/etc/rsyslog.d/50-default.conf` contient bien la ligne attendue
* Le service `rsyslog` est actif et fonctionne
* Le handler est bien exécuté **seulement** si le fichier était modifié
* Le playbook est **idempotent** (aucun changement à la 2e exécution)

## 🔍 Validation

Lancez le test avec la commande suivante :

```bash
pytest -v
```

Le test doit passer sans erreurs, comme ceci :

```bash
=== test session starts ===
platform linux -- Python 3.12.3, pytest-8.4.0, pluggy-1.6.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/perso/ansible-training/03-Handlers
plugins: testinfra-10.2.2
collected 2 items

challenge/tests/test_rsyslog.py::test_rsyslog_cron_uncommented PASSED                                                                                                                                                                                                           [ 50%]
challenge/tests/test_rsyslog.py::test_rsyslog_service_running PASSED                                                                                                                                                                                                            [100%]

==== 2 passed in 1.92s ====
```

**Attention** : Assurez-vous que le service `ssh` est en cours d'exécution
sur la machine server1, et que vous avez accès à la machine via SSH avec une clé
publique. Pour copier votre clé publique, utilisez les commandes suivantes :

```bash
incus exec server1 -- mkdir -p /home/admin/.ssh
incus file push ~/.ssh/id_ed25519.pub server1/home/admin/.ssh/authorized_keys
```

---

Bon courage et n'oubliez pas : **ne redémarrez que si nécessaire !** 🧪
