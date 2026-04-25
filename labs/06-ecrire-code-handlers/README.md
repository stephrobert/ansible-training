# Handlers — Pattern restart-on-config-change

Bienvenue dans ce lab sur les **handlers Ansible** ! 🚀

---

## 🧠 Rappel et lecture recommandée

Avant de plonger, lisez la page complète sur le site :

🔗 [**Handlers Ansible : notify, listen, flush_handlers et restart-on-config-change**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/handlers/)

Cette page explique :

- Le concept de **handler comme tâche réactive**
- Le déclenchement via **`notify:`** (un seul ou plusieurs handlers)
- Le regroupement via **`listen:`** sur un topic abstrait
- L'**ordre d'exécution** : à la fin de chaque section (`pre_tasks`, `tasks`, `post_tasks`)
- **`meta: flush_handlers`** pour forcer l'exécution immédiate
- Le pattern **restart-on-config-change** appliqué à nginx, sshd, postgresql

---

## 🌟 Objectif du TP

À la fin de ce TP, vous saurez :

1. Écrire un handler qui ne se déclenche **que si une tâche est `changed`**
2. Notifier plusieurs handlers depuis une même tâche
3. Forcer le déclenchement immédiat avec **`meta: flush_handlers`**
4. Combiner `validate:` + handler pour ne **jamais** appliquer une config invalide

---

## ⚙️ Arborescence cible

```text
labs/ecrire-code/playbooks/handlers/
├── README.md           ← ce fichier
├── playbook.yml        ← À CRÉER — votre play avec handlers
└── challenge/
    ├── README.md       ← challenge final
    └── tests/
        └── test_handlers.py
```

---

## ⚙️ Exercices pratiques

### Exercice 1 — Squelette

Créez `playbook.yml` :

```yaml
---
- name: Configurer httpd avec restart-on-config-change
  hosts: webservers
  become: true

  tasks:
    # Tâches qui notifient le handler
  handlers:
    # Le handler qui reload httpd
```

### Exercice 2 — Tâche avec notification

Dans `tasks:`, ajoutez :

1. Installer `httpd` via `ansible.builtin.dnf`.
2. Démarrer + activer `httpd` via `ansible.builtin.systemd`.
3. Modifier `/etc/httpd/conf/httpd.conf` pour poser `ServerTokens Prod` (au lieu de la ligne par défaut). Indices :
   - Module : `ansible.builtin.lineinfile`
   - `regexp: '^#?\\s*ServerTokens\\s+'`
   - `line: 'ServerTokens Prod'`
   - `validate: 'apachectl -t -f %s'`
   - **`notify: Reload httpd`**

### Exercice 3 — Handler

Dans `handlers:`, ajoutez `Reload httpd` qui utilise `ansible.builtin.systemd state: reloaded` sur `httpd`.

### Exercice 4 — Lancer

Depuis la racine :

```bash
ansible-playbook labs/ecrire-code/playbooks/handlers/playbook.yml
```

Au **premier passage**, le handler tourne (la ligne est ajoutée). Au **second passage**, le handler **ne tourne pas** (la ligne est déjà conforme) — c'est exactement le comportement attendu.

### Exercice 5 — Vérifier

```bash
curl -s -I http://web1.lab | grep -i ^Server:
```

Le header `Server:` doit afficher `Apache` (pas `Apache/2.4.x ...`) — preuve que `ServerTokens Prod` est appliqué et que le handler a tourné.

---

## 🚀 Pour aller plus loin

Le **challenge** dans `challenge/README.md` vous demande d'aller plus loin avec **deux handlers** déclenchés par une seule tâche, et un `meta: flush_handlers` pour tester une nouvelle config **avant** de continuer.

Bonne pratique ! 🧠
