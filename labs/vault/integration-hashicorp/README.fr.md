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
cd $ANSIBLE_TRAINING/labs/vault/integration-hashicorp/

# hvac et la collection sont déclarés par le dépôt : rien à installer à la main
mise install                       # hvac voyage avec ansible-core (mise.toml)
ansible-galaxy collection install -r $ANSIBLE_TRAINING/requirements.yml

# Démarrer Vault : c'est dsoxlab qui s'en charge
dsoxlab run vault-integration-hashicorp
```

Le serveur est déclaré dans `runtime.services` du `lab.yaml` : `dsoxlab run` le
démarre, attend qu'il réponde, y pose `secret/lab82`, et `dsoxlab clean`
l'arrête. Il écoute sur **8201**, pas sur le 8200 par défaut, pour cohabiter
avec un autre Vault déjà présent sur le poste.

Pour OpenBao, changez l'`image:` du service dans le `lab.yaml`.

## ⚙️ Arborescence cible

```text
labs/vault/integration-hashicorp/
├── README.md
├── lab.yaml                      ← déclare le service Vault (image, port, secrets)
└── challenge/
    ├── README.md                 ← contrat du challenge
    ├── solution.yml              ← à écrire : lookup vault_kv2_get + preuve
    └── tests/
        └── test_functional.py    ← tests contre le Vault qui tourne
```

## 📚 Exercice 1 — Démarrer Vault local

```bash
dsoxlab run vault-integration-hashicorp
```

Le lab déclare son serveur, dsoxlab l'exécute :

```yaml
services:
  - name: vault
    image: hashicorp/vault:1.21
    ports: ["8201:8200"]          # 8201 côté hôte : le 8200 est souvent pris
    ready_exec: vault status      # attendre qu'il RÉPONDE, pas que le port ouvre
    post_start:
      - vault kv put secret/lab82 db_password=… api_key=…
```

À l'issue : `http://127.0.0.1:8201`, token `lab82-root`, secrets dans
`secret/lab82`. Rien à exporter, le playbook a les mêmes valeurs par défaut.

🔍 **Observation** : Vault dev mode = **non sécurisé** (pas de TLS, pas de seal, root token statique). **Strictement** pour développement local. En prod : Vault HA + TLS + auto-unseal.

## 📚 Exercice 2 — Stocker des secrets dans Vault

```bash
# Le post_start du service a déjà posé secret/lab82
docker exec dsoxlab-ansible-training-vault vault kv get secret/lab82

# Pour ajouter un secret manuellement :
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault kv put secret/lab82-app \
    db_url=postgres://... \
    db_password=DemoPass123
```

🔍 **Observation** : `kv v2` versionne automatiquement les secrets (history, rollback). `kv v1` est le mode legacy (sans versioning).

## 📚 Exercice 3 — Lookup depuis Ansible

Écrivez le playbook du challenge (cf. [`challenge/README.md`](challenge/README.md)),
puis :

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=lab82-root

ansible-playbook challenge/solution.yml
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
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault vault auth enable approle

# Créer une policy "ansible-readonly"
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault sh -c '
  cat << EOF | vault policy write ansible-readonly -
path "secret/data/lab82" {
  capabilities = ["read"]
}
EOF
'

# Créer un AppRole
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault write auth/approle/role/ansible-app \
    token_policies="ansible-readonly" \
    token_ttl=1h \
    token_max_ttl=4h

# Récupérer role_id et secret_id
ROLE_ID=$(docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault read -field=role_id auth/approle/role/ansible-app/role-id)
SECRET_ID=$(docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
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
# Changez l'image du service dans lab.yaml pour openbao/openbao:latest, puis :
dsoxlab clean vault-integration-hashicorp && dsoxlab run vault-integration-hashicorp

# Le playbook fonctionne IDENTIQUEMENT
ansible-playbook challenge/solution.yml
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
- **Reset isolé** : `dsoxlab clean <id-du-lab>` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi **Vault > Ansible Vault fichier** en production ?

2. Quelle est la **différence concrète** entre HashiCorp Vault et OpenBao en 2026 ?

3. Pourquoi **AppRole** plutôt que **token root** en CI/CD ? Que se passe-t-il si le token root fuite ?

4. Qu'est-ce qu'un **secret lease** en Vault ? Comment Ansible doit-il gérer les leases ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) exige un Vault
qui tourne : les tests lisent les secrets via l'API et vérifient que la
preuve déposée par votre playbook y correspond (longueurs exactes, aucun
secret en clair, idempotence). Sans serveur, ils se mettent en `skip`.

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
