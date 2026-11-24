# Un seul mot de passe vault, et les stagiaires lisent la production

## La situation

Tous les secrets du dépôt sont chiffrés avec le même mot de passe vault, et ce
mot de passe est remis à quiconque doit déployer en dev. Autrement dit : le
stagiaire qui a déployé en dev ce matin peut déchiffrer les identifiants de la
base de production, et rien dans l'outillage ne l'en empêcherait ni ne le
consignerait. Les secrets sont chiffrés. Ils ne sont pas cloisonnés, et ce n'est
pas la même chose.

Votre mission, depuis **control-node.lab** :

1. Donner à chaque environnement sa **propre identité vault étiquetée** et son
   propre mot de passe : détenir la clé de dev ne déchiffre que dev.
2. Ranger les secrets par environnement sous `group_vars/`, dev sur **web1.lab**
   et prod sur **db1.lab**, chaque groupe ne portant que ce qui le concerne.
3. Lancer un seul play sur les **deux** environnements et faire déchiffrer par
   Ansible chaque fichier avec la bonne identité, preuve qu'ils ne se mélangent
   jamais.
4. Lire l'en-tête d'un fichier chiffré pour dire à quelle identité il appartient
   sans le déchiffrer, puis établir qui, dans l'équipe, reçoit quel mot de passe.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-id-multiples/

## 🎯 Challenge — Vault-id séparés `dev` et `prod`

### ✅ Objectif

Démontrer que **2 vault-id différents** (`dev` et `prod`) déchiffrent
correctement leurs **propres fichiers** sur leurs **propres hôtes**.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `web1.lab` (groupe `dev`) | `/tmp/lab79-challenge-web1.lab.txt` | `dev-db.example.com`, `Environnement: dev`, `length: 12` |
| `db1.lab` (groupe `prod`) | `/tmp/lab79-challenge-db1.lab.txt` | `prod-db.example.com`, `Environnement: prod`, `length: 26` |

### 🧩 Bloqué ?

```bash
dsoxlab hint vault-id-multiples
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/vault/id-multiples/challenge/solution.yml \
    --vault-id dev@labs/vault/id-multiples/.vault_password_dev \
    --vault-id prod@labs/vault/id-multiples/.vault_password_prod \
    -i labs/vault/id-multiples/inventory/hosts.yml
```

### 🧪 Validation

```bash
pytest -v labs/vault/id-multiples/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-id-multiples
```

### 💡 Pour aller plus loin

- **3+ vault-id** (dev/staging/prod/secret) : Ansible essaie chaque
  vault-id en cascade jusqu'à trouver le bon.
- **`@prompt`** au lieu de fichier : `--vault-id prod@prompt` pour
  saisir interactivement.
- **`server_list:`** dans `ansible.cfg` pour multi-Galaxy + multi-vault.
