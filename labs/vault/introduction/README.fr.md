# Lab 77 — Introduction à Ansible Vault (chiffrement de fichier complet)

> 💡 **Pré-requis** : `ansible all -m ansible.builtin.ping` répond `pong` sur les 4 VMs.

## 🧠 Rappel

🔗 [**Introduction à Ansible Vault**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/ansible-vault-introduction/)

**Ansible Vault** chiffre les fichiers contenant des secrets (mots de passe, tokens API, clés privées) avec **AES256**. Ces fichiers peuvent être commités dans Git **sans risque** — le chiffrement protège leur contenu. Au runtime, Ansible les **déchiffre à la volée** avec un mot de passe vault fourni via `--vault-password-file` ou `--ask-vault-pass`.

C'est le **mécanisme natif** Ansible pour gérer les secrets, sans dépendance externe (HashiCorp Vault, AWS Secrets Manager). Indispensable au RHCE EX294.

**Format du fichier chiffré** :

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961...   ← payload chiffré (hex)
6136353338613232633836333261396531376630...
```

Le **header** (`$ANSIBLE_VAULT;1.1;AES256`) permet à Ansible de reconnaître automatiquement le format.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Chiffrer** un fichier YAML complet avec `ansible-vault encrypt`.
2. **Visualiser** un fichier chiffré sans le déchiffrer (`ansible-vault view`).
3. **Modifier** un fichier chiffré (`ansible-vault edit`) — édition transparente.
4. **Lancer un playbook** qui consomme un fichier chiffré.
5. **Re-chiffrer** un fichier avec un nouveau mot de passe (`ansible-vault rekey`).
6. **Déchiffrer** un fichier en clair (`ansible-vault decrypt`) — pour debug exceptionnel.

## 🔧 Préparation

Le mot de passe vault de ce lab est **`lab77-vault-2026`**. Il vit dans
`.vault_password`, qui est **gitignoré** : on ne commite jamais un mot de passe,
même pédagogique. Il est donc absent d'un clone frais, et c'est la commande
suivante qui le pose :

```bash
scripts/setup-lab-vault-passwords.sh    # pose les .vault_password des labs vault
```

```bash
cd $ANSIBLE_TRAINING/labs/vault/introduction/
ls -la                         # voir la structure
cat .vault_password            # → lab77-vault-2026 (mode 0600 imposé)
```

Ce même mot de passe ouvre les deux fichiers chiffrés livrés avec le challenge
(`challenge/db_secrets.yml` et `challenge/api_secrets.yml`) : il est **imposé**
par eux, ce n'est pas un choix libre.

## ⚙️ Arborescence cible

```text
labs/vault/introduction/
├── README.md                  ← ce fichier
├── .vault_password            ← mot de passe vault (mode 0600, gitignoré)
├── secret.yml                 ← VOUS le créez à l'exercice 1 (chiffré, commitable !)
├── playbook.yml               ← VOUS le créez à l'exercice 4 (consomme secret.yml)
└── challenge/
    ├── README.md
    ├── db_secrets.yml         ← livré chiffré
    ├── api_secrets.yml        ← livré chiffré
    ├── solution.yml           ← VOUS l'écrivez (challenge sur db1.lab)
    └── tests/
        └── test_functional.py
```

## 📚 Exercice 1 : Créer et chiffrer un fichier de secrets

Le tutoriel travaille sur **votre propre** fichier `secret.yml` : le créer est
déjà l'essentiel du geste à apprendre.

```bash
cd $ANSIBLE_TRAINING/labs/vault/introduction/

cat > secret.yml <<'EOF'
---
db_password: "MotDePasseDemo2026"
api_token: "tok_demo_abc123xyz789"
EOF

ansible-vault encrypt secret.yml --vault-password-file=.vault_password
cat secret.yml | head -3
```

Sortie attendue :

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961333337353636643636393265...
6136353338613232633836333261396531376630623766330a663566666463...
```

🔍 **Observation** : sans le mot de passe, **impossible** de retrouver le contenu original. Le fichier peut être commité sur GitHub public — la confidentialité est assurée par AES256.

## 📚 Exercice 2 — Visualiser le contenu chiffré

```bash
ansible-vault view secret.yml --vault-password-file=.vault_password
```

Sortie :

```yaml
---
db_password: "MotDePasseDemo2026"
api_token: "tok_demo_abc123xyz789"
```

🔍 **Observation** : `view` déchiffre **temporairement en mémoire** pour affichage, **sans modifier** le fichier sur disque. Le fichier reste chiffré.

## 📚 Exercice 3 — Modifier un fichier chiffré

```bash
ansible-vault edit secret.yml --vault-password-file=.vault_password
```

Ouvre dans `$EDITOR` (vim/nano), déchiffre **en mémoire**, vous éditez, sauvegarde, **re-chiffre** automatiquement à la fermeture. Le fichier reste chiffré sur disque.

🔍 **Observation** : workflow ergonomique pour les modifications quotidiennes — pas besoin de `decrypt` puis `encrypt` manuels.

## 📚 Exercice 4 — Lancer le playbook avec déchiffrement

Créez `playbook.yml` à la racine du lab : il consomme `secret.yml` via
`vars_files:`, sans jamais le déchiffrer sur disque.

```bash
cat > playbook.yml <<'EOF'
---
- name: "Démonstration Ansible Vault : fichier chiffré"
  hosts: web1.lab
  become: true
  gather_facts: false

  vars_files:
    - secret.yml          # fichier chiffré, déchiffré au runtime

  tasks:
    - name: Afficher que les variables sont disponibles
      ansible.builtin.copy:
        dest: /tmp/lab77-vault-test.txt
        content: |
          Lab 77 : vault déchiffrement OK
          db_password length: {{ db_password | length }}
          api_token starts: {{ api_token[:4] }}...
        mode: "0600"
      no_log: false       # pour la démo on ne masque pas
EOF

ansible-playbook playbook.yml --vault-password-file=.vault_password
```

Sortie :

```text
PLAY [Démonstration Ansible Vault : fichier chiffré] *********

TASK [Afficher que les variables sont disponibles] ***********
changed: [web1.lab]

PLAY RECAP ***************************************************
web1.lab : ok=1 changed=1 unreachable=0 failed=0
```

🔍 **Observation** : Ansible déchiffre `secret.yml` **automatiquement** au runtime grâce à `vars_files: secret.yml`. Le playbook utilise `db_password` et `api_token` comme des variables normales.

## 📚 Exercice 5 — Vérifier le résultat sur web1.lab

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab "sudo cat /tmp/lab77-vault-test.txt"
```

Sortie attendue :

```text
Lab 77 : vault déchiffrement OK
db_password length: 18
api_token starts: tok_...
```

## 📚 Exercice 6 — Re-chiffrer avec un nouveau mot de passe

```bash
echo "NouveauMotDePasse2026!" > .vault_password_new
chmod 0600 .vault_password_new

ansible-vault rekey secret.yml \
  --vault-password-file=.vault_password \
  --new-vault-password-file=.vault_password_new

# Vérifier que l'ancien mot de passe ne marche plus
ansible-vault view secret.yml --vault-password-file=.vault_password
# → ERROR: Decryption failed
```

🔍 **Observation** : `rekey` permet de **rotater** le mot de passe vault sans modifier le contenu. Mandatory en cas de fuite ou de départ d'un membre de l'équipe.

```bash
# Restaurer pour les tests
ansible-vault rekey secret.yml \
  --vault-password-file=.vault_password_new \
  --new-vault-password-file=.vault_password
rm .vault_password_new
```

## 📚 Exercice 7 — Déchiffrer définitivement (rare)

```bash
ansible-vault decrypt secret.yml --vault-password-file=.vault_password
cat secret.yml                  # le fichier est en clair !
```

🔍 **Observation** : `decrypt` **modifie le fichier sur disque** (devient en clair). À utiliser **uniquement en debug exceptionnel** — sinon vous perdez la protection. Re-chiffrer ensuite :

```bash
ansible-vault encrypt secret.yml --vault-password-file=.vault_password
```

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `playbook.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `dsoxlab clean <id-du-lab>` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi le fichier chiffré peut-il être commité dans Git **sans risque** ? Quelle est la garantie cryptographique ?

2. Que se passe-t-il si vous lancez le playbook **sans** `--vault-password-file` ? (Test : retirer l'option et observer)

3. Comment **détecter** qu'un secret a été commité en clair par accident ? (Indice : `gitleaks`, `git-secrets`, `pre-commit detect-private-key`)

4. Pourquoi le mot de passe vault doit-il avoir **`mode 0600`** ?

5. Comment partager un fichier vault avec **plusieurs personnes** sans partager le mot de passe en clair ? (Sujet du lab 79 : multi vault-id)

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'**utiliser 2 fichiers chiffrés** (db_secrets.yml + api_secrets.yml) dans un playbook unifié sur `db1.lab`. Tests automatisés via `pytest+testinfra` (5 tests).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`ansible-vault rekey` en CI/CD** : automatiser la rotation périodique des mots de passe vault.
- **Variables d'environnement** : `ANSIBLE_VAULT_PASSWORD_FILE=.vault_password` évite de taper l'option à chaque commande.
- **Multi vault-id** (lab 79) : un mot de passe différent par environnement (dev/staging/prod).
- **Variables inline encrypt_string** (lab 78) : alternative plus lisible que le chiffrement de fichier complet.
- **Intégration HashiCorp Vault** (lab 82) : externaliser les secrets dans un vault enterprise.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile=production playbook.yml
```

Le linter vérifie :

- Pas de secret en clair dans le playbook (`no-log-password`).
- FQCN sur tous les modules (`ansible.builtin.copy`).
- Présence de `mode:` sur les fichiers déposés.
- Pas de `command:` sans `creates:` ou `changed_when:`.
