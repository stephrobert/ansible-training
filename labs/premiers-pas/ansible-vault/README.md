# Lab 04b — Premiers pas avec `ansible-vault`

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

🔗 [**Premiers pas avec Ansible Vault**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas-ansible-vault/)

Dès qu'un playbook manipule un **mot de passe**, un **token API** ou une
**clé privée**, il faut chiffrer ces valeurs avant de les commiter dans
Git. **`ansible-vault`** est le mécanisme natif Ansible : il chiffre des
fichiers YAML en **AES-256** avec un mot de passe vault.

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961...
6136353338613232633836333261396531376630...
```

→ Ce blob est **commitable sans risque** sur GitHub public — sans le mot
de passe vault, le contenu est inaccessible.

| Workflow | Commande |
| --- | --- |
| Chiffrer un fichier existant | `ansible-vault encrypt secret.yml` |
| Visualiser sans modifier | `ansible-vault view secret.yml` |
| Éditer (déchiffre/re-chiffre auto) | `ansible-vault edit secret.yml` |
| Déchiffrer (rare, debug) | `ansible-vault decrypt secret.yml` |
| Lancer un play qui consomme | `ansible-playbook play.yml --vault-password-file=.vault_password` |

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** un mot de passe vault dans un fichier `.vault_password`.
2. **Chiffrer** un fichier YAML avec `ansible-vault encrypt`.
3. **Visualiser / éditer** un fichier chiffré sans le déchiffrer sur disque.
4. **Lancer un playbook** qui consomme un fichier chiffré via `vars_files:`.
5. Comprendre pourquoi `.vault_password` doit être en **mode `0600`** et
   **gitignored**.
6. Différencier `--vault-password-file` (recommandé) de `--ask-vault-pass`
   (interactif).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ansible.builtin.ping
ansible-vault --version
```

## ⚙️ Arborescence cible

```text
labs/premiers-pas/ansible-vault/
├── README.md                        ← ce fichier
├── Makefile                         ← cible clean
├── .vault_password                  ← (à créer, gitignored, mode 0600)
├── secret.yml                       ← (à créer, puis chiffrer)
├── lab.yml                          ← (à écrire en suivant les exos)
└── challenge/
    ├── README.md                    ← consigne du challenge
    └── tests/
        └── test_vault_basics.py
```

## 📚 Exercice 1 — Créer le mot de passe vault

```bash
cd labs/premiers-pas/ansible-vault/

echo "premiers-pas-vault-2026" > .vault_password
chmod 0600 .vault_password
ls -la .vault_password
```

🔍 **Observation** : `mode 0600` (`-rw-------`) signifie **lisible/inscriptible
uniquement par le propriétaire**. Sans ça, `ansible-vault` peut accepter
le fichier mais c'est un anti-pattern majeur (autres users du système
peuvent voler le mot de passe).

> ⚠️ **Le fichier `.vault_password` ne doit JAMAIS être commité dans Git.**
> Il est déjà couvert par le `.gitignore` racine du repo. À sauvegarder
> dans un gestionnaire de mots de passe externe (Bitwarden, 1Password).

## 📚 Exercice 2 — Créer un fichier de secrets en clair

Créez `secret.yml` :

```yaml
---
db_password: "Sup3rSecretP@ss2026!"
api_token: "tok_demo_abc123xyz789"
```

```bash
cat secret.yml         # contenu en clair, lisible
```

## 📚 Exercice 3 — Chiffrer le fichier

```bash
ansible-vault encrypt secret.yml --vault-password-file=.vault_password
cat secret.yml | head -3
```

Sortie :

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961...
6136353338613232633836333261396531376630...
```

🔍 **Observation** : le fichier est **transformé sur place**. Le contenu
en clair n'existe plus sur disque. Seul `ansible-vault` (avec le bon mot
de passe) peut le relire.

## 📚 Exercice 4 — Visualiser sans modifier

```bash
ansible-vault view secret.yml --vault-password-file=.vault_password
```

Sortie :

```yaml
---
db_password: "Sup3rSecretP@ss2026!"
api_token: "tok_demo_abc123xyz789"
```

🔍 **Observation** : `view` déchiffre **en mémoire** pour affichage,
**sans modifier** le fichier sur disque. Le fichier reste chiffré.

## 📚 Exercice 5 — Éditer un fichier chiffré

```bash
ansible-vault edit secret.yml --vault-password-file=.vault_password
```

Cette commande :

1. Déchiffre le fichier **en mémoire**.
2. Ouvre votre `$EDITOR` (vim/nano).
3. Vous éditez normalement (ajoutez par exemple `app_secret: "xyz"`).
4. À la sauvegarde, **re-chiffre automatiquement**.

Le fichier sur disque reste chiffré tout du long.

🔍 **Observation** : workflow ergonomique pour les modifications
quotidiennes — pas besoin de `decrypt` puis `encrypt` manuels.

## 📚 Exercice 6 — Écrire un playbook qui consomme le secret

Créez `lab.yml` :

```yaml
---
- name: Premiers pas vault — déposer un secret sur db1
  hosts: db1.lab
  become: true
  gather_facts: false
  vars_files:
    - secret.yml         # ← Ansible déchiffre automatiquement au runtime

  tasks:
    - name: Déposer la config DB avec le mot de passe déchiffré
      ansible.builtin.copy:
        dest: /tmp/db-config.txt
        content: |
          # Lab 04b — vault déchiffrement OK
          db_password={{ db_password }}
          api_token={{ api_token }}
        owner: root
        group: root
        mode: "0600"
      no_log: true           # ← keyword au niveau task (pas dans le module)
```

🔍 **Observation** :

- `vars_files: [secret.yml]` charge le fichier — **chiffré ou non** —
  Ansible détecte le header `$ANSIBLE_VAULT` automatiquement.
- `no_log: true` empêche que les variables sensibles soient affichées
  dans la sortie Ansible (bonne pratique avec vault).
- `mode: "0600"` sur le fichier déposé évite que d'autres users le lisent.

## 📚 Exercice 7 — Lancer le playbook avec déchiffrement

```bash
ansible-playbook lab.yml --vault-password-file=.vault_password
```

Sortie :

```text
PLAY [Premiers pas vault — déposer un secret sur db1] ********

TASK [Déposer la config DB avec le mot de passe déchiffré] ***
changed: [db1.lab]

PLAY RECAP ***************************************************
db1.lab : ok=1 changed=1 unreachable=0 failed=0
```

🔍 **Observation** : Ansible déchiffre `secret.yml` **en mémoire au
runtime**, sans jamais écrire le contenu en clair sur disque. Le
résultat sur `db1.lab` :

```bash
ssh ansible@db1.lab "sudo cat /tmp/db-config.txt"
```

Sortie attendue :

```text
# Lab 04b — vault déchiffrement OK
db_password=Sup3rSecretP@ss2026!
api_token=tok_demo_abc123xyz789
```

## 📚 Exercice 8 — Que se passe-t-il sans le mot de passe ?

```bash
ansible-playbook lab.yml         # → SANS --vault-password-file
```

Sortie :

```text
ERROR! Attempting to decrypt but no vault secrets found
```

🔍 **Observation** : Ansible **refuse de tourner** sans le mot de passe.
**Sécurité par défaut**. Pour un workflow interactif :

```bash
ansible-playbook lab.yml --ask-vault-pass
```

Vous serez invité à taper le mot de passe au clavier (utile en démo,
**pas en CI/CD** où le fichier est plus pratique).

## 🔍 Observations à noter

- **Toujours** chiffrer les fichiers de secrets **avant** le premier
  commit Git.
- **`.vault_password`** : mode `0600`, **gitignored**, sauvegardé
  ailleurs.
- **`vars_files: [secret.yml]`** suffit — Ansible détecte le format
  vault automatiquement.
- **`no_log: true`** sur les tâches qui manipulent des secrets, sinon
  ils apparaissent dans `ansible-playbook -v`.
- **`--vault-password-file`** > `--ask-vault-pass` pour la CI/CD ;
  l'inverse en démo.

## 🤔 Questions de réflexion

1. Pourquoi `.vault_password` doit-il avoir `mode 0600` ? Que se passe-t-il
   si je laisse `0644` ?

2. Comment **détecter** qu'un secret a été commité en clair par accident ?
   (Indice : `gitleaks`, `git-secrets`, `pre-commit detect-private-key`.)

3. Imaginez : votre `.vault_password` a fuité. Que faut-il faire **dans
   l'ordre** ?

4. Pourquoi `no_log: true` est-il combiné avec vault dans les tâches qui
   manipulent des variables sensibles ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`ANSIBLE_VAULT_PASSWORD_FILE=.vault_password`** : variable d'env qui
  évite de répéter `--vault-password-file` à chaque commande.
- **Variable inline `!vault`** (lab 78) : alternative pour chiffrer
  **une seule variable** au lieu d'un fichier complet.
- **Multi vault-id** (lab 79) : un mot de passe différent par
  environnement (dev/staging/prod).
- **Vault dans un rôle** (lab 81) : `defaults/main.yml` (clair) +
  `vars/main.yml` (chiffré).
- **Intégration HashiCorp Vault / OpenBao** (labs 82-83) : externaliser
  les secrets dans un vault enterprise.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/premiers-pas/ansible-vault/lab.yml
ansible-lint labs/premiers-pas/ansible-vault/challenge/solution.yml
ansible-lint --profile production labs/premiers-pas/ansible-vault/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre
code est conforme aux bonnes pratiques : FQCN explicite, `name:` sur
chaque tâche, modes de fichier en chaîne, idempotence respectée, modules
dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des
> anti-patterns.
