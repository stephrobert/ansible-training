# Lab 94 — `requirements.yml` complet (Galaxy + Git + signatures GPG)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**`requirements.yml` complet**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/requirements-yml/)

Un projet Ansible mature **versionne ses dépendances** dans un fichier **`requirements.yml`** unique. Il liste les **collections** et **rôles** utilisés, leur **source** (Galaxy, Git, URL tarball, chemin local), leur **version pinnée** (semver strict), et optionnellement leurs **signatures GPG** pour vérification d'intégrité.

**Pourquoi c'est critique en 2026** :
- Les **builds reproductibles** d'Execution Environments dépendent de `requirements.yml`.
- Le **scan supply-chain** (Trivy, cosign, signatures) cible ce fichier.
- Un projet sans pinning **dérive** au fil des jours et casse en prod sans avertissement.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un **`requirements.yml`** avec **4 sources** différentes (Galaxy, Git, URL, chemin local).
2. **Pinner** strictement chaque version (semver `version: "X.Y.Z"`).
3. Installer toutes les collections avec **`ansible-galaxy collection install -r`**.
4. Vérifier l'intégrité avec **`ansible-galaxy collection verify`**.
5. Comprendre les **signatures GPG** détachées (`signatures:` dans `requirements.yml`).
6. Configurer **`ansible.cfg [galaxy]`** pour cibler **plusieurs serveurs** (Galaxy + Hub privé).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible-galaxy --version
mkdir -p labs/collections/requirements/local_collections
rm -rf labs/collections/requirements/.collections-cache
```

## ⚙️ Arborescence cible

```text
labs/collections/requirements/
├── README.md                       ← ce fichier (tuto guidé)
├── Makefile                        ← cible clean
└── challenge/
    ├── README.md                   ← consigne challenge avec squelette
    └── tests/
        └── test_requirements.py
```

L'apprenant écrit lui-même `requirements.yml`, `lab.yml`, et `challenge/solution.yml`.

## 📚 Exercice 1 — Source Galaxy avec pinning strict

Créer `requirements.yml` :

```yaml
---
collections:
  # Source Galaxy par défaut (galaxy.ansible.com)
  - name: ansible.posix
    version: "2.0.0"

  - name: community.general
    version: "10.5.0"

  - name: kubernetes.core
    version: "5.1.1"
```

```bash
ansible-galaxy collection install \
  -r labs/collections/requirements/requirements.yml \
  -p labs/collections/requirements/local_collections \
  --force
```

🔍 **Observation** : **`-p`** force l'installation dans un chemin **local au projet** (pas dans `~/.ansible/`). Permet **l'isolation** entre projets et la **reproductibilité** (le chemin est versionné).

## 📚 Exercice 2 — Source Git avec tag, branche ou SHA

Ajouter à `requirements.yml` :

```yaml
collections:
  - name: https://github.com/ansible-collections/community.docker.git
    type: git
    version: "4.0.0"           # tag Git
```

Variantes acceptées dans **`version:`** :

| Format | Exemple | Cas d'usage |
|--------|---------|-------------|
| Tag | `version: v1.2.3` | Production stable (recommandé) |
| Branche | `version: main` | Dev rapide (déconseillé en prod) |
| SHA40 | `version: abc1234...` | Reproductibilité absolue |

🔍 **Observation** : **Git source** est utile pour les collections **non publiées sur Galaxy** (privées d'entreprise, fork interne, contributions en cours). En prod, **toujours** pinner par **tag** ou **SHA**, jamais par branche.

## 📚 Exercice 3 — Source URL tarball

```yaml
collections:
  - name: https://example.com/dist/acme-webapp-1.4.2.tar.gz
    type: url
```

🔍 **Observation** : utile pour les **distributions internes airgap** où Galaxy n'est pas accessible. Pré-builder le tarball avec `ansible-galaxy collection build`, le poser sur un serveur HTTP local, le pointer ici.

## 📚 Exercice 4 — Source chemin local (dev)

```yaml
collections:
  - name: /home/bob/dev/acme.webapp
    type: dir
```

🔍 **Observation** : **mode dev** où on travaille sur sa collection en local. Modification immédiatement visible — pas besoin de rebuilder/réinstaller à chaque change. À retirer en prod (chemin absolu non portable).

## 📚 Exercice 5 — Lancer l'installation

```bash
ansible-galaxy collection install \
  -r labs/collections/requirements/requirements.yml \
  -p labs/collections/requirements/local_collections \
  --force
```

Sortie typique :

```text
Starting galaxy collection install process
Process install dependency map
Starting collection install process
Downloading https://galaxy.ansible.com/.../ansible-posix-2.0.0.tar.gz to ...
Installing 'ansible.posix:2.0.0' to '.../local_collections/ansible_collections/ansible/posix'
Cloning into 'community.docker'...
...
ansible.posix:2.0.0 was installed successfully
community.general:10.5.0 was installed successfully
community.docker:4.0.0 was installed successfully
```

🔍 **Observation** : `--force` réinstalle **même si la version est déjà présente**. Utile en dev pour s'assurer qu'on a bien la version pinnée. En CI, **omettre** `--force` (plus rapide).

## 📚 Exercice 6 — `ANSIBLE_COLLECTIONS_PATH`

Une fois installées en local, il faut indiquer à Ansible où chercher :

```bash
export ANSIBLE_COLLECTIONS_PATH=labs/collections/requirements/local_collections
ansible-galaxy collection list -p labs/collections/requirements/local_collections
```

Ou dans `ansible.cfg` :

```ini
[defaults]
collections_path = labs/collections/requirements/local_collections
```

🔍 **Observation** : la variable d'env **`ANSIBLE_COLLECTIONS_PATH`** est un `:` separator (comme `$PATH`). Permet d'enchaîner plusieurs paths (système + projet) avec priorité.

## 📚 Exercice 7 — Vérification d'intégrité (`verify`)

```bash
ansible-galaxy collection verify \
  -r labs/collections/requirements/requirements.yml \
  -p labs/collections/requirements/local_collections
```

Sortie :

```text
Verifying 'ansible.posix:2.0.0'.
Found ansible.posix at /home/.../local_collections/ansible_collections/ansible/posix
Successfully verified that checksums for 'ansible.posix:2.0.0' match the remote collection
```

🔍 **Observation** : `verify` compare les **checksums** des fichiers locaux avec ceux du serveur. **Détecte une corruption** (disque, modification manuelle) ou une **substitution** (attaque supply-chain). À automatiser en CI.

## 📚 Exercice 8 — Signatures GPG détachées

Pour les collections **certifiées Red Hat** ou les forks privés, on ajoute des signatures :

```yaml
collections:
  - name: community.general
    version: "10.5.0"
    signatures:
      - https://galaxy.ansible.com/api/v3/.../detached_signature.asc
      - file:///etc/ansible/sigs/community-general-10.5.0.asc
```

```bash
ansible-galaxy collection install \
  -r requirements.yml \
  --keyring /etc/ansible/trustedkeys.gpg
```

Variables associées :

| Variable | Effet |
|----------|-------|
| `GALAXY_REQUIRED_VALID_SIGNATURE_COUNT` | Nombre minimum de signatures valides (`+1`, `+all`) |
| `GALAXY_DISABLE_GPG_VERIFY` | `1` désactive (debug uniquement) |
| `--keyring` | Chemin vers le keyring GPG de confiance |

🔍 **Observation** : exige **`ansible-core ≥ 2.13`**. Sans `--keyring`, l'install **échoue** si signatures déclarées. Pattern essentiel pour **airgap signé** (verify offline avec `--offline`).

## 🔍 Observations à noter

- **`requirements.yml`** centralise toutes les dépendances Ansible.
- **4 sources** : Galaxy (default), `type: git`, `type: url`, `type: dir`.
- **Pinning strict** par **tag** ou **SHA** — jamais par branche en prod.
- **`-p <chemin>`** isole les collections au niveau projet.
- **`ansible-galaxy collection verify`** détecte les corruptions et les substitutions.
- **Signatures GPG** via `signatures:` + `--keyring` pour la chaîne supply-chain.

## 🤔 Questions de réflexion

1. Quel est le risque de **`type: git, version: main`** en production ?
2. Comment mettre à jour **automatiquement** les versions pinnées ? (Indice : Renovate / Dependabot).
3. À quoi sert **`build_ignore:`** dans `galaxy.yml` ? Quel est l'équivalent côté `requirements.yml` ?
4. Pourquoi un **registre privé** (Galaxy NG / Automation Hub) est-il préférable à Git pour les forks internes ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — écrire un `requirements.yml` qui combine **3 sources** (Galaxy + Git + URL) avec pinning strict, l'installer via Ansible, et déposer la liste des collections sur `db1.lab`.

## 💡 Pour aller plus loin

- **Lab 95** : créer **votre propre collection** (init + structure + galaxy.yml).
- **Lab 96** : pipeline CI matrice ansible-core × Python.
- **Renovate** pour bumper auto les versions pinnées.
- **Galaxy NG** : déployer un Automation Hub privé local.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/collections/requirements/lab.yml
ansible-lint --profile production labs/collections/requirements/challenge/solution.yml
```
