# 🎯 Challenge : écrire un requirements.yml et l'installer réellement

## ✅ Mission

Deux temps, tous deux vérifiés par pytest :

1. **Écrire** `requirements.yml` (à la racine du lab, livré en squelette) :

   | Attente | Détail |
   | --- | --- |
   | Section `roles:` | au moins 2 rôles, TOUS avec `version:` épinglée |
   | Source Git | au moins 1 rôle avec `src:` pointant github.com |
   | Source Galaxy | au moins 1 rôle sans `src:` (résolu via Galaxy) |
   | Section `collections:` | au moins 1 collection épinglée en version EXACTE (X.Y.Z) |

2. **Installer** ce manifeste dans le lab (nécessite le réseau) :

   ```bash
   cd labs/galaxy/installer-roles/
   ansible-galaxy role install -r requirements.yml -p challenge/deps/roles
   ansible-galaxy collection install -r requirements.yml -p challenge/deps/collections
   ```

   Pytest vérifie que **chaque rôle déclaré est réellement présent** dans
   `challenge/deps/roles/` et que la collection épinglée est installée
   **dans la version exacte demandée** (lecture du MANIFEST.json).

## 🧩 Bloqué ?

```bash
dsoxlab hint galaxy-installer-roles
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes d'installation
exécutées. Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/installer-roles/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean galaxy-installer-roles
```

## 💡 Pour aller plus loin

- `signatures:` sur les collections : vérification GPG cryptographique.
- `ansible-galaxy install -r ... --force` : forcer la réinstallation.
- Vendoriser `challenge/deps/` ou pas ? Le débat lockfile appliqué à Ansible.
