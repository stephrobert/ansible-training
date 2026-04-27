# Lab 82 — Intégration HashiCorp Vault / OpenBao

> 💡 **Pré-requis** :
> - Podman ou Docker installé.
> - Collection `community.hashi_vault` : `ansible-galaxy collection install community.hashi_vault`.
> - Le module Python `hvac` : `pip install hvac` (ou `pipx inject ansible hvac`).

## 🧠 Rappel

🔗 [**HashiCorp Vault / OpenBao avec Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-hashicorp-vault/)

**Limites d'Ansible Vault** (labs 77-81) :

- Mot de passe vault stocké quelque part (fichier, env var) — risque humain.
- Pas de **rotation centralisée** des secrets.
- Pas d'**audit logs** détaillés (qui a accédé à quel secret quand).
- Pas de **leases** ou de TTL sur les secrets.

**HashiCorp Vault** (et son fork open-source **OpenBao**) résolvent ces problèmes : centralisation, rotation, audit, TTL, intégrations Cloud (AWS IAM, Azure AD, K8s service accounts).

**API quasi identique** entre HashiCorp Vault et OpenBao — un même playbook Ansible fonctionne avec les deux. Choix selon contexte :

- **HashiCorp Vault** : licence BSL (commerciale au-delà d'un seuil), enterprise features.
- **OpenBao** : fork 100 % open-source (MPL-2.0), gouvernance Linux Foundation.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Démarrer** un Vault local en mode dev (Docker/Podman).
2. **Stocker** un secret via `vault kv put`.
3. **Récupérer** le secret depuis Ansible avec **`community.hashi_vault.vault_kv2_get`**.
4. Comprendre la **différence** entre `vault_kv1_get` et `vault_kv2_get`.
5. **Authentification** : token, AppRole, JWT, Kubernetes.
6. **Workflow CI/CD** : utiliser Vault pour ne pas stocker de secrets dans Git.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/vault/integration-hashicorp/

# Installer hvac (client Python Vault)
pipx inject ansible hvac

# Installer la collection
ansible-galaxy collection install community.hashi_vault

# Démarrer Vault en mode dev
./setup-vault.sh                   # HashiCorp Vault par défaut

# Pour OpenBao :
IMAGE=openbao/openbao:latest ./setup-vault.sh
```

## ⚙️ Arborescence cible

```text
labs/vault/integration-hashicorp/
├── README.md
├── setup-vault.sh                ← démarre Vault dev en container
├── playbook.yml                  ← lookup vault_kv2_get
└── challenge/
    └── tests/
        └── test_vault_integration.py   ← tests structure
```

## 📚 Exercice 1 — Démarrer Vault local

```bash
./setup-vault.sh
```

Sortie :

```text
[setup-vault] Lancement de hashicorp/vault:latest...
[setup-vault] OK — Vault disponible sur http://localhost:8200
  Token : lab82-root
  Path  : secret/lab82

Variables d'env à exporter pour le playbook :
  export VAULT_ADDR=http://localhost:8200
  export VAULT_TOKEN=lab82-root
```

🔍 **Observation** : Vault dev mode = **non sécurisé** (pas de TLS, pas de seal, root token statique). **Strictement** pour développement local. En prod : Vault HA + TLS + auto-unseal.

## 📚 Exercice 2 — Stocker des secrets dans Vault

```bash
# Le script setup-vault.sh a déjà posé secret/lab82
podman exec vault-lab82 vault kv get secret/lab82

# Pour ajouter un secret manuellement :
podman exec -e VAULT_TOKEN=lab82-root vault-lab82 \
  vault kv put secret/lab82-app \
    db_url=postgres://... \
    db_password=DemoPass123
```

🔍 **Observation** : `kv v2` versionne automatiquement les secrets (history, rollback). `kv v1` est le mode legacy (sans versioning).

## 📚 Exercice 3 — Lookup depuis Ansible

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=lab82-root

ansible-playbook playbook.yml \
  -e "hashi_vault_url=http://localhost:8200" \
  -e "hashi_vault_token=lab82-root"
```

Sortie :

```text
TASK [debug] **************
ok: [localhost] =>
  msg: "DB password length: 14"

PLAY RECAP ****************
localhost : ok=2 changed=1 unreachable=0 failed=0
```

🔍 **Observation** : le playbook **ne contient aucun secret en clair**. La `lookup` récupère le secret au runtime depuis Vault. Audit logs Vault tracent qui a accédé.

## 📚 Exercice 4 — Authentification AppRole (production)

En prod, **on n'utilise pas le token root**. Pattern recommandé : **AppRole**.

```bash
# Activer AppRole
podman exec -e VAULT_TOKEN=lab82-root vault-lab82 vault auth enable approle

# Créer une policy "ansible-readonly"
podman exec -e VAULT_TOKEN=lab82-root vault-lab82 sh -c '
  cat << EOF | vault policy write ansible-readonly -
path "secret/data/lab82" {
  capabilities = ["read"]
}
EOF
'

# Créer un AppRole
podman exec -e VAULT_TOKEN=lab82-root vault-lab82 \
  vault write auth/approle/role/ansible-app \
    token_policies="ansible-readonly" \
    token_ttl=1h \
    token_max_ttl=4h

# Récupérer role_id et secret_id
ROLE_ID=$(podman exec -e VAULT_TOKEN=lab82-root vault-lab82 \
  vault read -field=role_id auth/approle/role/ansible-app/role-id)
SECRET_ID=$(podman exec -e VAULT_TOKEN=lab82-root vault-lab82 \
  vault write -field=secret_id -f auth/approle/role/ansible-app/secret-id)

echo "role_id=$ROLE_ID, secret_id=$SECRET_ID"
```

Le playbook utilise alors `auth_method: approle` :

```yaml
- name: Lookup avec AppRole
  vars:
    db_password: "{{ lookup('community.hashi_vault.vault_kv2_get',
                            'lab82',
                            engine_mount_point='secret',
                            url=vault_url,
                            auth_method='approle',
                            role_id=role_id,
                            secret_id=secret_id).secret.db_password }}"
```

🔍 **Observation** : le `secret_id` peut être **éphémère** (TTL court). Le `role_id` est **publique** (peut être commité). Pattern recommandé en CI/CD.

## 📚 Exercice 5 — Différences HashiCorp Vault vs OpenBao

Lancer le même playbook avec **OpenBao** :

```bash
podman stop vault-lab82
IMAGE=openbao/openbao:latest ./setup-vault.sh

# Le playbook fonctionne IDENTIQUEMENT
ansible-playbook playbook.yml \
  -e "hashi_vault_url=http://localhost:8200" \
  -e "hashi_vault_token=lab82-root"
```

🔍 **Observation** : aucune modification du playbook. **API compatible**. Choisir Vault ou OpenBao selon licensing — pas selon fonctionnalités (95 % identiques).

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab + un serveur HashiCorp Vault ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi **Vault > Ansible Vault fichier** en production ?

2. Quelle est la **différence concrète** entre HashiCorp Vault et OpenBao en 2026 ?

3. Pourquoi **AppRole** plutôt que **token root** en CI/CD ? Que se passe-t-il si le token root fuite ?

4. Qu'est-ce qu'un **secret lease** en Vault ? Comment Ansible doit-il gérer les leases ?

## 🚀 Challenge final

Le challenge ([`challenge/`](challenge/)) valide la structure du lab via 6 tests pytest (script présent, support OpenBao, lookup correcte, kv v2, engine_mount_point, pas de secret en clair).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Auth Kubernetes** : Vault s'intègre avec les service accounts K8s pour rotation auto.
- **Auth AWS IAM / Azure AD / GCP** : pas de credentials à stocker.
- **Dynamic secrets** : Vault génère des credentials DB éphémères (PostgreSQL, MySQL, MongoDB).
- **Vault + Ansible Tower / AAP** : Vault Credential Type intégré.
- **Lab 83** : alternative team-friendly avec Passbolt (gestionnaire de mots de passe d'équipe).

## 🔍 Sécurité — bonnes pratiques 2026

- **Pas de token en clair** dans `playbook.yml` — toujours via env vars (`VAULT_TOKEN`).
- **AppRole** en CI/CD avec `secret_id` éphémère (renouvelé par job).
- **TLS mandatory** en production (`https://`, certificat pinné).
- **Audit log** activé sur tous les Vault prod (`vault audit enable file file_path=...`).
- **Rotation périodique** des `secret_id` AppRole.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/vault/integration-hashicorp/lab.yml
ansible-lint labs/vault/integration-hashicorp/challenge/solution.yml
ansible-lint --profile production labs/vault/integration-hashicorp/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
