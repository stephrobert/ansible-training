# Lab 68 — `ansible-lint --profile production` + pre-commit

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : `pipx install ansible-lint pre-commit yamllint`.

## 🧠 Rappel

🔗 [**ansible-lint en mode production**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/ansible-lint-production/)

`ansible-lint` a **6 profils** progressifs :

| Profil | Niveau | Cas d'usage |
| --- | --- | --- |
| `min` | Strict minimum | Code legacy, on veut juste éviter le pire |
| `basic` | Léger | Apprentissage |
| `moderate` | Modéré | Dev en cours |
| `safety` | Sécurité | Audit |
| `shared` | Rôles partagés | Galaxy |
| **`production`** | **Tout strict** | **Code livré en prod** |

Le profil **`production`** est ce qu'attend la **RHCE 2026**. Il vérifie :

- FQCN obligatoire (`ansible.builtin.copy`)
- `name:` sur chaque tâche
- Pas de `command:`/`shell:` quand un module dédié existe
- Idempotence respectée (pas de `changed_when` cassé)
- `meta/main.yml` complet (galaxy_info, platforms, license, version min)
- `meta/argument_specs.yml` présent
- Pas de modules dépréciés
- ...

Et on l'**automatise** avec **pre-commit** : un hook git qui lance
`ansible-lint` à chaque commit. Impossible de pousser du code non-conforme.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Configurer un fichier `.ansible-lint` avec `profile: production`.
2. Configurer `.yamllint` strict (interdire `yes`/`no`, lignes longues, etc.).
3. Écrire un `.pre-commit-config.yaml` qui lance lint + yamllint à chaque
   commit.
4. Activer un hook qui **bloque les fuites de secrets** (private keys).
5. Comprendre l'effet sur la CI : si le pre-commit passe localement, la CI
   passe aussi.

## 🔧 Préparation

```bash
pipx install ansible-lint pre-commit
pipx inject ansible-lint yamllint
```

## ⚙️ Arborescence

```text
labs/tests/ansible-lint-production/
├── README.md
├── Makefile
├── .ansible-lint                 ← profile: production
├── .yamllint                     ← truthy: only true/false
├── .pre-commit-config.yaml       ← hooks ansible-lint + yamllint + secrets
└── roles/webserver/
```

## 📚 Exercice 1 — `.ansible-lint`

```yaml
---
profile: production
strict: true

# Exclusions ciblées
exclude_paths:
  - .cache/
  - .pytest_cache/
  - .tox/

# Activer toutes les règles
enable_list:
  - fqcn-builtins
  - no-handler
  - no-relative-paths
  - no-same-owner
```

🔍 **Observation** : `profile: production` active **~50 règles**. On peut
en désactiver via `skip_list:` mais c'est un signal d'alerte.

## 📚 Exercice 2 — `.yamllint`

```yaml
---
extends: default

rules:
  line-length:
    max: 120
  truthy:
    allowed-values: ['true', 'false']    # interdit yes/no/on/off
    check-keys: false
  comments:
    min-spaces-from-content: 1
  braces:
    max-spaces-inside: 1
```

🔍 **Observation** : `truthy: only true/false` est crucial — YAML 1.2
strict considère `yes` comme une string, pas un booléen. Source de bugs
silencieux.

## 📚 Exercice 3 — `.pre-commit-config.yaml`

```yaml
---
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: detect-private-key       # ← bloque les fuites de clés SSH/TLS
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: ['--strict']

  - repo: https://github.com/ansible/ansible-lint
    rev: v25.0.0
    hooks:
      - id: ansible-lint
        args: ['--profile=production']
```

🔍 **Observation** :

- **`detect-private-key`** : refuse les commits qui contiennent
  `BEGIN PRIVATE KEY` (clé SSH/TLS). Indispensable.
- **`--strict`** sur yamllint : **erreur** (non warning) sur règles violées.
- **`--profile=production`** sur ansible-lint : niveau le plus strict.

## 📚 Exercice 4 — Activer pre-commit

```bash
cd labs/tests/ansible-lint-production
pre-commit install      # installe le hook .git/hooks/pre-commit
pre-commit run --all-files   # exécute manuellement sur tous les fichiers
```

🔍 Désormais, **chaque `git commit`** passera par ces hooks. Si l'un
échoue, le commit est annulé.

## 📚 Exercice 5 — Démontrer un blocage

Modifiez une tâche du rôle pour qu'elle soit non-conforme :

```yaml
- name: Mauvais exemple
  copy:                                   # ← FQCN manquant (anti-pattern)
    src: foo
    dest: /tmp/foo
    mode: 0644                            # ← non quoté (anti-pattern)
```

```bash
git add .
git commit -m "test"
```

🔍 Sortie attendue :

```text
ansible-lint.....................................FAILED
- fqcn[action-core]: Use FQCN for builtin module actions
- yaml[truthy]: Truthy value should be one of [false, true]
```

Le commit est **bloqué**. Vous devez fixer avant de pouvoir pousser.

## 🔍 Observations à noter

- **`profile: production`** = **standard RHCE 2026**. À utiliser dès la
  CI.
- **`pre-commit install`** une fois suffit — le hook persiste dans
  `.git/hooks/`.
- **`detect-private-key`** : la fuite de clé SSH/TLS est l'un des
  incidents les plus fréquents en open source. Hook obligatoire.
- **`yamllint truthy: [true, false]`** : évite les bugs YAML 1.1 vs 1.2.
- **CI redondante** : la CI doit aussi lancer `pre-commit run --all-files`
  pour blocker les contrib externes qui n'auraient pas le hook local.

## 🤔 Questions de réflexion

1. Comment adapter votre solution si la cible passait de **1 host** à un
   parc de **50 serveurs** ? Quels paramètres (`forks`, `serial`, `strategy`)
   faudrait-il ajuster pour conserver des temps d'exécution acceptables ?

2. Quels modules Ansible alternatifs auriez-vous pu utiliser pour atteindre
   le même résultat ? Quels sont leurs trade-offs (idempotence garantie,
   performance, dépendances de collection externe) ?

3. Si une étape du playbook échoue en cours d'exécution, quel est l'impact
   sur les hôtes déjà traités ? Comment rendre le scénario reprenable
   (`block/rescue/always`, `--start-at-task`, `serial`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`ansible-lint --write`** : auto-fixe les anti-patterns simples
  (FQCN, mode quoté).
- **`pre-commit autoupdate`** : met à jour les versions pinned des hooks.
- **GitHub Actions** : un job qui lance `pre-commit run --all-files` —
  redondant avec local mais protège des contributeurs externes.
- **Custom rules** : `ansible-lint` permet d'écrire vos propres règles
  d'entreprise (interdire un module spécifique, etc.).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile production labs/tests/ansible-lint-production/
```
