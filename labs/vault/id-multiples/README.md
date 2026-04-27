# Lab 79 — Vault IDs multiples (dev / prod / staging)

> 💡 **Pré-requis** : `ansible all -m ansible.builtin.ping` répond `pong` sur les 4 VMs.

## 🧠 Rappel

🔗 [**Vault IDs multiples**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-id-multiples/)

**Un mot de passe vault unique** ne suffit pas en équipe : tout le monde a accès aux secrets de **prod** s'il peut déchiffrer **dev**. Solution : **vault-id étiquetés** par environnement.

```yaml
$ANSIBLE_VAULT;1.2;AES256;dev      ← header avec label "dev"
$ANSIBLE_VAULT;1.2;AES256;prod     ← header avec label "prod"
```

Chaque fichier porte son **label**. Au runtime, on passe **plusieurs `--vault-id`** :

```bash
ansible-playbook \
  --vault-id dev@.vault_password_dev \
  --vault-id prod@.vault_password_prod \
  playbook.yml
```

Ansible essaie chaque vault-id sur chaque fichier chiffré et utilise le bon. **Workflow équipe** : les devs n'ont que `.vault_password_dev`, les ops ont les deux.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Chiffrer avec un **vault-id étiqueté** (`--encrypt-vault-id dev`).
2. Déchiffrer **plusieurs vault-id** dans un même run.
3. Structurer `inventory/group_vars/<env>/secrets.yml` par environnement.
4. Comprendre le **header v1.2** (`$ANSIBLE_VAULT;1.2;AES256;<label>`).
5. **Workflow équipe** : un mot de passe par environnement, distribué selon les rôles.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/vault/id-multiples/
ls -la                              # 2 fichiers .vault_password_*
ls inventory/group_vars/            # dev/  prod/
```

## ⚙️ Arborescence cible

```text
labs/vault/id-multiples/
├── README.md
├── .vault_password_dev             ← mot de passe DEV
├── .vault_password_prod            ← mot de passe PROD
├── inventory/
│   ├── hosts.yml                   ← 2 groupes : dev, prod
│   └── group_vars/
│       ├── dev/
│       │   └── secrets.yml         ← chiffré avec vault-id "dev"
│       └── prod/
│           └── secrets.yml         ← chiffré avec vault-id "prod"
├── playbook.yml
└── challenge/
    ├── solution.yml
    └── tests/
        └── test_vault_ids.py
```

## 📚 Exercice 1 — Inspecter les headers vault-id

```bash
head -1 inventory/group_vars/dev/secrets.yml
# → $ANSIBLE_VAULT;1.2;AES256;dev

head -1 inventory/group_vars/prod/secrets.yml
# → $ANSIBLE_VAULT;1.2;AES256;prod
```

🔍 **Observation** : la **version 1.2** du format vault inclut le **label** dans le header. La 1.1 (lab 77/78) ne le fait pas. Le label permet à Ansible de **savoir quel mot de passe utiliser** pour chaque fichier.

## 📚 Exercice 2 — Visualiser un fichier vault-id

```bash
ansible-vault view \
  --vault-id dev@.vault_password_dev \
  inventory/group_vars/dev/secrets.yml
```

Sortie :

```yaml
db_host: dev-db.example.com
db_password: "DevDBPass123"
```

🔍 **Observation** : sans **`dev@`**, Ansible essaie tous les `--vault-id` jusqu'à trouver le bon. Avec le label explicite, la résolution est **immédiate** — utile en debug.

## 📚 Exercice 3 — Tester l'isolation dev/prod

```bash
# Tenter de déchiffrer le fichier prod avec le mot de passe DEV
ansible-vault view \
  --vault-id dev@.vault_password_dev \
  inventory/group_vars/prod/secrets.yml
```

**Résultat** : ÉCHEC (`Decryption failed`). Le mot de passe dev **ne déchiffre pas** prod.

🔍 **Observation** : c'est exactement le bénéfice de cette isolation. Un dev compromis ne donne **pas** accès aux secrets prod.

## 📚 Exercice 4 — Lancer le playbook avec les 2 vault-id

```bash
ansible-playbook -i inventory/hosts.yml \
  --vault-id dev@.vault_password_dev \
  --vault-id prod@.vault_password_prod \
  playbook.yml
```

Sortie :

```text
PLAY [Démo vault-id multiples] *********

TASK [Pose un fichier...] ***********
changed: [web1.lab]
changed: [db1.lab]

PLAY RECAP **************************
db1.lab  : ok=1 changed=1 unreachable=0 failed=0
web1.lab : ok=1 changed=1 unreachable=0 failed=0
```

🔍 **Observation** : `web1.lab` reçoit les secrets DEV (groupe dev), `db1.lab` reçoit les secrets PROD (groupe prod). **Un seul run** déchiffre les 2 environnements en utilisant le bon mot de passe pour chaque.

## 📚 Exercice 5 — Vérifier les fichiers déposés

```bash
ssh ansible@web1.lab "sudo cat /tmp/lab79-web1.lab.txt"
ssh ansible@db1.lab  "sudo cat /tmp/lab79-db1.lab.txt"
```

`web1` voit `dev-db.example.com`, `db1` voit `prod-db.example.com`. **Pas de fuite** entre environnements.

## 📚 Exercice 6 — Re-chiffrer un environnement seul

```bash
echo "NouveauMotDePasseDev2026" > .vault_password_dev_new
chmod 0600 .vault_password_dev_new

ansible-vault rekey \
  --vault-id dev@.vault_password_dev \
  --new-vault-id dev@.vault_password_dev_new \
  inventory/group_vars/dev/secrets.yml

# prod n'est PAS impacté !
ansible-vault view \
  --vault-id prod@.vault_password_prod \
  inventory/group_vars/prod/secrets.yml
# → toujours OK
```

🔍 **Observation** : la rotation du mot de passe DEV **n'impacte pas** PROD. Pratique pour **rotater régulièrement** les secrets dev sans déranger la prod.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab (deux environnements) ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Quel est le risque concret d'un seul mot de passe vault partagé entre dev et prod ?

2. Si une équipe a 5 environnements (dev, qa, staging, preprod, prod), faut-il **5 vault-id** ?

3. Comment **distribuer** les fichiers `.vault_password_*` à l'équipe ? (Indice : Vault HashiCorp, OpenBao, gestionnaires de secrets entreprise)

4. Que se passe-t-il si vous oubliez `--vault-id prod@...` ? (Test : retirer et observer)

## 🚀 Challenge final

Le challenge ([`challenge/`](challenge/)) prouve que les 2 environnements sont déchiffrés correctement avec leurs mots de passe respectifs. Tests automatisés via `pytest+testinfra` (5 tests, dont une vérification que les passwords ont des **longueurs différentes** — preuve de déchiffrement séparé).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`vault_identity_list`** dans `ansible.cfg` pour fixer les vault-id par défaut sans les passer en CLI.
- **Playbook hybride** : variables vault-id `dev` ET vault-id `prod` dans le même fichier (rare mais possible).
- **CI/CD** : variables d'env `ANSIBLE_VAULT_PASSWORD_FILE_DEV` + `..._PROD` injectées par les secrets GitHub/GitLab.
- **Lab 82** : externaliser dans HashiCorp Vault au lieu de fichiers `.vault_password_*`.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile=production .
```

Le linter ne touche pas aux `--vault-id` — il vérifie le code Ansible classique.
