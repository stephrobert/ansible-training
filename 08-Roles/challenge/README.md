# Challenge Ansible : Configuration de `rsyslog` via un rôle

Bienvenue dans le challenge final du TP 08. Cette fois, vous allez devoir créer
un rôle Ansible permettant de configurer le service **rsyslog**, un composant
essentiel pour la gestion des journaux système sous Linux.

---

## 🎓 Objectif

Créer un rôle `rsyslog` qui :

1. Installe le paquet `rsyslog` si ce n'est pas déjà fait
2. Active et démarre le service `rsyslog`
3. Ajoutez une tâche qui utilise le module `lineinfile` pour decommenter la ligne
   `#cron.* /var/log/cron.log` dans le fichier `/etc/rsyslog.d/50-default.conf`.
4. Relance le service uniquement si le fichier a été modifié

Ajouter le rôle dans le playbook `playbook.yml` pour qu'il soit exécuté après le
role `sshd`.

---

## 🔧 Environnement

Détruisez la machine `server1` préalablement créée dans le TP avec Incus (Debian
12).

Recréez-la avec la commande suivante :

```bash
incus rm server1 --force
incus launch images:ubuntu/24.04/cloud server1  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus file push ~/.ssh/id_ed25519.pub server1/home/admin/.ssh/authorized_keys
```

Remplacez `~/.ssh/id_ed25519.pub` par le chemin de votre clé publique SSH si
vous utilisez une autre clé.

---

## ✏️ Fichiers attendus

Dans le rôle `roles/rsyslog/` :

* `tasks/main.yml` : installation, configuration, notification du service en cas
  de changement.
* `handlers/main.yml` : redémarrage du service `rsyslog`.

---

## 🧪 Validation automatique

Un test `testinfra` est fourni dans `challenge/tests/test_rsyslog.py`.

Il vérifie que :

* Le service `rsyslog` est installé et actif
* Le fichier `/etc/rsyslog.d/50-default.conf` contient la ligne
  `cron.* /var/log/cron.log` décommentée

Lancez le test avec :

```bash
pytest -v
```

---

## ✅ Conseils

* Utilisez le module `template` pour générer la conf
* Pensez à `notify` pour déclencher un handler
* Testez l'idempotence de votre rôle (aucun changement au 2e passage)

---

Bonne chance pour ce challenge de configuration réel ✨
