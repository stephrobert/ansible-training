# 🎯 Challenge — Refactorer un playbook non idempotent

## ✅ Objectif

Écrire un playbook qui **passe le test d'idempotence** : `changed=0` au second passage. Trois opérations à enchaîner sur `db1.lab`, chacune **idempotente** :

| # | Action | Module recommandé | Garde idempotence |
| --- | --- | --- | --- |
| 1 | Créer `/tmp/lab91-marker` avec contenu | `ansible.builtin.shell` | `creates:` |
| 2 | Poser `max_connections = 200` dans `/tmp/lab91-config.cfg` | `ansible.builtin.lineinfile` | `regexp:` + `create:` |
| 3 | Lire la version curl et la stocker dans `/tmp/lab91-curl.txt` | `ansible.builtin.command` + `register` + `copy` | `changed_when: false` sur la lecture |

**Critère** : second passage de `solution.yml` retourne `changed=0`.

## 🧩 Bloqué ?

```bash
dsoxlab hint troubleshooting-idempotence-perfs
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/idempotence-perfs/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-idempotence-perfs
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** détecte les `command`/`shell` sans `changed_when:`.
- **Pre-commit hook `ansible-lint`** dans le repo pour bloquer les régressions.
- **Mode `--check --diff`** pour prévisualiser les changements sans appliquer.
