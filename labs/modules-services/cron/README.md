# Lab 39 — Module `cron:` (planifier des jobs idempotents)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Module cron Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-cron/)

`ansible.builtin.cron:` gère les **jobs cron** avec **idempotence garantie via le
`name:`**. Chaque job est identifié par son **nom unique** que Ansible inscrit en
commentaire (`#Ansible: <name>`) au-dessus de la ligne du job. À chaque run, le
job est **mis à jour** au lieu d'être empilé.

Le module sait gérer :

- la **crontab utilisateur** (`crontab -l`) — défaut.
- les fichiers **`/etc/cron.d/*`** via `cron_file:` — préférable pour la
  traçabilité.
- les **variables d'environnement** (`MAILTO`, `PATH`) au-dessus des jobs (`env: true`).
- la **désactivation** sans suppression (`disabled: true`).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Comprendre** le mécanisme du `name:` et le marker `#Ansible:`.
2. **Choisir** entre crontab user et `/etc/cron.d/` (et pourquoi le second est
   préférable).
3. **Définir** des variables d'environnement (`MAILTO`, `PATH`) avec `env: true`.
4. **Désactiver** un job sans le supprimer (`disabled: true`).
5. **Utiliser** les raccourcis `special_time:` (`hourly`, `daily`, etc.).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/cron.d/lab-rhce; crontab -u root -r 2>/dev/null; true"
```

## 📚 Exercice 1 — Job dans la crontab user

Créez `lab.yml` :

```yaml
---
- name: Demo cron crontab user
  hosts: db1.lab
  become: true
  tasks:
    - name: Backup quotidien dans la crontab de root
      ansible.builtin.cron:
        name: "Backup base de donnees"
        minute: "0"
        hour: "2"
        job: "/usr/local/bin/backup-db.sh > /var/log/backup.log 2>&1"
```

**Lancez** :

```bash
ansible-playbook labs/modules-services/cron/lab.yml
ssh ansible@db1.lab 'sudo crontab -l'
```

🔍 **Observation** : la crontab de root contient :

```text
#Ansible: Backup base de donnees
0 2 * * * /usr/local/bin/backup-db.sh > /var/log/backup.log 2>&1
```

**Le commentaire `#Ansible: ...`** est le **marker d'idempotence** : Ansible
cherche cette ligne au prochain run pour identifier le job et le remplacer.

**Re-lancer** : `changed=0` (déjà au bon état).

## 📚 Exercice 2 — Pattern `/etc/cron.d/<file>` (préférable)

```yaml
- name: Healthcheck dans /etc/cron.d/
  ansible.builtin.cron:
    name: "Healthcheck monitoring"
    minute: "*/5"
    job: "/usr/local/bin/healthcheck.sh"
    cron_file: monitoring
    user: root
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/cron.d/monitoring'
```

🔍 **Observation** : le fichier `/etc/cron.d/monitoring` est créé. Différences
importantes avec la crontab user :

| Caractéristique | crontab user | `/etc/cron.d/<file>` |
|---|---|---|
| Visibilité | `crontab -l -u root` (caché) | `ls /etc/cron.d/` (visible) |
| Versioning git | Non (état système) | Oui (fichier dans `/etc/`) |
| Spécifie `user:` par ligne | Non (toute la crontab d'un user) | Oui (chaque ligne a un user) |
| Modularité | Tous les jobs dans 1 file | 1 fichier par module/rôle |

**Recommandation** : préférer **`cron_file:`** pour la **traçabilité** et la
**modularité**.

## 📚 Exercice 3 — Variables d'environnement (`env: true`)

```yaml
- name: Definir MAILTO pour les jobs lab
  ansible.builtin.cron:
    name: MAILTO
    env: true
    value: admin@lab.local
    cron_file: lab-rhce
    user: root

- name: Definir PATH custom (binaires myapp)
  ansible.builtin.cron:
    name: PATH
    env: true
    value: /opt/myapp/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
    cron_file: lab-rhce
    user: root

- name: Job qui utilise les vars
  ansible.builtin.cron:
    name: "Backup horaire"
    minute: "0"
    job: "myapp-backup.sh"  # Resolu via PATH
    cron_file: lab-rhce
    user: root
```

🔍 **Observation** :

- **`env: true`** change la sémantique : `name:` devient le **nom de la variable**,
  `value:` est sa **valeur**.
- **Variables utiles** : `MAILTO`, `PATH`, `SHELL`.

**Vérifiez le fichier généré** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/cron.d/lab-rhce'
```

```text
#Ansible: MAILTO
MAILTO="admin@lab.local"
#Ansible: PATH
PATH="/opt/myapp/bin:/usr/local/sbin:..."
#Ansible: Backup horaire
0 * * * * root myapp-backup.sh
```

**`PATH`** est crucial — par défaut, le `PATH` de cron est **très restrictif**
(`/usr/bin:/bin`). Si votre script est dans `/opt/myapp/bin/`, il ne sera **pas
trouvé** sans ce `PATH:` override.

## 📚 Exercice 4 — Désactiver un job sans le supprimer

```yaml
- name: Suspendre temporairement le backup horaire
  ansible.builtin.cron:
    name: "Backup horaire"
    minute: "0"
    job: "myapp-backup.sh"
    cron_file: lab-rhce
    user: root
    disabled: true
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/cron.d/lab-rhce'
```

```text
#Ansible: Backup horaire
#0 * * * * root myapp-backup.sh
```

🔍 **Observation** : la ligne du job est **commentée** (`#0 * * * * ...`). Le job
**ne s'exécute plus** mais reste **conservé pour référence**. Pour le **réactiver**,
repasser `disabled: false`.

**Cas d'usage** : maintenance programmée, debugging d'un script qui plante,
suspension d'un cron pendant un audit.

## 📚 Exercice 5 — `special_time:` (raccourcis)

```yaml
- name: Job hourly avec raccourci
  ansible.builtin.cron:
    name: "Healthcheck rapide"
    special_time: hourly
    job: "/usr/local/bin/healthcheck.sh"
    cron_file: lab-rhce
    user: root
```

| Forme | Équivalent | Usage |
|---|---|---|
| `special_time: hourly` | `0 * * * *` | Toutes les heures |
| `special_time: daily` | `0 0 * * *` | Tous les jours à minuit |
| `special_time: weekly` | `0 0 * * 0` | Tous les dimanches à minuit |
| `special_time: monthly` | `0 0 1 * *` | Le 1er de chaque mois |
| `special_time: reboot` | `@reboot` | À chaque démarrage |

🔍 **Observation** : `special_time:` **exclut** les options `minute/hour/day/month/weekday`.
Utiliser **soit** `special_time:`, **soit** les autres — pas les deux.

## 📚 Exercice 6 — Suppression d'un job (`state: absent`)

```yaml
- name: Supprimer le job "Backup horaire"
  ansible.builtin.cron:
    name: "Backup horaire"
    state: absent
    cron_file: lab-rhce
    user: root
```

🔍 **Observation** : Ansible cherche le commentaire `#Ansible: Backup horaire` et
**supprime cette ligne + la ligne du job juste en dessous**.

**Important** : sans `state: absent`, un job **renommé** ou **déplacé** devient
**orphelin** dans la crontab. Toujours **faire le ménage explicite** quand vous
restructurez les jobs.

## 📚 Exercice 7 — Le piège : modifier le `name:` empile au lieu de remplacer

```yaml
# Run 1
- ansible.builtin.cron:
    name: "Backup BDD"
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/backup-db.sh"

# Run 2 (apres avoir RENOMME)
- ansible.builtin.cron:
    name: "Backup base de donnees"  # Nouveau nom
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/backup-db.sh"  # Meme job
```

🔍 **Observation** : la crontab contient **2 jobs identiques** ! Un avec
`#Ansible: Backup BDD`, l'autre avec `#Ansible: Backup base de donnees`. Le job
tournera **2 fois** à 2h.

**Solution** : avant de renommer, **supprimer l'ancien** :

```yaml
- ansible.builtin.cron:
    name: "Backup BDD"  # Ancien nom
    state: absent

- ansible.builtin.cron:
    name: "Backup base de donnees"  # Nouveau nom
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/backup-db.sh"
```

**Règle** : `name:` est la **clé d'identification**. Ne **jamais** le modifier
sans plan de migration.

## 🔍 Observations à noter

- **`name:`** = clé d'idempotence — **ne jamais** modifier après création.
- **`cron_file:` dans `/etc/cron.d/`** est préférable à la crontab user (visibilité, versioning).
- **`env: true`** pour `MAILTO`, `PATH`, `SHELL` — pas dans la même tâche que les jobs.
- **`disabled: true`** désactive sans supprimer — utile pour les maintenances.
- **`special_time:`** raccourcit les schedules courants — exclut les options
  `minute/hour/etc`.
- **`state: absent`** + `name:` = supprimer un job (avec son commentaire marker).

## 🤔 Questions de réflexion

1. Vous gérez 5 jobs cron différents pour le rôle `monitoring`. Vous voulez
   pouvoir **déployer/retirer** tous ces jobs en une seule passe. Quel pattern
   (`cron_file:`, `loop:`, ...) ?

2. Pourquoi `PATH` dans la crontab est-il un piège classique pour les scripts
   custom ? Quelle est la valeur par défaut du `PATH` cron ?

3. Vous voulez exécuter un script **toutes les 30 minutes** mais aussi **à
   chaque reboot**. Comment articulez-vous deux tâches `cron:` (avec et sans
   `special_time:`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`hour: "8-18"`** ou **`hour: "*/2"`** : ranges et steps dans les schedules.
- **Pattern `at:`** : pour des **jobs ponctuels** (pas récurrents) — module
  `ansible.posix.at` (collection ansible.posix).
- **Anacron** : pour des jobs qui doivent **rattraper** leurs runs manqués si
  la machine était éteinte. Pas géré directement par `cron:` Ansible — passer
  par `template:` sur `/etc/cron.daily/`.
- **systemd timers** : alternative moderne à cron, plus puissant (déclencheurs
  multiples, dépendances). Géré via `systemd_service:` sur les `.timer` units.
- **Pattern `audit cron`** : un play qui collecte toutes les crontabs de tous
  les hôtes via `command: crontab -l` + `fetch:` — pour audit centralisé.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-services/cron/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-services/cron/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-services/cron/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
