# Premier playbook — Installer nginx sur les webservers

Bienvenue dans votre premier playbook Ansible ! 🚀

---

## 🧠 Rappel et lecture recommandée

Avant de plonger dans la pratique, lisez la page complète sur le site :

🔗 [**Premier playbook Ansible : installer nginx, ouvrir le port 80, démarrer le service**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premier-playbook/)

Cette page explique :

- L'**anatomie d'un playbook** (`name`, `hosts`, `become`, `gather_facts`, `tasks`)
- Les modules essentiels : `ansible.builtin.dnf`, `ansible.builtin.systemd`, `ansible.posix.firewalld`, `ansible.builtin.uri`, `ansible.builtin.debug`
- L'utilisation de **`register:`** pour capturer une sortie
- La lecture du **PLAY RECAP** et la preuve d'idempotence (`changed=0`)

---

## 🌟 Objectif du TP

À la fin de ce TP, vous serez capable de :

1. Écrire un playbook YAML qui enchaîne **5 tâches**
2. L'exécuter avec `ansible-playbook` sur le groupe `webservers`
3. Lire le PLAY RECAP et identifier les colonnes `ok`, `changed`, `failed`
4. Vérifier l'**idempotence** en relançant le playbook (`changed=0` au second passage)
5. Tester depuis l'extérieur que le service répond

---

## ⚙️ Arborescence cible (à construire vous-même)

```text
labs/premiers-pas/premier-playbook/
├── README.md          ← ce fichier (déjà présent)
├── playbook.yml       ← À CRÉER — votre premier playbook
└── challenge/
    ├── README.md      ← challenge final (déjà présent)
    └── tests/
        └── test_premier_playbook.py  ← (déjà présent — pytest+testinfra)
```

---

## ⚙️ Exercices pratiques

### Exercice 1 — Squelette du playbook

Créez le fichier `playbook.yml` dans ce répertoire avec la structure suivante :

```yaml
---
- name: Déployer nginx sur les webservers
  hosts: webservers
  become: true
  gather_facts: true

  tasks:
    # Vous allez écrire les 5 tâches ci-dessous, dans cet ordre
```

**Points à retenir** :

- `hosts: webservers` cible le groupe défini dans `inventory/hosts.yml`
- `become: true` élève en root via sudo
- `gather_facts: true` récupère les facts au démarrage du play

### Exercice 2 — Tâche 1 : installer nginx

Ajoutez une première tâche utilisant `ansible.builtin.dnf` (FQCN obligatoire pour la RHCE) qui installe le paquet `nginx` avec `state: present`.

**Documentation utile** :

```bash
ansible-doc ansible.builtin.dnf
```

### Exercice 3 — Tâche 2 : démarrer et activer nginx

Ajoutez une deuxième tâche utilisant `ansible.builtin.systemd` qui :

- Démarre le service `nginx` (`state: started`)
- L'active au boot (`enabled: true`)

### Exercice 4 — Tâche 3 : ouvrir le port 80 dans firewalld

Ajoutez une troisième tâche utilisant `ansible.posix.firewalld` qui ouvre le service `http` avec :

- `permanent: true` (règle persistante au reboot)
- `immediate: true` (règle appliquée tout de suite)
- `state: enabled`

### Exercice 5 — Tâche 4 : tester avec `uri`

Ajoutez une quatrième tâche utilisant `ansible.builtin.uri` qui interroge `http://localhost` côté managed node et vérifie que le code HTTP retourné est **200**.

Capturez la sortie dans une variable nommée `nginx_response` via `register:`.

### Exercice 6 — Tâche 5 : afficher le code HTTP avec `debug`

Ajoutez une cinquième tâche utilisant `ansible.builtin.debug` qui affiche un message du type :

> `nginx répond avec le code 200 sur web1.lab`

Indices : `{{ nginx_response.status }}` et `{{ inventory_hostname }}`.

### Exercice 7 — Exécuter le playbook

Depuis la **racine du repo** (`~/Projets/ansible-training/`) :

```bash
ansible-playbook labs/premiers-pas/premier-playbook/playbook.yml
```

**Sortie attendue** au premier passage :

```text
PLAY RECAP *********************************************************************
web1.lab                   : ok=5    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web2.lab                   : ok=5    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

`ok=5` (vos 5 tâches + les facts), `changed=3` (les 3 tâches qui ont modifié l'état réel — install, start, firewall).

### Exercice 8 — Vérifier l'idempotence

Relancez **immédiatement** la même commande. Le PLAY RECAP doit afficher :

```text
web1.lab                   : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

`changed=0` est la **preuve d'idempotence** : le playbook ne re-modifie rien quand l'état désiré est déjà appliqué.

### Exercice 9 — Tester depuis votre poste

Depuis le control node (votre poste) :

```bash
curl -I http://10.10.20.21
curl -I http://10.10.20.22
```

Vous devez voir `HTTP/1.1 200 OK` et `Server: nginx/...` dans les en-têtes.

---

## 🚀 Pour aller plus loin

Quand votre playbook fonctionne et est idempotent, attaquez le **challenge** dans `challenge/README.md` qui vous demandera de réécrire le même type de logique pour un autre service web (Apache `httpd`) sur le serveur `db1.lab`. Les tests pytest+testinfra valideront automatiquement votre solution.

Bonne pratique ! 🧠
