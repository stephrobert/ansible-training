# 🎯 Challenge — Passbolt : récupérer un secret via la collection `anatomicjc.passbolt`

## ✅ Objectif

Démontrer une intégration Ansible avec **Passbolt** (gestionnaire de
mots de passe d'équipe basé OpenPGP). Le test valide la **structure**
du projet (pas l'exécution), car Passbolt requiert une clé OpenPGP
personnelle non automatisable.

| Fichier | Attente |
| --- | --- |
| `setup-passbolt.sh` | Exécutable. Lance `podman run` pour `passbolt/passbolt` + `mariadb`. |
| `playbook.yml` | Utilise `anatomicjc.passbolt.passbolt`. Variables `passbolt_uri`, `passbolt_private_key`, `passbolt_passphrase`. `no_log: true` sur les tâches sensibles. **Aucun** secret en dur. |
| `README.md` | Explique le positionnement vs HashiCorp Vault (mention `passbolt` + `OpenPGP`). |

## 🧩 Indices

### Étape 1 — Démarrer Passbolt local

```bash
cd labs/vault/integration-passbolt/
./setup-passbolt.sh                # → containers passbolt + mariadb-passbolt
# Suivre l'URL de setup web pour créer l'admin + générer la clé OpenPGP
```

### Étape 2 — Préparer la clé OpenPGP côté apprenant

```bash
gpg --gen-key                       # nom + email + passphrase
gpg --armor --export-secret-key <fingerprint> > .passbolt-private.asc
```

### Étape 3 — Compléter `playbook.yml`

```yaml
---
- name: Lab 83 — récupérer un secret depuis Passbolt
  hosts: localhost
  gather_facts: false
  vars:
    passbolt_uri: ???                 # URL de votre instance Passbolt locale
    passbolt_private_key: "{{ lookup('file', '.passbolt-private.asc') }}"
    passbolt_passphrase: "{{ lookup('env', 'PASSBOLT_PASSPHRASE') }}"

  tasks:
    - name: Récupérer un secret par son nom
      anatomicjc.passbolt.passbolt:
        name: lab83-app
      register: secret
      no_log: ???

    - name: Afficher la longueur (preuve de récupération sans exposer le secret)
      ansible.builtin.debug:
        msg: "Password length: {{ secret.password | length }}"
      no_log: ???
```

> 💡 **Pièges** :
>
> - **Clé OpenPGP obligatoire et personnelle** : sans clé exportée, le
>   playbook ne peut **pas** authentifier — c'est ce qui rend Passbolt
>   non-automatisable "out of the box". Pour un bot, prévoyez un compte
>   dédié sans MFA + clé dédiée.
> - **`PASSBOLT_PASSPHRASE` en variable d'env** : ne jamais l'inscrire
>   dans le playbook. Le test scanne le YAML et rejette `passbolt123`,
>   `demopass`, `rootlab83` (chaînes en dur interdites).
> - **`no_log: true`** sur la tâche `passbolt:` ET la tâche `debug:`
>   (sinon le secret apparaît en clair).
> - **Test structurel** : le test ne lance pas de container, il valide
>   que `setup-passbolt.sh` est exécutable et que `playbook.yml` utilise
>   les bonnes variables. Vous pouvez le passer **sans** avoir un Passbolt
>   réel.

## 🚀 Lancement

Pré-requis : avoir un compte Passbolt + clé OpenPGP exportée.

```bash
ansible-galaxy collection install anatomicjc.passbolt
export PASSBOLT_PASSPHRASE='???'
ansible-playbook labs/vault/integration-passbolt/playbook.yml
```

## 🧪 Validation

Le test pytest est **structurel** (fichiers + leur contenu) :

```bash
pytest -v labs/vault/integration-passbolt/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/vault/integration-passbolt/ clean
```

## 💡 Pour aller plus loin

- **Passbolt vs HashiCorp Vault** : Passbolt cible les **équipes
  humaines** (UI riche, partage par groupe), Vault cible le **runtime**
  (auto-scaling secrets pour services).
- **MFA Passbolt** : possible mais incompatible avec une clé exportée
  pour automation — utiliser un compte dédié sans MFA pour les bots.
- **Backup de la clé OpenPGP** : critique. Sans elle, vos secrets sont
  perdus à jamais.
