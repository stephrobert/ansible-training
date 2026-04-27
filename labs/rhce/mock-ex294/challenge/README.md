# Challenge — Mock RHCE EX294 : 12 tâches en 4 heures

## Conditions de l'examen

- **Durée** : 4 heures chrono.
- **Environnement** : 4 VMs (`web1.lab`, `web2.lab`, `db1.lab`, `control-node.lab`).
- **Connaissance attendue** : choix du module FQCN, paramètres, idempotence.
- **Pas d'aide externe** : doc Ansible offline (`ansible-doc`) autorisée. Pas
  d'Internet hors la doc Ansible Red Hat.
- **Critère de réussite** : 12/12 tests pytest verts.

## Pré-requis (à valider avant de démarrer le chrono)

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping              # 4 'pong' attendus
```

L'environnement de l'examen attend :

- VG `vg_lab` présent sur `db1.lab` (T10).
- UID `2001` libre sur tous les hôtes (T7).
- Port 80 libre sur les `webservers` (T5/T6).

Le lab fournit un script qui pose ces 3 pré-requis en une commande :

```bash
labs/rhce/mock-ex294/prep-environment.sh
# ou, équivalent :
make -C labs/rhce/mock-ex294/ prep
```

Lancez-le **avant** de démarrer le chrono. À l'examen Red Hat réel,
l'environnement est posé pour vous — ce script reproduit cet état initial.

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
    └── solution.yml          ← le playbook unique qui orchestre les 12 tâches
```

## Lancement attendu

```bash
ansible-playbook \
    -i labs/rhce/mock-ex294/inventory/hosts.yml \
    --vault-password-file labs/rhce/mock-ex294/.vault_password \
    -e ansible_roles_path=labs/rhce/mock-ex294/roles \
    labs/rhce/mock-ex294/challenge/solution.yml
```

---

## Les 12 tâches

### Tâche 1 — Inventaire statique

Produire `inventory/hosts.yml` au format YAML déclarant :

- Groupe `webservers` : `web1.lab`, `web2.lab`.
- Groupe `dbservers` : `db1.lab`.
- Variables globales pour tous les hôtes :
  - `ansible_user: ansible`
  - `ansible_python_interpreter: /usr/bin/python3`
  - chemin de clé SSH approprié pour atteindre les VMs du lab.

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

Installer sur **tous** les hôtes : `httpd`, `mariadb-server`, `python3-libselinux`.

### Tâche 6 — Services

- Sur `webservers` : `httpd` activé au boot et démarré.
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

- Dépose `/var/www/html/index.html` à partir d'un template Jinja2 contenant
  au moins le nom d'hôte d'inventaire.
- Garantit que `httpd` est actif (idempotent — la tâche 6 l'a déjà fait,
  votre rôle ne doit pas casser).
- Définit un handler `Restart httpd` notifié si le template change.

Le `solution.yml` invoque ce rôle pour les `webservers` (ex. `roles:` ou
`include_role:` dans une `play` qui cible `webservers`).

### Tâche 12 — Boucles et conditions

Sur `db1.lab`, créer 5 fichiers `/tmp/file1` à `/tmp/file5` :

- numéro **pair** (2, 4) : contenu `pair`.
- numéro **impair** (1, 3, 5) : contenu `impair`.

Les 5 fichiers doivent être créés en **une seule tâche** avec une boucle.

---

## Validation

```bash
pytest -v labs/rhce/mock-ex294/challenge/tests/
```

Score sur 12. Le barème de réussite est dans le README racine du lab.

## Reset

```bash
make -C labs/rhce/mock-ex294/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/rhce/mock-ex294/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?
