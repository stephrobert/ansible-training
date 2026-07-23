# 🎯 Challenge — `ansible.cfg` projet avec `profile_tasks` actif

## ✅ Objectif

Créer un `ansible.cfg` au niveau du lab qui active **`profile_tasks`** + force **`forks=20`** + utilise **`stdout_callback = yaml`**, puis lancer un playbook qui dépose **la sortie de `ansible-config dump --only-changed`** dans un fichier sur `db1.lab`.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab03a-config.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Sortie de `ansible-config dump --only-changed` (≥3 lignes non vides) |
| `ansible.cfg` doit contenir | `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks` |

## 🧩 Bloqué ?

```bash
dsoxlab hint decouvrir-configuration-ansible
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
cd labs/decouvrir/configuration-ansible/
ansible-playbook challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/decouvrir/configuration-ansible/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab03a-config.txt` existe sur `db1.lab` avec mode `0644`, owner `root`.
- ≥3 lignes non vides dans le contenu.
- L'`ansible.cfg` du lab contient bien `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks`.

## 🧹 Reset

```bash
dsoxlab clean decouvrir-configuration-ansible
```

## 💡 Pour aller plus loin

- **`ansible-config init --disabled > ansible.cfg`** : génère un fichier de config exhaustif documenté.
- **Variables d'env** : `ANSIBLE_FORKS=50` surcharge sans toucher au fichier.
- **`ansible-lint`** ne vérifie pas le contenu d'`ansible.cfg`. Pour valider la syntaxe : `ansible-config view`.
