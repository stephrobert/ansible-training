# Lab 78 — Chiffrer un fichier OU une variable inline

> 💡 **Pré-requis** : `ansible all -m ansible.builtin.ping` répond `pong` sur les 4 VMs.

## 🧠 Rappel

🔗 [**Chiffrer un fichier ou une variable**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/chiffrer-fichier-variable/)

Ansible Vault propose **deux approches** complémentaires de chiffrement :

| Approche | Commande | Cas d'usage |
|---|---|---|
| **Fichier complet** | `ansible-vault encrypt fichier.yml` | Plusieurs secrets liés (lab 77) |
| **Variable inline** | `ansible-vault encrypt_string 'valeur'` | Mélanger valeurs claires + chiffrées dans un même YAML |

L'**inline (encrypt_string)** est **plus lisible** dans les diffs Git : on voit que la variable change (et le contexte autour reste lisible), sans pour autant exposer la valeur. Idéal pour `group_vars/all.yml` qui contient majoritairement des valeurs publiques (ports, versions) et **quelques** secrets.

**Format** d'une variable inline chiffrée dans un YAML :

```yaml
admin_username: lab78_admin                  # ← clair (lisible dans le diff)
admin_password: !vault |                     # ← VALEUR seulement chiffrée
          $ANSIBLE_VAULT;1.1;AES256
          30613465643765383...
          6265336366626535...
```

Le **tag YAML `!vault |`** signale à Ansible que la valeur multi-ligne qui suit doit être déchiffrée au runtime.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Chiffrer **une seule valeur** avec `ansible-vault encrypt_string`.
2. **Mélanger** valeurs en clair et valeurs chiffrées dans un même fichier YAML.
3. Comprendre **quand préférer** `encrypt_string` à `encrypt` complet.
4. **Re-chiffrer** une variable existante.
5. Utiliser le tag YAML **`!vault |`** dans `group_vars/`/`host_vars/`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/vault/chiffrer-fichier-variable/
ls -la inventory/group_vars/
cat .vault_password
```

## ⚙️ Arborescence cible

```text
labs/vault/chiffrer-fichier-variable/
├── README.md
├── .vault_password               ← mot de passe vault (mode 0600)
├── inventory/
│   ├── hosts.yml                 ← inventaire local du lab
│   └── group_vars/
│       └── all.yml               ← MIXTE : clair + encrypt_string
├── playbook.yml                  ← consomme admin_username + admin_password
└── challenge/
    ├── README.md
    ├── solution.yml              ← challenge sur db1.lab
    └── tests/
        └── test_encrypt_string.py
```

## 📚 Exercice 1 — Lire le fichier mixte clair/chiffré

```bash
cat inventory/group_vars/all.yml
```

Sortie :

```yaml
---
admin_username: lab78_admin                  # ← clair
admin_password: !vault |                     # ← inline encrypt_string
          $ANSIBLE_VAULT;1.1;AES256
          30613465643765383...
```

🔍 **Observation** : seule la **valeur** de `admin_password` est chiffrée. Le **nom de la variable** reste lisible dans Git, ce qui facilite les revues de code (« Ah, on ajoute admin_password ») sans pour autant exposer le secret.

## 📚 Exercice 2 — Visualiser une variable inline

```bash
ansible-vault view inventory/group_vars/all.yml --vault-password-file=.vault_password
```

🔍 **Observation** : `view` fonctionne aussi sur les fichiers à **chiffrement mixte** — il déchiffre uniquement les valeurs `!vault |` et laisse le reste tel quel.

## 📚 Exercice 3 — Créer une nouvelle variable chiffrée

```bash
ansible-vault encrypt_string \
  --vault-password-file=.vault_password \
  --name 'db_password' \
  'MonNouveauSecretDB2026'
```

Sortie : un bloc YAML prêt à coller dans `inventory/group_vars/all.yml` :

```yaml
db_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
```

🔍 **Observation** : pas de saisie interactive du secret — il est passé en argument CLI. **Attention** : ce secret apparaît dans `bash_history`. Mieux : utiliser `--encrypt-vault-id default` + saisie via stdin.

## 📚 Exercice 4 — Saisie via stdin (plus sécurisé)

```bash
echo -n 'MonSecretViaStdin' | ansible-vault encrypt_string \
  --vault-password-file=.vault_password \
  --name 'api_key' \
  --stdin-name api_key
```

🔍 **Observation** : la valeur n'apparaît **pas** dans `bash_history`. Pour des automatisations (CI/CD), c'est le pattern recommandé.

## 📚 Exercice 5 — Lancer le playbook

```bash
ansible-playbook -i inventory/hosts.yml \
  --vault-password-file=.vault_password \
  playbook.yml
```

Sortie attendue : `changed=1`. Le playbook utilise `admin_password` comme une variable normale — déchiffrement transparent.

```bash
ssh ansible@web1.lab "sudo cat /tmp/lab78-encryptstring.txt"
```

Sortie :

```text
username: lab78_admin
password length: 17
password starts: Admin
```

## 📚 Exercice 6 — Différence inline vs fichier complet

| Critère | Fichier complet (`encrypt`) | Inline (`encrypt_string`) |
|---|---|---|
| Lisibilité du diff Git | ❌ Tout le fichier change | ✅ Seul le bloc concerné change |
| Granularité | Tous les secrets d'un fichier | Une seule valeur à la fois |
| Mélange clair + chiffré | ❌ Tout chiffré | ✅ Clair + chiffré ensemble |
| Édition interactive | `ansible-vault edit` | Manuelle (re-générer encrypt_string) |
| Performance | Une seule passe de déchiffrement | N passes (une par variable) |

**Recommandation** : `encrypt_string` pour `group_vars/all.yml` (mixte), `encrypt` pour `vars/secrets.yml` dédié aux secrets purs.

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

1. Pourquoi `encrypt_string` est-il préférable pour `group_vars/all.yml` qui contient majoritairement des valeurs publiques ?

2. Que se passe-t-il si vous **éditez manuellement** un bloc `!vault |` (ex: changer un caractère hex) ?

3. Comment **rotater** une seule variable inline sans toucher aux autres ?

4. Pourquoi `--stdin-name` est-il préférable au passage de la valeur en argument CLI ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) cible `db1.lab` et démontre que les variables `admin_username` (clair) + `admin_password` (chiffré inline) sont déchiffrées correctement. Tests automatisés via `pytest+testinfra` (4 tests).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Multi vault-id** (lab 79) : encrypt_string avec différents vault-id pour dev/prod.
- **`!vault |` dans les rôles** : utilisable dans `defaults/main.yml` ou `vars/main.yml` (lab 81).
- **Re-chiffrer toutes les variables** : `ansible-vault rekey inventory/group_vars/all.yml`.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile=production .
```

Le linter ne touche pas aux blocs `!vault |` — il vérifie uniquement la qualité du code Ansible classique autour.
