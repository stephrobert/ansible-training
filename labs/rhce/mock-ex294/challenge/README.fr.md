# Challenge — Mock RHCE EX294 : 19 tâches en 4 heures

## Conditions de l'examen

- **Durée** : 4 heures chrono.
- **Environnement** : 4 VMs (`web1.lab`, `web2.lab`, `db1.lab`, `control-node.lab`).
- **Connaissance attendue** : choix du module FQCN, paramètres, idempotence.
- **Pas d'aide externe** : doc Ansible offline (`ansible-doc`) autorisée. Pas
  d'Internet hors la doc Ansible Red Hat.
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
- UID `2001` libre sur tous les hôtes (T7).
- Port 80 libre sur les `webservers` (T5/T6).
- `semanage` disponible sur les `webservers` (vérification de T8).

C'est le `setup.yaml` du lab qui pose cet état, et il le pose **en défaisant**
le résultat attendu des 18 tâches : booléen SELinux à `off`, services firewalld
refermés, `nginx` et `mariadb-server` désinstallés, `appuser` supprimé, crontab
et facts personnalisés retirés, marqueurs effacés. Rien ne vous est offert par
un run précédent.

```bash
dsoxlab run rhce-mock-ex294       # joue le setup.yaml, puis vous rend la main
```

Démarrez le chrono **après**.

## Arborescence imposée

Tous les fichiers ci-dessous sont à créer **sous le dossier du lab** :
`labs/rhce/mock-ex294/`. Référez-vous toujours à des chemins relatifs au
lab quand le sujet dit `inventory/`, `vault.yml`, `roles/`, etc.

```text
labs/rhce/mock-ex294/
├── inventory/
│   ├── hosts.yml
│   ├── group_vars/
│   │   ├── all.yml
│   │   └── webservers.yml
│   └── host_vars/
│       └── db1.lab.yml
├── .vault_password
├── vault.yml
├── roles/
│   └── app_deploy/
└── challenge/
    └── solution.yml          ← le playbook unique qui orchestre les 19 tâches
```

## Lancement attendu

```bash
ANSIBLE_ROLES_PATH=labs/rhce/mock-ex294/roles \
ansible-playbook \
    -i labs/rhce/mock-ex294/inventory/hosts.yml \
    --vault-password-file labs/rhce/mock-ex294/.vault_password \
    labs/rhce/mock-ex294/challenge/solution.yml
```

> `ansible_roles_path` en `-e` ne sert à rien : le chemin des rôles est une
> option de configuration, pas une variable de playbook. C'est
> `ANSIBLE_ROLES_PATH` (ou `roles_path` dans `ansible.cfg`) qui la porte. Le
> conftest la déduit tout seul de l'arborescence du lab quand vous lancez
> pytest.

---

## Les 19 tâches

### Tâche 1 — Inventaire statique

Produire `inventory/hosts.yml` au format YAML déclarant :

- Groupe `webservers` : `web1.lab`, `web2.lab`.
- Groupe `dbservers` : `db1.lab`.
- Variables globales pour tous les hôtes :
  - `ansible_user: ansible` (le compte de service que dsoxlab provisionne sur les VMs).
  - `ansible_python_interpreter: /usr/bin/python3`
  - de quoi joindre les VMs sans coder la moindre IP : Terraform les attribue
    et elles changent à chaque reprovisionnement. Le ssh_config généré par
    dsoxlab (`~/.cache/dsoxlab/ansible-training/ssh_config`) porte les
    adresses réelles et la clé ; passez-le à OpenSSH via
    `ansible_ssh_common_args: -F <chemin>`.

`ansible-inventory -i inventory/hosts.yml --graph` doit afficher les deux
groupes avec leurs hôtes.

### Tâche 2 — Variables hiérarchiques

Définir :

| Fichier | Variable | Valeur |
| --- | --- | --- |
| `inventory/group_vars/all.yml` | `app_env` | `production` |
| `inventory/group_vars/webservers.yml` | `worker_count` | `4` |
| `inventory/host_vars/db1.lab.yml` | `db_name` | `lab100db` |

Sur `web1.lab`, déposer le fichier `/tmp/lab100-vars.txt` (mode `0644`) qui
contient au minimum les lignes :

```text
app_env: production
worker_count: 4
```

### Tâche 3 — Vault

- Créer `.vault_password` (mode `0600`) avec un mot de passe de votre choix.
- Créer `vault.yml`, **chiffré**, contenant la variable :
  - `db_password: "Lab92Pass!"`
- Charger ce fichier dans le playbook via `vars_files:`.
- Sur `db1.lab`, écrire `/tmp/lab100-vault-test.txt` (mode `0600`) contenant
  la valeur déchiffrée de `db_password`.

### Tâche 4 — Template

Sur `db1.lab`, déposer `/tmp/lab100-app.conf` :

- mode `0640`, owner `appuser`, group `appgroup` (cf. tâche 7).
- contenu généré depuis un template Jinja2 incluant **au minimum** le hostname
  Ansible et la valeur de `db_name` (la chaîne `lab100db` doit apparaître).

### Tâche 5 — Paquets

Installer sur **tous** les hôtes : `nginx`, `mariadb-server`, `python3-libselinux`.

### Tâche 6 — Services

- Sur `webservers` : `nginx` activé au boot et démarré.
- Sur `db1.lab` : `mariadb` activé au boot et démarré.

### Tâche 7 — Utilisateurs et groupes

Sur **tous** les hôtes :

- Groupe `appgroup` (GID `2001`).
- Utilisateur `appuser` (UID `2001`, group primaire `appgroup`, shell `/bin/bash`).
- Le user `appuser` doit pouvoir exécuter `/usr/bin/systemctl` via `sudo` **sans
  saisir de mot de passe** (uniquement cette commande).

### Tâche 8 — SELinux

Sur `webservers`, activer le booléen SELinux `httpd_can_network_connect` de
manière **permanente** (survit au reboot).

> 💡 Le booléen s'appelle `httpd_*` alors que le serveur web installé est
> nginx : ce n'est pas une erreur d'énoncé. Sur RHEL, nginx tourne dans le
> **domaine SELinux `httpd_t`**, qui est le domaine générique des serveurs web
> de la politique targeted. Vérifiez-le vous-même sur web1 :
> `ps -eZ | grep nginx` affiche `system_u:system_r:httpd_t:s0`. Les booléens
> `httpd_can_network_connect`, `httpd_enable_homedirs` et consorts s'appliquent
> donc bien à nginx.

### Tâche 9 — Firewalld

- Sur `webservers` : ouvrir les services `http` et `https`.
- Sur `db1.lab` : ouvrir le service `mysql`.

Les règles doivent être **persistantes** (reboot) **et actives immédiatement**
(pas besoin de `firewall-cmd --reload` après le playbook).

### Tâche 10 — Stockage LVM

Sur `db1.lab`, dans le VG existant `vg_lab` :

- Créer un LV `lv_data` de **300 Mo**.
- Le formater en **XFS**.
- Le monter sur `/mnt/data`, avec une entrée `fstab` qui **persiste au reboot**.

### Tâche 11 — Rôle `app_deploy`

Créer un rôle `app_deploy` (sous `roles/app_deploy/`) qui, sur les `webservers` :

- Dépose `/usr/share/nginx/html/index.html` à partir d'un template Jinja2 contenant
  au moins le nom d'hôte d'inventaire.
- Garantit que `nginx` est actif (idempotent, la tâche 6 l'a déjà fait,
  votre rôle ne doit pas casser).
- Définit un handler `Restart nginx` notifié si le template change.

Le `solution.yml` invoque ce rôle pour les `webservers` (ex. `roles:` ou
`include_role:` dans une `play` qui cible `webservers`).

### Tâche 12 — Boucles et conditions

Sur `db1.lab`, créer 5 fichiers `/tmp/file1` à `/tmp/file5` :

- numéro **pair** (2, 4) : contenu `pair`.
- numéro **impair** (1, 3, 5) : contenu `impair`.

Les 5 fichiers doivent être créés en **une seule tâche** avec une boucle.

### Tâche 13 — Gestion d'incident

Sur `db1.lab`, le playbook doit tenter de démarrer le service
`lab100-collecteur`. Aucun paquet de la distribution ne fournit ce service : la
tentative **échoue réellement**, à chaque passage. C'est voulu.

- La tâche qui échoue se nomme **exactement** `Démarrer le collecteur lab100`.
- L'échec ne doit **pas** interrompre le playbook. Pour `db1.lab`, le
  `PLAY RECAP` doit afficher `failed=0`.
- L'incident doit être **rattrapé**, pas passé sous silence : le `PLAY RECAP`
  doit afficher `rescued=1` et `ignored=0`. Faire taire l'erreur est refusé.
- **Uniquement en cas d'échec** : écrire `/tmp/lab100-incident.txt` (mode
  `0644`) contenant, sur une ligne à elle, le nom de la tâche qui a échoué **tel
  qu'Ansible le rapporte**. Ce nom se lit à l'exécution, il ne se recopie pas.
- **Dans tous les cas**, succès comme échec : écrire
  `/tmp/lab100-incident-fin.txt` (mode `0644`).

### Tâche 14 — Déploiement par vagues

Sur les `webservers`, le déploiement doit se faire **par vagues d'un seul hôte à
la fois**, dans l'ordre de l'inventaire (`web1.lab`, puis `web2.lab`).

- Chaque hôte dépose `/tmp/lab100-vague-<inventory_hostname>.txt` (mode `0644`,
  owner `root`). Exemple : `/tmp/lab100-vague-web1.lab.txt`.
- Le contenu du marqueur doit être **stable d'un passage à l'autre** (un
  horodatage dans le contenu casserait l'idempotence exigée plus bas).
- Entre deux vagues, le déploiement doit observer un **temps de stabilisation
  d'au moins 5 secondes**, le temps qu'un hôte fraîchement déployé se pose avant
  d'attaquer le suivant.

> La vérification porte sur les **horodatages** (`mtime`) des deux marqueurs :
> celui de `web1.lab` doit précéder celui de `web2.lab` d'au moins 3 secondes.
> Un déploiement parallèle les pose à quelques millisecondes d'écart.

### Tâche 15 — Journal de déploiement centralisé

Depuis un play qui cible les **`webservers`**, écrire le journal
`/tmp/lab100-deploy-log.txt` (mode `0644`, owner `root`) **sur `db1.lab`**.

- Il doit contenir **exactement une ligne**, quel que soit le nombre de
  webservers, et rejouer le playbook ne doit pas en ajouter.
- Cette ligne doit nommer le **webserver** à l'origine de l'écriture (son
  `inventory_hostname`) et porter la valeur de `worker_count` (cf. tâche 2).
- Le fichier ne doit exister **sur aucun** webserver.

### Tâche 16 — Tâche planifiée

Sur `db1.lab`, planifier un rapport dans la **crontab de l'utilisateur
`appuser`** (cf. tâche 7), c'est-à-dire celle que rend
`crontab -l -u appuser` :

- horaire : tous les jours à **04h05** ;
- commande : `/usr/bin/date >> /tmp/lab100-rapport.log 2>&1` ;
- une entrée et une seule : rejouer le playbook ne doit pas la dupliquer.

### Tâche 17 — Sélection des tâches par tags

Sur `db1.lab`, quatre tâches, chacune déposant son marqueur en mode `0644` :

| Tâche | Marqueur | Doit s'exécuter |
| --- | --- | --- |
| Marqueur de préparation | `/tmp/lab100-tag-preparation.txt` | sous le tag `preparation` |
| Marqueur de déploiement | `/tmp/lab100-tag-deploiement.txt` | sous le tag `deploiement` |
| Marqueur systématique | `/tmp/lab100-tag-always.txt` | **toujours**, y compris sous `--tags deploiement` |
| Purge destructive | `/tmp/lab100-tag-purge.txt` | **jamais**, sauf sous `--tags purge` demandé explicitement |

La purge, en plus de poser son marqueur, supprime ceux de préparation et de
déploiement.

Les deux comportements vérifiés, sur des runs réels :

- **Sans `--tags`** : préparation, déploiement et systématique sont posés ; la
  purge n'a **pas** eu lieu.
- **Avec `--tags deploiement`** : déploiement et systématique sont posés ;
  préparation et purge sont **absents**.

### Tâche 18 — Fact personnalisé

Sur les `webservers`, publier un fact personnalisé que toute collecte de facts
retrouvera :

- répertoire `/etc/ansible/facts.d` (mode `0755`, owner `root`) ;
- fichier `lab100.fact` (mode `0644`, owner `root`), au format **INI**, section
  `[exam]`, avec deux clés :
  - `env` : la valeur de `app_env` (cf. tâche 2) ;
  - `workers` : la valeur de `worker_count` (cf. tâche 2).

Les valeurs doivent **venir de l'inventaire**, pas être recopiées en dur.

La vérification n'ouvre pas le fichier : elle demande à Ansible ce qu'il en
récupère. La commande suivante doit rendre `ansible_local.lab100.exam.env` et
`ansible_local.lab100.exam.workers` sur **les deux** webservers :

```bash
ansible webservers -i inventory/hosts.yml \
    -m ansible.builtin.setup -a filter=ansible_local
```

### Tâche 19 — Content Collection via `requirements.yml`

L'objectif EX294 **« Install Content Collections and use them in playbooks »**
n'est prouvé par aucune des tâches précédentes : ajoutez-le.

Écrivez un **`requirements.yml`** déclarant **une** collection depuis Ansible
Galaxy, sa version **épinglée en semver strict** (`community.general` version
`10.5.0`). Installez-la dans un **répertoire dédié au projet** (pas dans le
home), avec l'étape d'installation rendue **idempotente** (`creates:` sur
`ansible-galaxy`, qui est un processus fils et ignore tout d'un second passage).

Puis, depuis `db1.lab` :

- Déposez `/tmp/lab100-collections.txt` (mode `0644`, owner `root`) contenant la
  sortie de `ansible-galaxy collection list` pour ce chemin d'installation. Elle
  doit nommer la collection **et** sa version épinglée, la preuve qu'elle est
  réellement installée et résolvable.
- **Servez-vous** d'un module **de la collection installée** :
  `community.general.ini_file` écrit `/tmp/lab100-collection-use.ini` (mode
  `0644`, owner `root`) avec la section `[collections]` et la clé
  `installed = community.general`.

> La vérification ne lit pas votre `requirements.yml` : elle contrôle l'état
> qu'il a produit. Un `requirements.yml` qui déclare les bonnes sources mais
> n'est jamais installé ne laisse aucun `10.5.0` dans l'inventaire des
> collections, et un fichier obtenu par un simple `copy` ne prouve pas que vous
> savez utiliser un module de collection.

---

## Validation

```bash
pytest -v labs/rhce/mock-ex294/challenge/tests/
```

Le barème de réussite est dans le README racine du lab. Les 19 tâches sont
couvertes par la suite pytest : plusieurs tâches en ont deux ou trois, parce
qu'une tâche RHCE se rate rarement en bloc. On peut ouvrir un port sans le rendre
permanent, activer un booléen SELinux qui retombe au reboot, monter un volume
sans entrée fstab, ou accorder à `appuser` un sudo bien plus large que demandé :
à chaque fois l'état est juste à l'instant T et faux après reboot, ou juste et
dangereux. Ce sont exactement les points que l'examen réel sanctionne.

Les tâches 13 à 18 sont vérifiées de la même façon, sur l'état réel des
machines : les compteurs du `PLAY RECAP` pour l'incident rattrapé, les
horodatages des marqueurs pour les vagues, le nombre de lignes du journal pour
la délégation, `crontab -l -u appuser` pour la tâche planifiée, un vrai run
`--tags` pour la sélection, et une collecte de facts pour `ansible_local`.
Obtenir le bon fichier par le mauvais moyen ne passe pas : une erreur ignorée au
lieu d'être rattrapée laisse le même fichier derrière elle, et le `PLAY RECAP`
la dénonce.

## Reset

```bash
dsoxlab clean rhce-mock-ex294
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/rhce/mock-ex294/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois. Un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre. C'est un critère de
  l'examen, et un test le vérifie.

- **Tâche 14, la preuve par l'absurde** : retirez le mot-clé qui séquence les
  vagues et relancez. Les deux marqueurs se posent en même temps, et le test
  vire au rouge. C'est ce qui fait la différence entre un test qui mesure et un
  test qui espère.

- **Cas limites** : au-delà de la tâche 13, pensez aux autres scénarios d'erreur
  (host indisponible, dépendance manquante, valeur invalide) que votre solution
  pourrait rencontrer en production. `failed_when`, `assert` et
  `any_errors_fatal` complètent `block`/`rescue`.
