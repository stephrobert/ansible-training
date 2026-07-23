# Lab 92 — Mock RHCE EX294 (4h chrono, 19 tâches)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `mise install && dsoxlab provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Préparer la RHCE (EX294)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/)

L'examen **RHCE EX294** est **performance-based** : 4 heures, environnement RHEL/AlmaLinux live, écriture de playbooks complets sur 15 à 20 tâches couvrant **inventaires**, **variables**, **conditions**, **boucles**, **rôles**, **gestion fichiers/services/users/SELinux/firewalld**, **ansible-vault**, **gestion d'erreur**, **déploiement par vagues**, **délégation**, **tags**, **tâches planifiées** et **facts personnalisés**. Aucun QCM. Le succès = **chaque playbook exécuté retourne `failed=0`**.

Ce lab simule un examen complet : **19 tâches indépendantes**, 4 heures, validation par pytest. **Chronométrez-vous**. Si vous finissez en 3h00, vous êtes prêt pour l'examen réel.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Gérer un examen sous chrono** : prioriser, ne pas bloquer, revenir.
2. **Couvrir** les 19 catégories standard EX294 (voir ci-dessous).
3. **Vérifier** chaque tâche **immédiatement** après sa rédaction (pas tout en fin d'examen).
4. **Identifier** vos **faiblesses persistantes** par catégorie pour réviser ciblé.

## 📋 Les 19 tâches du mock

| # | Catégorie | Tâche | Hôte cible |
|---|-----------|-------|------------|
| 1 | **Inventaire** | Créer un inventaire statique avec 2 groupes (`webservers`, `dbservers`) et `ansible_python_interpreter` | local |
| 2 | **Variables** | Définir des `group_vars` et `host_vars`, vérifier la précédence | tous |
| 3 | **Vault** | Chiffrer un fichier `vault.yml` avec `ansible-vault encrypt`, le consommer dans un playbook | tous |
| 4 | **Modules fichiers** | Déposer un fichier templatisé (`copy` + `template`) avec mode `0640`, owner `app` | `db1.lab` |
| 5 | **Modules paquets** | Installer `nginx`, `mariadb-server`, `python3-libselinux` via `dnf` | tous |
| 6 | **Services** | Activer + démarrer `nginx` et `mariadb` via `systemd` | `webservers` + `db1.lab` |
| 7 | **Utilisateurs** | Créer user `appuser` (UID 2001) + group `appgroup` (GID 2001) avec sudo NOPASSWD limité à `systemctl` | tous |
| 8 | **SELinux** | Activer `httpd_can_network_connect` (booléen permanent) | `webservers` |
| 9 | **Firewalld** | Ouvrir `http`/`https`/`mysql` (`permanent: true, immediate: true`) | `webservers` + `db1.lab` |
| 10 | **Stockage** | Créer un LV `lv_data` de 300M, fs xfs, monté sur `/mnt/data` (fstab) | `db1.lab` |
| 11 | **Rôle** | Écrire un rôle `app_deploy` qui combine 2 modules + 1 handler + 1 template | `webservers` |
| 12 | **Conditions/Boucles** | Boucle qui crée 5 fichiers `/tmp/file{1..5}` avec contenu différent selon parité | `db1.lab` |
| 13 | **Gestion d'erreur** | Rattraper l'échec réel d'une tâche (`rescued=1`, `ignored=0`), en consigner la trace, poursuivre | `db1.lab` |
| 14 | **Déploiement par vagues** | Traiter les webservers un à la fois, avec stabilisation entre les vagues | `webservers` |
| 15 | **Délégation** | Écrire un journal unique sur `db1.lab` depuis un play qui cible les webservers | `webservers` → `db1.lab` |
| 16 | **Tâches planifiées** | Rapport quotidien à 04h05 dans la crontab d'`appuser` | `db1.lab` |
| 17 | **Tags** | Tâches sélectionnables par `--tags`, un tag systématique et une purge hors de portée | `db1.lab` |
| 18 | **Facts personnalisés** | Publier `lab100` dans `/etc/ansible/facts.d`, et prouver qu'il remonte | `webservers` |
| 19 | **Content Collections** | Installer une collection épinglée depuis un `requirements.yml`, prouver qu'elle est résolvable, puis utiliser un de ses modules | `db1.lab` |

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping

# Pose l'état « salle d'examen » sur les 4 VMs, puis rend la main
dsoxlab run rhce-mock-ex294
```

Le `setup.yaml` du lab **défait** le résultat attendu des 19 tâches avant de
vous rendre la main : booléen SELinux à `off`, services firewalld refermés,
`nginx` et `mariadb-server` désinstallés, `appuser` supprimé, `/mnt/data`
démonté, crontab d'`appuser` et fact `lab100` retirés, marqueurs effacés. Un run précédent, le vôtre ou celui d'un autre lab, ne vous offre
aucun point. Il pose en revanche ce que l'énoncé déclare fourni par
l'environnement : le VG `vg_lab` sur `db1.lab`, l'UID 2001 libre, le port 80
libre.

## ⚙️ Arborescence cible

```text
labs/rhce/mock-ex294/
├── README.md                       ← cette page
├── setup.yaml                      ← l'état « salle d'examen »
├── cleanup.yaml                    ← le reset après coup
├── inventory/                      ← tâches 1 et 2
└── challenge/
    ├── README.md                   ← consigne avec les 19 tâches détaillées
    └── tests/
        └── test_functional.py      ← tests pytest pour les 19 tâches
```

L'apprenant écrit lui-même :

- `inventory/hosts.yml` et ses `group_vars`/`host_vars` (tâches 1 et 2)
- `vault.yml` chiffré + `.vault_password` (tâche 3)
- `roles/app_deploy/...` (tâche 11)
- **Un seul** `challenge/solution.yml` qui orchestre **les 19 tâches** dans
  l'ordre.

> L'`inventory/` que vous écrivez est le livrable des tâches 1 et 2 : il n'est
> pas livré avec l'énoncé, et il est gitignoré. La solution de référence du
> formateur a le sien, chiffré sous `solution/`, que vous ne pouvez pas lire.

## 📚 Stratégie d'examen

### Avant de commencer (5 minutes)

1. **Lire les 19 énoncés** du `challenge/README.md` en entier.
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

Les 19 tâches sont couvertes par la suite pytest : les plus piégeuses en ont
plusieurs, parce qu'une tâche RHCE se rate rarement en bloc. Un port ouvert
mais pas permanent, un booléen SELinux qui retombe au reboot, un volume monté
sans entrée fstab, un `NOPASSWD` bien plus large que demandé : à chaque fois
l'état est juste à l'instant T et faux après reboot, ou juste et dangereux.
C'est ce que l'examen réel sanctionne, donc c'est testé à part.

Les tests ne vérifient jamais qu'une commande a été tapée, ni ce que raconte
votre YAML : ils regardent la machine. Pour les tâches 13 à 19, cela veut dire
les compteurs du `PLAY RECAP`, les horodatages des marqueurs, le nombre de
lignes d'un journal, `crontab -l -u appuser`, un vrai run `--tags`, une
collecte de facts et l'inventaire résolu par `ansible-galaxy collection list`.
Un bon fichier obtenu par le mauvais moyen ne passe pas.

Votre score :

| Score | Verdict |
| --- | --- |
| 30/30 | ✅ Prêt pour l'examen réel |
| 26-29/30 | ⚠️ Réviser les catégories ratées avant de tenter l'examen |
| 20-25/30 | 🔁 Refaire le mock dans 1 semaine après révision ciblée |
| < 20/30 | ❌ Reprendre les sections de cours correspondantes |

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
- **Convention de ciblage** : `hosts: all` vaut ici les 3 nœuds gérés
  (`web1.lab`, `web2.lab`, `db1.lab`), et pas les 4 VMs du parc : le control
  node n'est pas dans l'inventaire du lab, l'examen ne le gère pas. C'est votre
  `inventory/hosts.yml` de la tâche 1 qui décide, pas le parc.
- **Reset isolé** : `dsoxlab clean rhce-mock-ex294` défait ce que la solution a
  posé (LV, montage, entrée fstab, `appuser`, règle sudo, booléen, ports) pour
  pouvoir rejouer le scénario à blanc.

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

Voir [`challenge/README.md`](challenge/README.md) — les **19 tâches détaillées**, dans l'ordre du playbook attendu.

## 💡 Pour aller plus loin

- **Mock 2** : refaire ce lab dans 1 semaine, viser un temps inférieur.
- **`ansible-navigator`** : un vrai objectif de l'EX294 (utiliser le content navigator pour trouver des modules dans les collections et construire des inventaires). Tester en plus votre playbook dans `community-ansible-dev-tools` (lab 84) garantit la portabilité.
- **`ansible-lint --profile production`** sur votre playbook : zéro warning attendu.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/rhce/mock-ex294/challenge/solution.yml
ansible-lint --profile production labs/rhce/mock-ex294/challenge/solution.yml
```

> 💡 **À l'examen réel**, `ansible-lint` n'est **pas** un critère officiel,
> mais un playbook qui passe le profil `production` réussit aussi l'examen
> dans 99 % des cas (FQCN explicite, modes quotés, idempotence respectée).
