# Lab 92 — Mock RHCE EX294 (4h chrono, 12 tâches)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Préparer la RHCE (EX294)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/)

L'examen **RHCE EX294** est **performance-based** : 4 heures, environnement RHEL/AlmaLinux live, écriture de playbooks complets sur 12-15 tâches couvrant **inventaires**, **variables**, **conditions**, **boucles**, **rôles**, **gestion fichiers/services/users/SELinux/firewalld**, et **ansible-vault**. Aucun QCM. Le succès = **chaque playbook exécuté retourne `failed=0`**.

Ce lab simule un examen complet : **12 tâches indépendantes**, 4 heures, validation par pytest. **Chronométrez-vous**. Si vous finissez en 3h00, vous êtes prêt pour l'examen réel.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Gérer un examen sous chrono** : prioriser, ne pas bloquer, revenir.
2. **Couvrir** les 12 catégories standard EX294 (voir ci-dessous).
3. **Vérifier** chaque tâche **immédiatement** après sa rédaction (pas tout en fin d'examen).
4. **Identifier** vos **faiblesses persistantes** par catégorie pour réviser ciblé.

## 📋 Les 12 tâches du mock

| # | Catégorie | Tâche | Hôte cible |
|---|-----------|-------|------------|
| 1 | **Inventaire** | Créer un inventaire statique avec 2 groupes (`webservers`, `dbservers`) et `ansible_python_interpreter` | local |
| 2 | **Variables** | Définir des `group_vars` et `host_vars`, vérifier la précédence | tous |
| 3 | **Vault** | Chiffrer un fichier `vault.yml` avec `ansible-vault encrypt`, le consommer dans un playbook | tous |
| 4 | **Modules fichiers** | Déposer un fichier templatisé (`copy` + `template`) avec mode `0640`, owner `app` | `db1.lab` |
| 5 | **Modules paquets** | Installer `httpd`, `mariadb-server`, `python3-libselinux` via `dnf` | tous |
| 6 | **Services** | Activer + démarrer `httpd` et `mariadb` via `systemd` | `webservers` + `db1.lab` |
| 7 | **Utilisateurs** | Créer user `appuser` (UID 2001) + group `appgroup` (GID 2001) avec sudo NOPASSWD limité à `systemctl` | tous |
| 8 | **SELinux** | Activer `httpd_can_network_connect` (booléen permanent) | `webservers` |
| 9 | **Firewalld** | Ouvrir `http`/`https`/`mysql` (`permanent: true, immediate: true`) | `webservers` + `db1.lab` |
| 10 | **Stockage** | Créer un LV `lv_data` de 200M, fs xfs, monté sur `/mnt/data` (fstab) | `db1.lab` |
| 11 | **Rôle** | Écrire un rôle `app_deploy` qui combine 2 modules + 1 handler + 1 template | `webservers` |
| 12 | **Conditions/Boucles** | Boucle qui crée 5 fichiers `/tmp/file{1..5}` avec contenu différent selon parité | `db1.lab` |

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping

# Reset complet de l'état pour démarrer à blanc
ansible all -b -m ansible.builtin.shell \
  -a "rm -f /tmp/lab100-* /etc/yum.repos.d/lab100-* 2>/dev/null; true" \
  2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/rhce/mock-ex294/
├── README.md                       ← cette page
├── Makefile                        ← cible clean (purge tout)
└── challenge/
    ├── README.md                   ← consigne avec les 12 tâches détaillées
    └── tests/
        └── test_mock_ex294.py      ← 12 tests pytest (un par tâche)
```

L'apprenant écrit lui-même les **12 fichiers** :

- `inventory/hosts.yml` (tâche 1)
- `inventory/group_vars/all.yml`, `inventory/group_vars/webservers.yml`, `inventory/host_vars/db1.lab.yml` (tâche 2)
- `vault.yml` chiffré + `.vault_password` (tâche 3)
- `roles/app_deploy/...` (tâche 11)
- **Un seul** `playbook.yml` qui orchestre **les 12 tâches** dans l'ordre.

## 📚 Stratégie d'examen

### Avant de commencer (5 minutes)

1. **Lire les 12 énoncés** du `challenge/README.md` en entier.
2. **Identifier** les 2-3 tâches qui paraissent les plus difficiles → prévoir plus de temps.
3. **Vérifier** que `ansible all -m ping` répond `pong` partout.

### Pendant l'examen (≤ 4h chrono)

- **Une tâche à la fois**. Écrire la tâche + lancer le playbook + vérifier manuellement.
- **Bloqué > 10 minutes** ? **Sauter** et revenir plus tard.
- **`ansible-doc <module>`** pour rappel rapide d'un paramètre.
- **`ansible-doc -l | grep <mot>`** pour retrouver un module FQCN.

### Validation finale (15 minutes)

```bash
pytest -v labs/rhce/mock-ex294/challenge/tests/
```

Sur les 12 tests, votre score :

| Score | Verdict |
| --- | --- |
| 12/12 | ✅ Prêt pour l'examen réel |
| 10-11/12 | ⚠️ Réviser les 1-2 catégories ratées avant de tenter l'examen |
| 8-9/12 | 🔁 Refaire le mock dans 1 semaine après révision ciblée |
| < 8/12 | ❌ Reprendre les sections de cours correspondantes |

## 📚 Exercice 1 — Démarrer le chrono

```bash
date '+Démarrage : %Y-%m-%d %H:%M:%S' | tee /tmp/lab100-start.txt
```

Stoppez quand vous lancez le `pytest` final. Comparez à 4h.

## 🤔 Pièges classiques en EX294 réel

- **Quoter `mode: "0644"`** sinon YAML l'interprète en octal puis décimal → mode `420` (lecture seule).
- **`name:` se terminant par `:`** → casse YAML 1.2. Toujours quoter.
- **`firewalld`** sans `immediate: true` → règle permanente non active jusqu'au reload.
- **`SELinux`** : oublier `python3-libselinux` côté cible → `template`/`copy` plantent.
- **`ansible-vault`** : oublier `--vault-password-file` au lancement.
- **`hosts: all`** au lieu de `hosts: webservers` → tâche s'exécute partout, casse l'inventaire.
- **`become: true`** oublié sur les tâches privilégiées (firewalld, dnf, systemd).

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible all (les 4 VMs du parc) ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Comment adapter votre solution si la cible passait de **1 host** à un
   parc de **50 serveurs** ? Quels paramètres (`forks`, `serial`, `strategy`)
   faudrait-il ajuster pour conserver des temps d'exécution acceptables ?

2. Quels modules Ansible alternatifs auriez-vous pu utiliser pour atteindre
   le même résultat ? Quels sont leurs trade-offs (idempotence garantie,
   performance, dépendances de collection externe) ?

3. Si une étape du playbook échoue en cours d'exécution, quel est l'impact
   sur les hôtes déjà traités ? Comment rendre le scénario reprenable
   (`block/rescue/always`, `--start-at-task`, `serial`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — les **12 tâches détaillées**, dans l'ordre du playbook attendu.

## 💡 Pour aller plus loin

- **Mock 2** : refaire ce lab dans 1 semaine, viser un temps inférieur.
- **`ansible-navigator`** : pas requis à l'EX294 actuel, mais tester votre playbook dans `creator-ee` (lab 84) garantit la portabilité.
- **`ansible-lint --profile production`** sur votre playbook : zéro warning attendu.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/rhce/mock-ex294/challenge/solution.yml
ansible-lint --profile production labs/rhce/mock-ex294/challenge/solution.yml
```

> 💡 **À l'examen réel**, `ansible-lint` n'est **pas** un critère officiel,
> mais un playbook qui passe le profil `production` réussit aussi l'examen
> dans 99 % des cas (FQCN explicite, modes quotés, idempotence respectée).
