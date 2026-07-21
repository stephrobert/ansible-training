# Examen blanc RHCE EX294 #2 (4h chrono, 19 tâches)

> 💡 **Vous arrivez directement à ce lab ?** Chaque lab de ce dépôt est
> **autonome**. Pré-requis unique : les 4 VMs du lab doivent répondre au ping
> Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `mise install && dsoxlab provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Préparer la RHCE (EX294)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/)

L'examen **RHCE EX294** est **performance-based** : 4 heures, environnement
RHEL/AlmaLinux live, écriture de playbooks complets sur 15 à 20 tâches. Ce lab
est un **second examen blanc**, une variante de `rhce/mock-ex294` : les **19
mêmes catégories**, mais **toutes les valeurs concrètes changent**. Si vous avez
déjà fait le mock #1, aucune de vos réponses ne se recopie ici : la pile est
**Apache + valkey** au lieu de nginx + mariadb, et les utilisateurs, le découpage
LVM, les ports, le booléen SELinux, l'horaire du cron, les tags, le fact
personnalisé et la collection installée sont tous différents. Mêmes compétences,
situation différente. **Chronométrez-vous.**

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Gérer un examen sous chrono** : prioriser, ne pas bloquer, revenir.
2. **Couvrir** les 19 catégories standard EX294 sur une cible non familière.
3. **Vérifier** chaque tâche **immédiatement** après sa rédaction.
4. **Identifier** vos **faiblesses persistantes** par catégorie pour réviser
   ciblé.

## 📋 Les 19 tâches du mock #2

| # | Catégorie | Tâche | Hôte cible |
|---|-----------|-------|------------|
| 1 | **Inventaire** | Inventaire statique avec 2 groupes (`frontends`, `backends`) et `ansible_python_interpreter` | local |
| 2 | **Variables** | Définir des `group_vars` et `host_vars` (`deploy_stage`, `pool_size`, `schema_name`) | tous |
| 3 | **Vault** | Chiffrer un `vault.yml` (`api_token`), le consommer dans un playbook | tous |
| 4 | **Modules fichiers** | Déposer un fichier templatisé (`template`) mode `0600`, owner `svcuser` | `db1.lab` |
| 5 | **Modules paquets** | Installer `httpd`, `valkey`, `python3-libselinux` via `dnf` | tous |
| 6 | **Services** | Activer + démarrer `httpd` et `valkey` via `systemd` | `frontends` + `db1.lab` |
| 7 | **Utilisateurs** | Créer `svcuser` (UID 3200) + group `svcgroup` (GID 3200) avec sudo NOPASSWD limité à `journalctl` | tous |
| 8 | **SELinux** | Activer `httpd_can_network_connect_db` (booléen permanent) | `frontends` |
| 9 | **Firewalld** | Ouvrir `http`/`https` sur les frontends, port `6379/tcp` sur db1 (`permanent`+`immediate`) | `frontends` + `db1.lab` |
| 10 | **Stockage** | Créer un LV `lv_app` de 400M, fs ext4, monté sur `/srv/appdata` (fstab) | `db1.lab` |
| 11 | **Rôle** | Écrire un rôle `web_publish` qui combine 2 modules + 1 handler + 1 template | `frontends` |
| 12 | **Conditions/Boucles** | Boucle qui crée 6 fichiers `/tmp/slot{1..6}` avec contenu différent selon parité | `db1.lab` |
| 13 | **Gestion d'erreur** | Rattraper l'échec réel d'une tâche (`rescued=1`, `ignored=0`), en consigner la trace, poursuivre | `db1.lab` |
| 14 | **Déploiement par vagues** | Traiter les frontends un à la fois, avec stabilisation entre les vagues | `frontends` |
| 15 | **Délégation** | Écrire un journal unique sur `db1.lab` depuis un play qui cible les frontends | `frontends` → `db1.lab` |
| 16 | **Tâches planifiées** | Rapport quotidien à 22h30 dans la crontab de `svcuser` | `db1.lab` |
| 17 | **Tags** | Tâches sélectionnables par `--tags`, un tag systématique et une purge hors de portée | `db1.lab` |
| 18 | **Facts personnalisés** | Publier `lab200` dans `/etc/ansible/facts.d`, et prouver qu'il remonte | `frontends` |
| 19 | **Content Collections** | Installer une collection épinglée depuis un `requirements.yml`, prouver qu'elle est résolvable, puis utiliser un de ses modules | `db1.lab` |

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping

# Pose l'état « salle d'examen » sur les 4 VMs, puis rend la main
dsoxlab run rhce-mock-ex294-2
```

Le `setup.yaml` du lab **défait** le résultat attendu des 19 tâches avant de
vous rendre la main : booléen SELinux à `off`, services et port firewalld
refermés, `httpd` et `valkey` désinstallés, `svcuser` supprimé, `/srv/appdata`
démonté, crontab de `svcuser` et fact `lab200` retirés, marqueurs effacés, nginx
arrêté pour libérer le port 80. Un run précédent ne vous offre aucun point. Il
pose en revanche ce que l'énoncé déclare fourni par l'environnement : le VG
`vg_lab` sur `db1.lab`, l'UID 3200 libre, le port 80 libre.

## ⚙️ Arborescence cible

```text
labs/rhce/mock-ex294-2/
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
- `roles/web_publish/...` (tâche 11)
- **Un seul** `challenge/solution.yml` qui orchestre **les 19 tâches** dans
  l'ordre.

> L'`inventory/` que vous écrivez est le livrable des tâches 1 et 2 : il n'est
> pas livré avec l'énoncé, et il est gitignoré. La solution de référence du
> formateur a le sien, chiffré sous `solution/`, que vous ne pouvez pas lire.

## 📚 Stratégie d'examen

### Avant de commencer (5 minutes)

1. **Lire les 19 énoncés** du `challenge/README.md` en entier.
2. **Identifier** les 2-3 tâches qui paraissent les plus difficiles → prévoir
   plus de temps.
3. **Vérifier** que `ansible all -m ping` répond `pong` partout.

### Pendant l'examen (≤ 4h chrono)

- **Une tâche à la fois**. Écrire la tâche + lancer le playbook + vérifier.
- **Bloqué > 10 minutes** ? **Sauter** et revenir plus tard.
- **`ansible-doc <module>`** pour rappel rapide d'un paramètre.

### Validation finale (15 minutes)

```bash
pytest -v labs/rhce/mock-ex294-2/challenge/tests/
```

Les 19 tâches sont couvertes par la suite pytest : les plus piégeuses en ont
plusieurs, parce qu'une tâche RHCE se rate rarement en bloc. Un port ouvert mais
pas permanent, un booléen SELinux qui retombe au reboot, un volume monté sans
entrée fstab, un `NOPASSWD` bien plus large que demandé : à chaque fois l'état
est juste à l'instant T et faux après reboot, ou juste et dangereux. C'est ce
que l'examen réel sanctionne, donc c'est testé à part.

Les tests ne vérifient jamais qu'une commande a été tapée, ni ce que raconte
votre YAML : ils regardent la machine. Pour les tâches 13 à 19, cela veut dire
les compteurs du `PLAY RECAP`, les horodatages des marqueurs, le nombre de
lignes d'un journal, `crontab -l -u svcuser`, un vrai run `--tags`, une collecte
de facts et l'inventaire résolu par `ansible-galaxy collection list`. Un bon
fichier obtenu par le mauvais moyen ne passe pas.

Votre score :

| Score | Verdict |
| --- | --- |
| tout vert | ✅ Prêt pour l'examen réel |
| 1-2 rouges | ⚠️ Réviser les catégories ratées avant de tenter l'examen |
| 3-6 rouges | 🔁 Refaire le mock dans 1 semaine après révision ciblée |
| plus | ❌ Reprendre les sections de cours correspondantes |

## 🤔 Pièges classiques en EX294 réel

- **Quoter `mode: "0644"`** sinon YAML l'interprète en octal puis décimal → mode `420`.
- **`firewalld`** sans `immediate: true` → règle permanente non active jusqu'au reload.
- **`SELinux`** : oublier `python3-libselinux` côté cible → `template`/`copy` plantent.
- **`ansible-vault`** : oublier `--vault-password-file` au lancement.
- **`hosts: all`** au lieu de `hosts: frontends` → la tâche s'exécute partout.
- **`become: true`** oublié sur les tâches privilégiées (firewalld, dnf, systemd).

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0` partout.
- **FQCN explicite** : préférez `ansible.builtin.<module>` (ou la collection
  appropriée) plutôt que le nom court.
- **Convention de ciblage** : `hosts: all` vaut ici les 3 nœuds gérés
  (`web1.lab`, `web2.lab`, `db1.lab`), et pas les 4 VMs du parc.
- **Reset isolé** : `dsoxlab clean rhce-mock-ex294-2` défait ce que la solution
  a posé, pour rejouer le scénario à blanc.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) : les **19 tâches détaillées**,
dans l'ordre du playbook attendu.

## 💡 Pour aller plus loin

- Vous avez aussi terminé `rhce/mock-ex294` ? Deux examens blancs complets aux
  valeurs différentes sont la meilleure preuve que vous avez appris la
  **compétence**, pas la réponse.
- **`ansible-lint --profile production`** sur votre playbook : zéro warning attendu.
