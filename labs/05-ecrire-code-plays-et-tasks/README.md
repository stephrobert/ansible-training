# Plays et tasks — Anatomie complète d'un play Ansible

Bienvenue dans ce lab sur la **structure complète d'un play** Ansible ! 🚀

---

## 🧠 Rappel et lecture recommandée

Avant de plonger dans la pratique, lisez la page complète sur le site :

🔗 [**Plays et tasks Ansible : anatomie complète, ordre d'exécution, mots-clés**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/plays-et-tasks/)

Cette page explique :

- L'anatomie d'un play et ses **14 mots-clés** principaux
- L'**ordre d'exécution** : `gather_facts` → `pre_tasks` → `roles` → `tasks` → `post_tasks` → `handlers`
- L'usage de **`serial:`** pour les rolling updates
- Le rôle de **`max_fail_percentage:`** comme circuit breaker
- Les stratégies **`linear`**, **`free`**, **`host_pinned`**, **`debug`**

---

## 🌟 Objectif du TP

À la fin de ce TP, vous saurez :

1. Écrire un play qui utilise **`pre_tasks`**, **`tasks`**, **`post_tasks`** et **`handlers`** dans le bon ordre
2. Vérifier l'**ordre d'exécution réel** via des fichiers marqueurs horodatés
3. Activer un rolling update avec **`serial: 1`** sur le groupe `webservers`
4. Lire le **PLAY RECAP** et identifier les colonnes par phase

---

## ⚙️ Arborescence cible

```text
labs/ecrire-code/playbooks/plays-et-tasks/
├── README.md           ← ce fichier
├── playbook.yml        ← À CRÉER — votre play complet
└── challenge/
    ├── README.md       ← challenge final (déjà présent)
    └── tests/
        └── test_plays_et_tasks.py   ← (déjà présent — pytest+testinfra)
```

---

## ⚙️ Exercices pratiques

### Exercice 1 — Squelette du play

Créez `playbook.yml` à la racine de ce répertoire avec la structure suivante :

```yaml
---
- name: Déployer nginx avec play complet (pre/tasks/post/handlers)
  hosts: webservers
  become: true
  serial: 1                      # rolling update : un hôte à la fois

  pre_tasks:
    # Vous allez écrire ici : poser un fichier marqueur "predeploy"

  tasks:
    # Vous allez écrire ici : installer + démarrer + configurer nginx

  post_tasks:
    # Vous allez écrire ici : poser un fichier marqueur "postdeploy"

  handlers:
    # Vous allez écrire ici : recharger nginx
```

### Exercice 2 — `pre_tasks` (marqueur "predeploy")

Dans `pre_tasks:`, créez un fichier `/tmp/predeploy-{{ inventory_hostname }}.txt` contenant le timestamp via `ansible.builtin.copy` + `content:`. Indices :

- Module : `ansible.builtin.copy`
- `dest: "/tmp/predeploy-{{ inventory_hostname }}.txt"`
- `content: "predeploy {{ inventory_hostname }} at {{ ansible_date_time.iso8601 }}\n"`
- `mode: "0644"`

### Exercice 3 — `tasks` (nginx + ouverture firewalld)

Dans `tasks:`, enchaînez :

1. Installer le paquet `nginx` (FQCN `ansible.builtin.dnf`).
2. **Modifier** `/etc/nginx/conf.d/site.conf` avec `ansible.builtin.copy` + `content:` posant un `server` minimal qui sert "Hello world from {{ inventory_hostname }}". Notifier le handler `Recharger nginx`.
3. Démarrer et activer `nginx` (`ansible.builtin.systemd`).
4. Ouvrir le port HTTP dans firewalld (`ansible.posix.firewalld` avec `service: http`).

### Exercice 4 — `post_tasks` (marqueur + smoke test)

Dans `post_tasks:`, enchaînez :

1. Tester `http://localhost` avec `ansible.builtin.uri` et vérifier `status_code: 200`.
2. Poser un fichier marqueur `/tmp/postdeploy-{{ inventory_hostname }}.txt` (même structure que predeploy).

### Exercice 5 — `handlers` (reload nginx)

Dans `handlers:`, ajoutez un handler nommé `Recharger nginx` qui utilise `ansible.builtin.systemd` avec `state: reloaded`.

### Exercice 6 — Exécuter

Depuis la **racine du repo** :

```bash
ansible-playbook labs/ecrire-code/playbooks/plays-et-tasks/playbook.yml
```

Avec `serial: 1`, vous voyez bien web1 traité **complètement** avant web2 (pre → tasks → post → handlers).

### Exercice 7 — Vérifier l'ordre d'exécution

```bash
ssh ansible@web1.lab cat /tmp/predeploy-web1.lab.txt /tmp/postdeploy-web1.lab.txt
```

Le fichier `predeploy` doit être **antérieur** au fichier `postdeploy` (timestamp).

### Exercice 8 — Vérifier l'idempotence

Relancez le playbook. PLAY RECAP attendu : `changed=0` partout (les paquets, services et fichiers sont déjà dans l'état désiré).

---

## 🚀 Pour aller plus loin

Quand votre playbook fonctionne et est idempotent, attaquez le **challenge** dans `challenge/README.md` qui demande d'ajouter `max_fail_percentage: 0` et un `pre_tasks` qui **échoue volontairement sur web2** pour vérifier que le rolling update **s'arrête** dès la première erreur.

Bonne pratique ! 🧠
