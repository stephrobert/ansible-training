# 🎯 Challenge — Module `cron:` (2 jobs via `cron_file:`)

## ✅ Objectif

Sur **db1.lab**, créer un fichier dédié **`/etc/cron.d/lab-rhce`** qui
contient :

- Une variable d'environnement `MAILTO=admin@lab.local`
- **Job 1** : `Backup horaire` à `0 * * * *` (minute 0 de chaque heure),
  exécute `/usr/local/bin/backup.sh` en tant que `root`.
- **Job 2** : `Cleanup quotidien` à `0 3 * * *` (3h du matin),
  exécute `/usr/bin/find /tmp -mtime +7 -delete` en tant que `root`.

> 💡 **Pourquoi `cron_file:` plutôt que la crontab utilisateur ?**
> `/etc/cron.d/<fichier>` est versionné via Ansible, lisible directement,
> et permet de poser une **configuration packageable** (un rôle pose son
> fichier dédié, c'est plus propre que de patcher une crontab partagée).

## 🧩 Pattern `cron_file:`

Avec `cron_file: lab-rhce`, **chaque appel** à `ansible.builtin.cron`
écrit/modifie une ligne dans `/etc/cron.d/lab-rhce`. Pour
qu'Ansible reconnaisse une ligne déjà posée et ne duplique pas, il utilise
le `name:` (qui devient un commentaire `#Ansible: <name>` dans le fichier).

> ⚠️ **`name:`** est **obligatoire** quand vous utilisez `cron_file:` —
> c'est l'identifiant d'idempotence.

## 🧩 Squelette

```yaml
---
- name: Challenge - cron via fichier dédié
  hosts: db1.lab
  become: true

  tasks:
    - name: Variable d'environnement MAILTO
      ansible.builtin.cron:
        name: ???
        env: ???
        value: ???
        cron_file: ???
        user: root

    - name: Job backup horaire
      ansible.builtin.cron:
        name: ???
        minute: ???
        # hour: par défaut "*"
        job: ???
        cron_file: ???
        user: root

    - name: Job cleanup quotidien
      ansible.builtin.cron:
        name: ???
        minute: ???
        hour: ???
        job: ???
        cron_file: ???
        user: root
```

> 💡 **Pièges** :
>
> - **`name:`** est le **marqueur d'idempotence** (commentaire `#Ansible:
>   <name>` dans le crontab). Sans, chaque run ajoute une nouvelle entrée.
> - **`cron_file:`** crée `/etc/cron.d/<file>` (system-wide). Sans,
>   modifie le crontab user (`/var/spool/cron/<user>`).
> - **`user:`** : pour `cron_file:`, c'est l'user qui exécute la tâche
>   (champ entre minute et commande). Pour crontab user, c'est le crontab
>   ciblé.
> - **`@reboot`** comme `special_time:` : `special_time: reboot`,
>   `daily`, `weekly`, etc. Évite l'écriture manuelle de
>   `0 0 * * 0`.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-services/cron/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/cron.d/lab-rhce"
```

🔍 Sortie attendue (extrait) :

```text
#Ansible: MAILTO
MAILTO=admin@lab.local
#Ansible: Backup horaire
0 * * * * root /usr/local/bin/backup.sh
#Ansible: Cleanup quotidien
0 3 * * * root /usr/bin/find /tmp -mtime +7 -delete
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-services/cron/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-services/cron clean
```

## 💡 Pour aller plus loin

- **Crontab utilisateur** : sans `cron_file:`, `cron:` modifie la crontab de
  l'utilisateur cible (`crontab -e`). Plus standard mais moins versionnable.
- **`special_time:`** : raccourci pour `@reboot`, `@hourly`, `@daily`,
  `@weekly`, `@monthly`.
- **`disabled: true`** : commente la ligne (au lieu de la supprimer). Permet
  de désactiver temporairement un job sans perdre sa définition.
- **Lint** :

   ```bash
   ansible-lint labs/modules-services/cron/challenge/solution.yml
   ```
