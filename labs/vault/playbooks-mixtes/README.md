# Lab 80 — Playbooks mixtes : main.yml + vault.yml par groupe

> 💡 **Pré-requis** : `ansible all -m ansible.builtin.ping` répond `pong` sur les 4 VMs.

## 🧠 Rappel

🔗 [**Playbooks mixtes (clair + chiffré)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/playbooks-mixtes/)

**Pattern recommandé 2026** : séparer les **variables publiques** (clair) des **secrets** (chiffrés) dans deux fichiers distincts au sein de chaque `group_vars/<groupe>/` :

```text
inventory/group_vars/
├── all/
│   ├── main.yml        ← variables publiques partagées (port, version, env)
│   └── vault.yml       ← secrets partagés (chiffré)
├── webservers/
│   ├── main.yml        ← config publique webservers
│   └── vault.yml       ← secrets webservers (chiffré)
└── dbservers/
    ├── main.yml
    └── vault.yml
```

**Convention de nommage** : préfixer les variables vault par **`vault_*`** (ex: `vault_admin_token`, `vault_db_password`). Permet un coup d'œil rapide pour distinguer une variable sensible.

**Avantages** :

- **Diff Git lisibles** sur les variables publiques (`main.yml` change souvent, `vault.yml` rarement).
- **Lecture du main.yml sans déchiffrer** — pas besoin du mot de passe vault pour comprendre la config.
- **Secrets isolés** : un seul fichier à protéger par groupe.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Structurer **`group_vars/<groupe>/main.yml + vault.yml`**.
2. **Ne chiffrer que les secrets**, pas les configurations publiques.
3. Adopter la convention **`vault_*`** pour les variables sensibles.
4. Voir Ansible **fusionner automatiquement** main.yml et vault.yml (même variable globale).
5. **Référencer** les vault_* depuis le playbook comme des variables normales.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/vault/playbooks-mixtes/
ls inventory/group_vars/all/        # main.yml + vault.yml
ls inventory/group_vars/webservers/ # main.yml + vault.yml
```

## ⚙️ Arborescence cible

```text
labs/vault/playbooks-mixtes/
├── README.md
├── .vault_password                 ← mot de passe vault unique (mode 0600)
├── inventory/
│   ├── hosts.yml
│   └── group_vars/
│       ├── all/
│       │   ├── main.yml            ← deployment_environment (clair)
│       │   └── vault.yml           ← vault_admin_token (chiffré)
│       └── webservers/
│           ├── main.yml            ← http_port, worker_count (clair)
│           └── vault.yml           ← vault_web_secret, vault_web_db_password (chiffré)
├── playbook.yml
└── challenge/
    ├── solution.yml
    └── tests/
```

## 📚 Exercice 1 — Inspecter la structure mixte

```bash
cat inventory/group_vars/all/main.yml
# → deployment_environment: lab80 (clair)

cat inventory/group_vars/all/vault.yml | head -3
# → $ANSIBLE_VAULT;1.1;AES256 (chiffré)
```

🔍 **Observation** : les **2 fichiers** sont **fusionnés** automatiquement par Ansible — un host du groupe `all` voit **toutes** les variables (claires + chiffrées) comme un seul namespace.

## 📚 Exercice 2 — Lancer le playbook

```bash
ansible-playbook -i inventory/hosts.yml \
  --vault-password-file=.vault_password \
  playbook.yml
```

Sortie : `changed=1` sur web1.lab. Le playbook accède à 5 variables (3 claires, 3 chiffrées) **sans distinction** dans les `{{ var }}`.

## 📚 Exercice 3 — Vérifier le résultat

```bash
ssh ansible@web1.lab "sudo cat /tmp/lab80-mixte.txt"
```

Sortie :

```text
=== Lab 80 — playbook mixte ===

Variables PUBLIQUES (group_vars/<group>/main.yml) :
  deployment_environment: lab80
  http_port: 80
  worker_count: 4

Secrets CHIFFRÉS (group_vars/<group>/vault.yml) :
  vault_admin_token starts: lab80
  vault_web_secret starts: web_s
  vault_web_db_password length: 17
```

🔍 **Observation** : les 6 variables sont accessibles transparentement. Le **préfixe `vault_*`** permet de distinguer **visuellement** dans le code les valeurs sensibles.

## 📚 Exercice 4 — Lire le main.yml SANS déchiffrer

```bash
cat inventory/group_vars/webservers/main.yml
# → http_port, worker_count visibles
```

🔍 **Observation crucial** : un **développeur sans mot de passe vault** peut lire le main.yml et comprendre la config (ports, versions). C'est exactement le bénéfice du pattern : **séparation lecture publique / lecture sensible**.

## 📚 Exercice 5 — Diff Git typique

Modifier le port http :

```bash
sed -i 's/http_port: 80/http_port: 8080/' inventory/group_vars/webservers/main.yml
git diff
```

Diff Git **lisible et clair**. Avec un fichier complet chiffré, le diff serait **incompréhensible** (juste des changements hex aléatoires).

```bash
# Restaurer
sed -i 's/http_port: 8080/http_port: 80/' inventory/group_vars/webservers/main.yml
```

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi préfixer les variables sensibles par **`vault_*`** plutôt que par `_secret_*` ou autre ?

2. Que se passe-t-il si **`main.yml`** et **`vault.yml`** définissent la même variable ? (Test : ajouter `vault_admin_token: clair` dans main.yml)

3. Comment **rotater UNIQUEMENT** les secrets de `webservers/` sans toucher à `all/vault.yml` ?

4. Pourquoi **séparer** par groupe (`all/`, `webservers/`) plutôt que tout dans `all/` ?

## 🚀 Challenge final

Le challenge ([`challenge/solution.yml`](challenge/solution.yml)) déploie sur webservers et prouve que les variables main.yml + vault.yml fusionnent correctement. Tests automatisés (4 tests).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Pattern dans les rôles** (lab 81) : `defaults/main.yml` + `vars/vault.yml` du rôle.
- **Multi vault-id** (lab 79) : appliquer ce pattern par environnement (dev/prod).
- **gitignore .vault_password** : `.vault_password*` dans `.gitignore` racine du repo (le mot de passe ne doit JAMAIS être commit).
- **`ansible.cfg [defaults] vault_password_file`** pour fixer le mot de passe par défaut sans `--vault-password-file` à chaque commande.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile=production .
```

Le linter **ne touche pas** aux fichiers vault. Il vérifie le code Ansible classique (FQCN, mode, no_log).
