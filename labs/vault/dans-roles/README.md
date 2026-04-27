# Lab 81 — Vault dans un rôle (defaults clair + vars chiffré)

> 💡 **Pré-requis** : `ansible all -m ansible.builtin.ping` répond `pong` sur les 4 VMs.

## 🧠 Rappel

🔗 [**Vault dans les rôles**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-dans-roles/)

Un rôle Ansible peut contenir ses **propres secrets**, chiffrés avec Vault. Le **pattern standard 2026** :

```text
roles/secured_app/
├── defaults/
│   └── main.yml            ← variables PUBLIQUES override-ables (clair)
│                              référencent les vault_* via Jinja indirect
├── vars/
│   └── main.yml            ← secrets CHIFFRÉS (vault_*)
└── tasks/
    └── main.yml            ← utilise les variables publiques
```

**Pattern d'indirection** : `defaults/main.yml` expose `secured_app_db_password` (clair) qui pointe vers `vault_secured_app_db_password` (chiffré dans `vars/`) via Jinja :

```yaml
# defaults/main.yml (clair)
secured_app_db_password: "{{ vault_secured_app_db_password }}"
```

```yaml
# vars/main.yml (CHIFFRÉ)
vault_secured_app_db_password: "RoleDBPasswordLab81!"
```

L'utilisateur du rôle peut **override** `secured_app_db_password` dans son playbook (priorité haute) sans devoir déchiffrer/modifier `vars/main.yml`. **Best of both worlds** : secrets distribués, override possible.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Structurer **`defaults/main.yml` + `vars/main.yml` chiffré** dans un rôle.
2. Utiliser le **pattern d'indirection** `secured_app_X = vault_secured_app_X`.
3. Comprendre pourquoi **`vars/main.yml`** (priorité 18) est un bon emplacement pour les secrets.
4. **Override** une variable de defaults/ depuis le playbook utilisateur.
5. Convention de nommage **`vault_<role>_<var>`**.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/vault/dans-roles/
tree roles/secured_app/
cat roles/secured_app/defaults/main.yml
ansible-vault view roles/secured_app/vars/main.yml --vault-password-file=.vault_password
```

## ⚙️ Arborescence cible

```text
labs/vault/dans-roles/
├── README.md
├── .vault_password                    ← mot de passe vault (mode 0600)
├── playbook.yml                       ← consomme le rôle
└── roles/
    └── secured_app/
        ├── defaults/main.yml          ← variables publiques (CLAIR)
        ├── vars/main.yml              ← secrets (CHIFFRÉ vault)
        ├── tasks/main.yml             ← logique du rôle
        └── meta/main.yml              ← metadata
```

## 📚 Exercice 1 — Inspecter le pattern d'indirection

```bash
cat roles/secured_app/defaults/main.yml
```

Sortie :

```yaml
secured_app_user: appuser                                              # ← clair
secured_app_db_password: "{{ vault_secured_app_db_password }}"         # ← indirection
secured_app_api_token: "{{ vault_secured_app_api_token }}"
```

🔍 **Observation** : `defaults/main.yml` ne contient **aucun secret en clair**. Il **pointe** vers les variables `vault_*` qui sont chiffrées dans `vars/main.yml`.

## 📚 Exercice 2 — Voir le contenu chiffré

```bash
ansible-vault view roles/secured_app/vars/main.yml --vault-password-file=.vault_password
```

Sortie :

```yaml
vault_secured_app_db_password: "RoleDBPasswordLab81!"
vault_secured_app_api_token: "role_api_tok_lab81_xyz"
```

🔍 **Observation** : `vars/main.yml` contient les **vraies valeurs**, chiffrées. Le préfixe `vault_*` est convention pour distinguer ces variables internes.

## 📚 Exercice 3 — Lancer le playbook

```bash
ansible-playbook --vault-password-file=.vault_password \
  -e "ansible_roles_path=./roles" \
  playbook.yml
```

Sortie : `changed=1` sur web1.lab. Le rôle a déchiffré et utilisé les secrets.

```bash
ssh ansible@web1.lab "sudo cat /tmp/lab81-secured-app.txt"
```

## 📚 Exercice 4 — Override d'une variable defaults/

Dans `playbook.yml`, ajouter :

```yaml
- name: Démo override
  hosts: web1.lab
  roles:
    - role: secured_app
      vars:
        secured_app_port: 12345
```

🔍 **Observation** : `secured_app_port` est override sans toucher au rôle. **`secured_app_db_password`** (qui pointe sur `vault_*`) **ne peut pas** être override aussi facilement (`vault_*` est dans `vars/main.yml` priorité 18).

## 📚 Exercice 5 — Pourquoi vars/ et pas defaults/ pour le secret ?

Si on mettait `vault_secured_app_db_password` dans `defaults/main.yml` (priorité 2), un utilisateur pourrait le **override silencieusement** depuis son playbook (priorité 13) — risque de fuite si la valeur override est mal gérée.

En le mettant dans `vars/main.yml` (priorité 18), seul `--extra-vars` (priorité 22) peut l'override — comportement **explicite et controllé**.

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

1. Pourquoi le **pattern d'indirection** (defaults clair → vars chiffré) plutôt que tout directement dans `vars/` ?

2. Comment **rotater** `vault_secured_app_db_password` sans casser le rôle pour les utilisateurs ?

3. Si un utilisateur veut **override** le password en CLI, comment fait-il ? (Indice : `--extra-vars` priorité 22)

4. Pourquoi **convention `vault_<role>_<var>`** ? Que se passe-t-il si 2 rôles utilisent `vault_db_password` ?

## 🚀 Challenge final

Le challenge ([`challenge/solution.yml`](challenge/solution.yml)) déploie sur `db1.lab` avec un override de `secured_app_port: 9999`. Tests automatisés (5 tests dont vérification que les secrets vault sont bien déchiffrés).

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`vars/<distro>.yml` chiffré** : secrets différents par OS (mandatory rare).
- **Multi vault-id dans un rôle** : un mot de passe par environnement même au sein du rôle.
- **Externaliser dans HashiCorp Vault** (lab 82) : éviter de stocker les secrets en repo.
- **Passbolt** (lab 83) : alternative team-friendly pour secrets équipe.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile=production roles/
```

Le linter vérifie le pattern (FQCN, no_log si nécessaire). Il ne touche pas aux secrets vault.
