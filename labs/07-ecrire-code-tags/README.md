# Tags — Cibler un sous-ensemble de tâches

Bienvenue dans ce lab sur les **tags Ansible** ! 🚀

---

## 🧠 Rappel et lecture recommandée

🔗 [**Tags Ansible : cibler ou ignorer un sous-ensemble de tâches**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/tags/)

Cette page explique :

- **`tags:`** sur tâche, bloc, play, rôle
- **`--tags <liste>`** et **`--skip-tags <liste>`**
- Tags spéciaux : **`always`**, **`never`**, **`tagged`**, **`untagged`**
- L'**héritage** des tags depuis play/bloc/rôle vers les tâches enfants

---

## 🌟 Objectif du TP

À la fin :

1. Appliquer un tag à plusieurs tâches indépendantes
2. Exécuter sélectivement avec `--tags configuration`
3. Vérifier que seules les tâches ciblées ont tourné

---

## ⚙️ Exercices pratiques

### Exercice 1 — Squelette du playbook

Créez `playbook.yml` :

```yaml
---
- name: Démo tags Ansible
  hosts: web1.lab
  become: true

  tasks:
    # Tâche 1 : tagged install — pose /tmp/tag-install.txt
    # Tâche 2 : tagged configuration — pose /tmp/tag-configuration.txt
    # Tâche 3 : tagged service — pose /tmp/tag-service.txt
```

### Exercice 2 — 3 tâches taggées

Pour chaque tâche, utilisez `ansible.builtin.copy` avec `content:` :

```yaml
- name: Marqueur stage install
  ansible.builtin.copy:
    dest: /tmp/tag-install.txt
    content: "install posé à {{ ansible_date_time.iso8601 }}\n"
    mode: "0644"
  tags: install
```

Idem avec les tags `configuration` et `service`.

### Exercice 3 — Lancer en ciblant un seul tag

```bash
ansible-playbook labs/07-ecrire-code-tags/playbook.yml --tags configuration
```

PLAY RECAP attendu : `ok=1 changed=1 skipped=2`. Les tâches `install` et
`service` sont **skippées**.

### Exercice 4 — Vérifier sur web1

```bash
ssh ansible@web1.lab 'ls /tmp/tag-*.txt'
```

Seul `/tmp/tag-configuration.txt` doit exister.

### Exercice 5 — `--list-tags` et `--list-tasks`

```bash
ansible-playbook playbook.yml --list-tags
ansible-playbook playbook.yml --list-tasks --tags configuration
```

Permet de **dry-runner** la sélection avant l'exécution réelle.

---

## 🚀 Pour aller plus loin

Le **challenge** dans `challenge/README.md` ajoute les tags spéciaux
**`always`** et **`never`** pour des tâches qui doivent **toujours** ou
**jamais** s'exécuter.

Bonne pratique ! 🧠
