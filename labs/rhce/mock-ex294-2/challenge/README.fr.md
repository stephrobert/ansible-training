# Challenge — Examen blanc RHCE EX294 #2 : 19 tâches en 4 heures

## Conditions de l'examen

- **Durée** : 4 heures chrono.
- **Environnement** : 4 VMs (`web1.lab`, `web2.lab`, `db1.lab`, `control-node.lab`).
- **Connaissance attendue** : choix du module FQCN, paramètres, idempotence.
- **Pas d'aide externe** : doc Ansible offline (`ansible-doc`) autorisée.
- **Critère de réussite** : les tests pytest verts (19 tâches, plusieurs
  d'entre elles vérifiées par plus d'un test).

## Pré-requis (à valider avant de démarrer le chrono)

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping              # 4 'pong' attendus
```

L'environnement de l'examen vous est **posé** : comme à l'examen Red Hat réel,
la salle est prête et vous n'avez pas à la construire.

- VG `vg_lab` présent sur `db1.lab` (T10).
- UID `3200` libre sur tous les hôtes (T7).
- Port 80 libre sur les `frontends` (nginx arrêté) (T5/T6).
- `semanage` disponible sur les `frontends` (vérification de T8).

C'est le `setup.yaml` du lab qui pose cet état, et il le pose **en défaisant** le
résultat attendu des 19 tâches.

```bash
dsoxlab run rhce-mock-ex294-2     # joue le setup.yaml, puis vous rend la main
```

Démarrez le chrono **après**.

## Arborescence imposée

Tous les fichiers ci-dessous sont à créer **sous le dossier du lab** :
`labs/rhce/mock-ex294-2/`.

```text
labs/rhce/mock-ex294-2/
├── inventory/
│   ├── hosts.yml
│   ├── group_vars/
│   │   ├── all.yml
│   │   └── frontends.yml
│   └── host_vars/
│       └── db1.lab.yml
├── .vault_password
├── vault.yml
├── roles/
│   └── web_publish/
└── challenge/
    └── solution.yml          ← le playbook unique qui orchestre les 19 tâches
```

## Lancement attendu

```bash
ANSIBLE_ROLES_PATH=labs/rhce/mock-ex294-2/roles \
ansible-playbook \
    -i labs/rhce/mock-ex294-2/inventory/hosts.yml \
    --vault-password-file labs/rhce/mock-ex294-2/.vault_password \
    labs/rhce/mock-ex294-2/challenge/solution.yml
```

---

## Les 19 tâches

### Tâche 1 — Inventaire statique

Produire `inventory/hosts.yml` au format YAML déclarant :

- Groupe `frontends` : `web1.lab`, `web2.lab`.
- Groupe `backends` : `db1.lab`.
- Variables globales pour tous les hôtes :
  - `ansible_user: ansible` (le compte de service que dsoxlab provisionne sur les VMs).
  - `ansible_python_interpreter: /usr/bin/python3`
  - de quoi joindre les VMs sans coder la moindre IP : le ssh_config généré par
    dsoxlab (`~/.cache/dsoxlab/ansible-training/ssh_config`) porte les adresses
    réelles et la clé ; passez-le à OpenSSH via `ansible_ssh_common_args: -F <chemin>`.

`ansible-inventory -i inventory/hosts.yml --graph` doit afficher les deux
groupes avec leurs hôtes.

### Tâche 2 — Variables hiérarchiques

Définir :

| Fichier | Variable | Valeur |
| --- | --- | --- |
| `inventory/group_vars/all.yml` | `deploy_stage` | `staging` |
| `inventory/group_vars/frontends.yml` | `pool_size` | `8` |
| `inventory/host_vars/db1.lab.yml` | `schema_name` | `lab200schema` |

Sur `web1.lab`, déposer le fichier `/tmp/lab200-vars.txt` (mode `0644`) qui
contient au minimum les lignes :

```text
deploy_stage: staging
pool_size: 8
```

### Tâche 3 — Vault

- Créer `.vault_password` (mode `0600`) avec un mot de passe de votre choix.
- Créer `vault.yml`, **chiffré**, contenant la variable :
  - `api_token: "Ex294-Deux!"`
- Charger ce fichier dans le playbook via `vars_files:`.
- Sur `db1.lab`, écrire `/tmp/lab200-token.txt` (mode `0600`) contenant la valeur
  déchiffrée de `api_token`.

### Tâche 4 — Template

Sur `db1.lab`, déposer `/tmp/lab200-service.conf` :

- mode `0600`, owner `svcuser`, group `svcgroup` (cf. tâche 7).
- contenu généré depuis un template Jinja2 incluant **au minimum** le hostname
  Ansible et la valeur de `schema_name` (la chaîne `lab200schema` doit apparaître).

### Tâche 5 — Paquets

Installer sur **tous** les hôtes : `httpd`, `valkey`, `python3-libselinux`.

### Tâche 6 — Services

- Sur `frontends` : `httpd` activé au boot et démarré.
- Sur `db1.lab` : `valkey` activé au boot et démarré.

### Tâche 7 — Utilisateurs et groupes

Sur **tous** les hôtes :

- Groupe `svcgroup` (GID `3200`).
- Utilisateur `svcuser` (UID `3200`, group primaire `svcgroup`, shell `/bin/bash`).
- Le user `svcuser` doit pouvoir exécuter `/usr/bin/journalctl` via `sudo` **sans
  saisir de mot de passe** (uniquement cette commande).

### Tâche 8 — SELinux

Sur `frontends`, activer le booléen SELinux `httpd_can_network_connect_db` de
manière **permanente** (survit au reboot).

> 💡 Sur cet examen le serveur web est Apache (`httpd`), qui tourne dans le
> domaine SELinux `httpd_t`. Le booléen `httpd_can_network_connect_db` autorise
> une page servie par Apache à ouvrir une connexion réseau vers une base de
> données. Vérifiez-le avec `ps -eZ | grep httpd`.

### Tâche 9 — Firewalld

- Sur `frontends` : ouvrir les services `http` et `https`.
- Sur `db1.lab` : ouvrir le **port `6379/tcp`** (le port de valkey).

Les règles doivent être **persistantes** (reboot) **et actives immédiatement**
(pas besoin de `firewall-cmd --reload` après le playbook).

### Tâche 10 — Stockage LVM

Sur `db1.lab`, dans le VG existant `vg_lab` :

- Créer un LV `lv_app` de **400 Mo**.
- Le formater en **ext4**.
- Le monter sur `/srv/appdata`, avec une entrée `fstab` qui **persiste au reboot**.

### Tâche 11 — Rôle `web_publish`

Créer un rôle `web_publish` (sous `roles/web_publish/`) qui, sur les `frontends` :

- Dépose `/var/www/html/index.html` à partir d'un template Jinja2 contenant au
  moins le nom d'hôte d'inventaire.
- Garantit que `httpd` est actif (idempotent, la tâche 6 l'a déjà fait, votre
  rôle ne doit pas casser).
- Définit un handler `Restart httpd` notifié si le template change.

Le `solution.yml` invoque ce rôle pour les `frontends`.

### Tâche 12 — Boucles et conditions

Sur `db1.lab`, créer 6 fichiers `/tmp/slot1` à `/tmp/slot6` :

- numéro **pair** (2, 4, 6) : contenu `even`.
- numéro **impair** (1, 3, 5) : contenu `odd`.

Les 6 fichiers doivent être créés en **une seule tâche** avec une boucle.

### Tâche 13 — Gestion d'incident

Sur `db1.lab`, le playbook doit tenter de démarrer le service `lab200-agent`.
Aucun paquet de la distribution ne fournit ce service : la tentative **échoue
réellement**, à chaque passage. C'est voulu.

- La tâche qui échoue se nomme **exactement** `Lancer l'agent lab200`.
- L'échec ne doit **pas** interrompre le playbook. Pour `db1.lab`, le
  `PLAY RECAP` doit afficher `failed=0`.
- L'incident doit être **rattrapé**, pas passé sous silence : le `PLAY RECAP`
  doit afficher `rescued=1` et `ignored=0`. Faire taire l'erreur est refusé.
- **Uniquement en cas d'échec** : écrire `/tmp/lab200-incident.txt` (mode `0644`)
  contenant, sur une ligne à elle, le nom de la tâche qui a échoué **tel
  qu'Ansible le rapporte**. Ce nom se lit à l'exécution, il ne se recopie pas.
- **Dans tous les cas**, succès comme échec : écrire
  `/tmp/lab200-incident-fin.txt` (mode `0644`).

### Tâche 14 — Déploiement par vagues

Sur les `frontends`, le déploiement doit se faire **par vagues d'un seul hôte à
la fois**, dans l'ordre de l'inventaire (`web1.lab`, puis `web2.lab`).

- Chaque hôte dépose `/tmp/lab200-palier-<inventory_hostname>.txt` (mode `0644`,
  owner `root`). Exemple : `/tmp/lab200-palier-web1.lab.txt`.
- Le contenu du marqueur doit être **stable d'un passage à l'autre**.
- Entre deux vagues, le déploiement doit observer un **temps de stabilisation
  d'au moins 6 secondes**.

> La vérification porte sur les **horodatages** (`mtime`) des deux marqueurs :
> celui de `web1.lab` doit précéder celui de `web2.lab` d'au moins 3 secondes.

### Tâche 15 — Journal de déploiement centralisé

Depuis un play qui cible les **`frontends`**, écrire le journal
`/tmp/lab200-central-log.txt` (mode `0644`, owner `root`) **sur `db1.lab`**.

- Il doit contenir **exactement une ligne**, quel que soit le nombre de
  frontends, et rejouer le playbook ne doit pas en ajouter.
- Cette ligne doit nommer le **frontend** à l'origine de l'écriture (son
  `inventory_hostname`) et porter la valeur de `pool_size` (cf. tâche 2).
- Le fichier ne doit exister **sur aucun** frontend.

### Tâche 16 — Tâche planifiée

Sur `db1.lab`, planifier un rapport dans la **crontab de l'utilisateur
`svcuser`** (cf. tâche 7), c'est-à-dire celle que rend `crontab -l -u svcuser` :

- horaire : tous les jours à **22h30** ;
- commande : `/usr/bin/date >> /tmp/lab200-audit.log 2>&1` ;
- une entrée et une seule : rejouer le playbook ne doit pas la dupliquer.

### Tâche 17 — Sélection des tâches par tags

Sur `db1.lab`, quatre tâches, chacune déposant son marqueur en mode `0644` :

| Tâche | Marqueur | Doit s'exécuter |
| --- | --- | --- |
| Marqueur d'init | `/tmp/lab200-tag-init.txt` | sous le tag `init` |
| Marqueur de publication | `/tmp/lab200-tag-publish.txt` | sous le tag `publish` |
| Marqueur systématique | `/tmp/lab200-tag-always.txt` | **toujours**, y compris sous `--tags publish` |
| Purge destructive | `/tmp/lab200-tag-purge.txt` | **jamais**, sauf sous `--tags purge` demandé explicitement |

La purge, en plus de poser son marqueur, supprime ceux d'init et de publication.

Les deux comportements vérifiés, sur des runs réels :

- **Sans `--tags`** : init, publication et systématique sont posés ; la purge n'a
  **pas** eu lieu.
- **Avec `--tags publish`** : publication et systématique sont posés ; init et
  purge sont **absents**.

### Tâche 18 — Fact personnalisé

Sur les `frontends`, publier un fact personnalisé que toute collecte de facts
retrouvera :

- répertoire `/etc/ansible/facts.d` (mode `0755`, owner `root`) ;
- fichier `lab200.fact` (mode `0644`, owner `root`), au format **INI**, section
  `[audit]`, avec deux clés :
  - `stage` : la valeur de `deploy_stage` (cf. tâche 2) ;
  - `pool` : la valeur de `pool_size` (cf. tâche 2).

Les valeurs doivent **venir de l'inventaire**, pas être recopiées en dur.

La vérification n'ouvre pas le fichier : elle demande à Ansible ce qu'il en
récupère. La commande suivante doit rendre `ansible_local.lab200.audit.stage` et
`ansible_local.lab200.audit.pool` sur **les deux** frontends :

```bash
ansible frontends -i inventory/hosts.yml \
    -m ansible.builtin.setup -a filter=ansible_local
```

### Tâche 19 — Content Collection via `requirements.yml`

L'objectif EX294 **« Install Content Collections and use them in playbooks »**
n'est prouvé par aucune des tâches précédentes : ajoutez-le.

Écrivez un **`requirements.yml`** déclarant **une** collection depuis Ansible
Galaxy, sa version **épinglée en semver strict** (`ansible.posix` version
`1.6.2`). Installez-la dans un **répertoire dédié au projet** (pas dans le home),
avec l'étape d'installation rendue **idempotente** (`creates:` sur
`ansible-galaxy`).

Puis, depuis `db1.lab` :

- Déposez `/tmp/lab200-collections.txt` (mode `0644`, owner `root`) contenant la
  sortie de `ansible-galaxy collection list` pour ce chemin d'installation. Elle
  doit nommer la collection **et** sa version épinglée.
- **Servez-vous** d'un module **de la collection installée** : `ansible.posix.sysctl`
  écrit le paramètre noyau `vm.swappiness` à la valeur `25`, appliqué et persisté
  dans le fichier `/etc/sysctl.d/99-lab200-collection.conf`.

> La vérification ne lit pas votre `requirements.yml` : elle contrôle l'état
> qu'il a produit. Un `requirements.yml` qui déclare les bonnes sources mais
> n'est jamais installé ne laisse aucun `1.6.2` dans l'inventaire des
> collections, et un `vm.swappiness` resté à sa valeur par défaut prouve
> qu'aucun module de la collection n'a tourné.

---

## Validation

```bash
pytest -v labs/rhce/mock-ex294-2/challenge/tests/
```

Le barème de réussite est dans le README racine du lab. Plusieurs tâches ont deux
ou trois tests, parce qu'une tâche RHCE se rate rarement en bloc. On peut ouvrir
un port sans le rendre permanent, activer un booléen SELinux qui retombe au
reboot, monter un volume sans entrée fstab, ou accorder à `svcuser` un sudo bien
plus large que demandé : à chaque fois l'état est juste à l'instant T et faux
après reboot, ou juste et dangereux. Ce sont exactement les points que l'examen
réel sanctionne.

## Reset

```bash
dsoxlab clean rhce-mock-ex294-2
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.
- **Idempotence** : relancez la solution une seconde fois. Un `PLAY RECAP` avec
  `changed=0` partout confirme un playbook propre. Un test le vérifie.
