# Quel ansible.cfg tourne vraiment ?

## La situation

Le même playbook met quatre minutes chez vous et onze chez votre collègue, et
aucun de vous deux ne sait quel `ansible.cfg` Ansible a réellement lu : celui
de `/etc`, celui du répertoire personnel, celui de la racine du dépôt, ou une
variable d'environnement qui écrase tout en silence. Pire : personne ne peut
dire quelle tâche mange les onze minutes. On arrête de deviner. Vous
travaillez depuis **control-node.lab** et archivez la preuve sur `db1.lab`.

Votre mission :

1. Écrire un **`ansible.cfg` projet** qui monte le parallélisme à
   **`forks = 20`**, bascule la sortie sur le **callback `yaml`** et active
   **`profile_tasks`** pour que les tâches lentes se dénoncent elles-mêmes.
2. Vérifier ce qui est **réellement actif** avec
   `ansible-config dump --only-changed --type all`, et comprendre pourquoi votre fichier
   ne gagne que si le run démarre depuis son répertoire.
3. Archiver la preuve : déposer ce dump sur `db1.lab` dans
   `/tmp/lab03a-config.txt`, propriétaire `root`, mode `0644`.
4. Garder la capture honnête : une commande qui ne fait que lire ne doit jamais
   se déclarer `changed`.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/ansible-config-fichier/

## 🎯 Challenge — `ansible.cfg` projet avec `profile_tasks` actif

### ✅ Objectif

Créer un `ansible.cfg` au niveau du lab qui active **`profile_tasks`** + force **`forks=20`** + utilise **`callback_result_format = yaml`**, puis lancer un playbook qui dépose **la sortie de `ansible-config dump --only-changed --type all`** dans un fichier sur `db1.lab`.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab03a-config.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Sortie de `ansible-config dump --only-changed --type all` (≥3 lignes non vides) |
| `ansible.cfg` doit contenir | `forks = 20`, `callback_result_format = yaml`, `callbacks_enabled = ansible.posix.profile_tasks` |

### 🧩 Bloqué ?

```bash
dsoxlab hint decouvrir-configuration-ansible
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
cd labs/decouvrir/configuration-ansible/
ansible-playbook challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/decouvrir/configuration-ansible/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab03a-config.txt` existe sur `db1.lab` avec mode `0644`, owner `root`.
- ≥3 lignes non vides dans le contenu.
- L'`ansible.cfg` du lab contient bien `forks = 20`, `callback_result_format = yaml`, `callbacks_enabled = ansible.posix.profile_tasks`.

### 🧹 Reset

```bash
dsoxlab clean decouvrir-configuration-ansible
```

### 💡 Pour aller plus loin

- **`ansible-config init --disabled > ansible.cfg`** : génère un fichier de config exhaustif documenté.
- **Variables d'env** : `ANSIBLE_FORKS=50` surcharge sans toucher au fichier.
- **`ansible-lint`** ne vérifie pas le contenu d'`ansible.cfg`. Pour valider la syntaxe : `ansible-config view`.
