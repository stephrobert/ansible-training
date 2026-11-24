# Il faut le mot de passe vault juste pour lire un numéro de port

## La situation

L'accueil d'un nouveau a buté cette semaine. Une collègue voulait savoir sur quel
port écoutent les serveurs web. Cette valeur est publique, sans enjeu, et enfermée
dans un fichier `group_vars` chiffré, à côté d'un token d'administration : lui
répondre imposait de lui confier le mot de passe vault. La configuration de
l'équipe et ses secrets vivent dans le même fichier, et c'est le secret qui dicte
les règles d'accès aux deux.

Votre mission, depuis **control-node.lab** :

1. Couper chaque `group_vars/<groupe>/` en deux : la configuration publique en
   clair, les secrets dans un **fichier chiffré séparé** chargé au même endroit.
2. Adopter une convention de nommage qui rende une variable sensible
   reconnaissable au premier coup d'œil, sans rien ouvrir.
3. Vérifier qu'Ansible fusionne les deux fichiers de façon transparente au
   runtime : prouver sur **web1.lab** que valeurs publiques et secrets
   déchiffrés, venus du groupe `all` comme du groupe web, atterrissent tous dans
   le même play.
4. Constater le gain : `main.yml` reste lisible, et ses diffs restent relisibles.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/playbooks-mixtes/

## 🎯 Challenge — Mixer `main.yml` (clair) + `vault.yml` (chiffré) par groupe

### ✅ Objectif

Démontrer le pattern production : un `group_vars/<grp>/main.yml` avec
**variables non sensibles en clair**, et un `group_vars/<grp>/vault.yml`
**chiffré** avec les mots de passe / tokens. Les deux fichiers sont
chargés automatiquement par Ansible au runtime.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `web1.lab` | `/tmp/lab80-challenge.txt` | `Env: lab80`, `Port: 80`, `Admin token starts: lab80_admi`, `Web secret length: 20` |

### 🧩 Bloqué ?

```bash
dsoxlab hint vault-playbooks-mixtes
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/vault/playbooks-mixtes/challenge/solution.yml \
    --vault-password-file=labs/vault/playbooks-mixtes/.vault_password
```

### 🧪 Validation

```bash
pytest -v labs/vault/playbooks-mixtes/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-playbooks-mixtes
```

### 💡 Pour aller plus loin

- **Convention** : préfixer les variables vault par `vault_` pour
  documenter leur sensibilité.
- **Deux fichiers vs un fichier `!vault |` inline** : préférer la
  séparation sur des projets multi-équipe.
- **Précédence** : `group_vars/<grp>/*` > `group_vars/all/*` —
  `webservers` peut overrider une valeur de `all`.
