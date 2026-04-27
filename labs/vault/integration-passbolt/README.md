# Lab 83 — Intégration Passbolt (gestionnaire d'équipe OpenPGP)

> 💡 **Pré-requis** :
> - Podman installé.
> - Collection `anatomicjc.passbolt` : `ansible-galaxy collection install anatomicjc.passbolt`.
> - Module Python `py-passbolt` : `pip install py-passbolt` (ou `pipx inject ansible py-passbolt`).
> - GnuPG (`gpg`) pour générer la clé OpenPGP utilisateur.

## 🧠 Rappel

🔗 [**Intégration Passbolt avec Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-passbolt/)

**Passbolt** est un gestionnaire de mots de passe **orienté équipes** sous licence open-source (AGPL). Contrairement à HashiCorp Vault (lab 82), il vise un public différent :

| Aspect | HashiCorp Vault / OpenBao | Passbolt |
|--------|---------------------------|----------|
| **Cas d'usage** | Secrets infra, dynamic secrets, CI/CD | Mots de passe d'équipe (humains + machines) |
| **Modèle** | Token / AppRole / IAM | Clé OpenPGP par utilisateur |
| **Audit** | Lease + audit log natifs | Activity log + email notifications |
| **UI** | Optionnelle (CLI-first) | Web UI riche (browser + extension) |
| **Partage** | Policies HCL | Groupes + rôles + permissions par ressource |
| **Rotation** | Automatique (dynamic secrets) | Manuelle (UI) |

**Quand choisir Passbolt** ? Quand l'équipe humaine doit **partager des mots de passe** (admin db, comptes SaaS, certificats, API keys de tiers) et qu'on veut un workflow accessible **non-DevOps** (lecture par marketing, support, etc.) tout en gardant Ansible capable de récupérer ces secrets côté infrastructure.

**Quand garder HashiCorp Vault** ? Pour les secrets **dynamiques**, les **certificats X.509 PKI**, les **dynamic database credentials**, les besoins de **TTL automatique** et l'intégration **Cloud IAM**.

⚠️ **Pas redondant** avec Vault : les deux outils répondent à des besoins **complémentaires**. Beaucoup d'organisations utilisent **les deux** (Passbolt pour humains, Vault pour infra).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Démarrer** un Passbolt CE local (Podman + MariaDB).
2. Comprendre l'authentification **OpenPGP** (clé privée + passphrase).
3. **Récupérer** un secret Passbolt depuis Ansible avec la collection **`anatomicjc.passbolt`**.
4. Comparer **Passbolt** et **HashiCorp Vault** sur des cas concrets.
5. **Sécuriser** la clé privée OpenPGP (pas de commit Git).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/vault/integration-passbolt/

# Installer la collection Passbolt
ansible-galaxy collection install anatomicjc.passbolt

# Installer py-passbolt (client Python)
pipx inject ansible py-passbolt

# Démarrer Passbolt local
./setup-passbolt.sh
```

## ⚙️ Arborescence cible

```text
labs/vault/integration-passbolt/
├── README.md
├── setup-passbolt.sh                ← démarre Passbolt + MariaDB en containers
├── playbook.yml                     ← lookup anatomicjc.passbolt.passbolt
└── challenge/
    └── tests/
        └── test_passbolt_integration.py   ← tests structure
```

## 📚 Exercice 1 — Démarrer Passbolt local

```bash
./setup-passbolt.sh
```

Sortie typique :

```text
[setup-passbolt] Création du réseau passbolt-lab83...
[setup-passbolt] Démarrage MariaDB...
[setup-passbolt] Démarrage Passbolt CE...
[setup-passbolt] Initialisation admin user...

[setup-passbolt] OK — Passbolt disponible sur https://localhost:8443
```

🔍 **Observation** : Passbolt = **2 containers** (DB + app). Architecture proche d'une app Rails/Django classique. Pas de cluster HA inclus dans la version CE.

## 📚 Exercice 2 — Compléter l'inscription via UI

La commande `register_user` retourne un **lien d'inscription unique**. L'inscription se fait dans le navigateur car elle nécessite la **génération d'une clé OpenPGP** côté client (jamais transmise au serveur).

```text
1. Ouvrir https://localhost:8443 (accepter le self-signed)
2. Cliquer le lien d'inscription retourné par register_user
3. Choisir une passphrase forte (sera demandée à chaque déchiffrement)
4. L'extension Passbolt génère la clé GPG dans le navigateur
5. TÉLÉCHARGER le fichier de récupération (kit) — IRRÉCUPÉRABLE sinon
```

🔍 **Observation cruciale** : la **clé privée** ne quitte **jamais** le navigateur de l'utilisateur. Le serveur ne stocke que la **clé publique**. Si vous perdez la clé privée + le kit de récupération → **secrets perdus à jamais**. C'est une **différence majeure** avec Vault (où le serveur a "tout").

## 📚 Exercice 3 — Exporter la clé privée pour Ansible

Pour qu'Ansible utilise Passbolt, on a besoin de la clé privée d'un utilisateur dédié (pattern recommandé : créer un user `ansible@lab83.local` séparé de `admin@`).

```bash
# Créer un user Ansible dédié
podman exec passbolt-app-lab83 su -m -c \
  "/usr/share/php/passbolt/bin/cake passbolt register_user \
    -u ansible@lab83.local -f Ansible -l Bot -r user" www-data

# Compléter l'inscription via UI, puis exporter sa clé privée :
mkdir -p .passbolt
# (export GPG depuis le browser → coller dans .passbolt/private.key)
chmod 600 .passbolt/private.key

# .gitignore obligatoire :
echo ".passbolt/" >> ../../.gitignore
```

🔍 **Observation** : un user Ansible **dédié** simplifie l'audit (qui a accédé : Ansible vs un humain). Permissions limitées sur les groupes "Infrastructure" uniquement.

## 📚 Exercice 4 — Stocker un secret de démo dans Passbolt

Via UI :

```text
1. Se connecter en tant que admin@lab83.local
2. New password → name=lab83-demo, password=DemoPassbolt2026!
3. Partager avec ansible@lab83.local (lecture seule)
```

Via API REST (pour automatisation, plus avancé) : voir [`anatomicjc.passbolt`](https://galaxy.ansible.com/ui/repo/published/anatomicjc/passbolt/) collection.

🔍 **Observation** : **partage explicite** par ressource. Ansible ne voit **que** les secrets explicitement partagés avec lui. Pattern **least-privilege** par construction.

## 📚 Exercice 5 — Lookup depuis Ansible

```bash
export PASSBOLT_URI=https://localhost:8443
export PASSBOLT_PRIVATE_KEY="$(cat .passbolt/private.key)"
export PASSBOLT_PASSPHRASE="votre-passphrase"

ansible-playbook playbook.yml \
  -e "passbolt_uri=$PASSBOLT_URI" \
  -e "passbolt_private_key=$PASSBOLT_PRIVATE_KEY" \
  -e "passbolt_passphrase=$PASSBOLT_PASSPHRASE"
```

Sortie :

```text
TASK [Récupérer le secret 'lab83-demo' depuis Passbolt] ***
ok: [localhost]

TASK [Afficher uniquement la longueur du secret] ***
ok: [localhost] => 
  msg: "Secret length: 19"
```

🔍 **Observation** : `no_log: true` sur la `set_fact` pour ne **jamais** logger la valeur claire. Le `debug` final n'expose que la longueur.

## 📚 Exercice 6 — Quand Passbolt complète Ansible Vault

Pattern réaliste : **Passbolt** stocke le **mot de passe** Ansible Vault.

```bash
# 1. L'admin stocke "ansible-vault-master-password" dans Passbolt
# 2. Le pipeline CI récupère ce mot de passe via lookup Passbolt
# 3. Le pipeline déchiffre les fichiers Ansible Vault avec ce password
# 4. Ansible exécute les playbooks
```

🔍 **Observation** : **chaîne de confiance**. Passbolt protège le **master password**, qui protège les **vault files**. Rotation simple : changer le mot de passe vault → rechiffrer → mettre à jour dans Passbolt.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab + une instance Passbolt ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi **Passbolt** plutôt qu'un coffre `pass(1)` GPG partagé via Git ?

2. Que se passe-t-il si le **kit de récupération** Ansible est perdu et que la passphrase est oubliée ?

3. Comment **rotater** un mot de passe stocké dans Passbolt sans casser les playbooks en cours ?

4. **Passbolt vs HashiCorp Vault** : pour un Bastion SSH partagé entre 5 admins, lequel choisir ? Pourquoi ?

## 🚀 Challenge final

Le challenge ([`challenge/tests/`](challenge/tests/)) valide la structure du lab via 7 tests pytest (script présent, podman + mariadb, lookup correct, no_log, pas de secret en clair, variables passbolt_*, README mentionne OpenPGP).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Passbolt PRO** : SSO (SAML, OIDC), MFA, audit logs avancés, teams.
- **Self-hosted en prod** : Passbolt Helm chart (K8s) ou Ansible role officiel `passbolt.passbolt_collection`.
- **API REST + JWT** : alternative à OpenPGP pour intégrations machine-to-machine (Passbolt 4.x+).
- **Browser extension** : remplit auto les forms web (différenciateur vs Vault).
- **Combo gagnant** : Passbolt (humains) + HashiCorp Vault (infra/dynamic) + Ansible Vault (configs sensibles versionnées).

## 🔍 Sécurité — bonnes pratiques 2026

- **Clé privée OpenPGP** : `chmod 600`, jamais commitée, idéalement dans un keystore (gnome-keyring, macOS Keychain).
- **Passphrase** : passée par variable d'env, jamais en CLI (`ps aux` la révélerait).
- **TLS valide** en prod (Let's Encrypt). Le self-signed du lab est uniquement pour dev local.
- **MFA** sur tous les comptes humains (TOTP gratuit en CE).
- **Audit log activé** (Passbolt 4.5+) : qui a accédé à quel secret, quand, depuis quelle IP.
- **Backup base** : la DB MariaDB contient secrets chiffrés + clés publiques. Pas suffisant seul — chaque user doit aussi backup sa **clé privée + kit de récupération**.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/vault/integration-passbolt/lab.yml
ansible-lint labs/vault/integration-passbolt/challenge/solution.yml
ansible-lint --profile production labs/vault/integration-passbolt/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
