# Lab 88 — Debug d'un Execution Environment cassé

> 💡 **Pré-requis** : labs 84, 85, 86 validés (vous savez builder et tester un EE).

## 🧠 Rappel

🔗 [**Pièges courants ansible-builder v3**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/ee-builder/#pièges-courants)

Trois **pièges classiques 2026** d'ansible-builder cassent silencieusement un EE :

1. **`version: 3` oublié** : ansible-builder lit en mode v1 hérité, **ignore** les sections de dépendances modernes. Le build "réussit" mais l'EE est vide. **Bug le plus fréquent**.
2. **Collection inexistante dans `requirements.yml`** : `ansible-galaxy` retourne `404` mais l'erreur peut passer inaperçue dans des logs verbeux.
3. **Version Python inexistante** : `kubernetes==9999.0.0` → `pip` retourne `ERROR: No matching distribution found` — souvent confondu avec un problème de proxy.

Ce lab fournit un EE **volontairement cassé** et demande à l'apprenant de **diagnostiquer** puis **corriger**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Reconnaître** un EE qui build "OK" mais ne contient pas ansible-core.
2. **Lire** les logs `ansible-builder build --verbosity 2` pour identifier l'étape qui échoue.
3. **Diagnostiquer** une collection Galaxy inexistante.
4. **Diagnostiquer** une version PyPI inexistante.
5. **Inspecter** un EE construit avec `podman run --rm <ee> ansible --version`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/ee/debug/

# Inspecter le fichier buggy
cat execution-environment-buggy.yml
cat requirements-buggy.yml
cat requirements-buggy.txt
```

## ⚙️ Arborescence

```text
labs/ee/debug/
├── README.md
├── execution-environment-buggy.yml      ← VERSION CASSÉE (3 bugs)
├── requirements-buggy.yml
├── requirements-buggy.txt
└── challenge/
    ├── execution-environment.yml         ← version corrigée
    ├── requirements.yml
    ├── requirements.txt
    ├── bindep.txt
    └── tests/
        └── test_ee_debug.py              ← 6 tests de validation
```

## 📚 Exercice 1 — Tenter le build buggy

```bash
ansible-builder build \
  --tag local/lab88-buggy:dev \
  --container-runtime podman \
  --file execution-environment-buggy.yml \
  --context ./context-buggy \
  --verbosity 2
```

Observation typique :

```text
WARNING: No 'version' key found, defaulting to schema v1
[1/2] Building image...
ERROR: galaxy install failed: collection 'community.does-not-exist' not found
```

🔍 **Le 1er warning est crucial** : sans `version: 3`, ansible-builder utilise le schéma v1. Les sections `dependencies.ansible_core`, `dependencies.python`, `dependencies.system` sont **silencieusement ignorées**. L'EE produit n'a **pas** ansible-core.

## 📚 Exercice 2 — Diagnostic du bug n°1 (version: 3 manquant)

```bash
# Cas où le build "réussit" sans erreur visible mais l'EE est vide :
podman run --rm local/lab88-buggy:dev ansible --version
# → /bin/sh: ansible: command not found
```

🔍 **Diagnostic** : aucune commande `ansible` dans l'image. La cause : **`version: 3` manquant** dans `execution-environment-buggy.yml` → ansible-builder a ignoré la section `dependencies.ansible_core`.

**Correction** : ajouter `version: 3` en première ligne.

## 📚 Exercice 3 — Diagnostic du bug n°2 (collection inexistante)

Une fois `version: 3` ajouté :

```text
[1/3] Galaxy stage:
  Installing community.does-not-exist:1.2.3 ... 
  ERROR! - community.does-not-exist:1.2.3 was NOT installed successfully:
  could not find versions that match: 1.2.3 for: community.does-not-exist
```

🔍 **Diagnostic** : Galaxy retourne **404 / no matching version**. Vérifier l'existence sur https://galaxy.ansible.com/ui/repo/published/community/does-not-exist/.

**Correction** : remplacer par une collection valide (ex: `kubernetes.core`).

## 📚 Exercice 4 — Diagnostic du bug n°3 (version Python inexistante)

```text
[2/3] Python deps:
  ERROR: Could not find a version that satisfies the requirement kubernetes==9999.0.0
  ERROR: No matching distribution found for kubernetes==9999.0.0
```

🔍 **Diagnostic** : `pip` n'a pas trouvé la version sur PyPI. Vérifier sur https://pypi.org/project/kubernetes/.

**Correction** : remplacer par une version réelle (`kubernetes==31.0.0`).

## 📚 Exercice 5 — Build de la version corrigée

```bash
cd challenge/
ansible-builder build \
  --tag local/lab88-fixed:dev \
  --container-runtime podman \
  --file execution-environment.yml \
  --context ../context-fixed \
  --verbosity 2

# Vérifier
podman run --rm local/lab88-fixed:dev ansible --version | head -1
podman run --rm local/lab88-fixed:dev ansible-galaxy collection list
```

Sortie attendue :

```text
ansible [core 2.18.1]

Collection         Version
------------------ -------
ansible.builtin    2.18.1
ansible.posix      2.0.0
kubernetes.core    5.1.1
```

🔍 **Validation finale** : ansible-core présent, collections **réellement** installées, deps Python OK.

## 📚 Exercice 6 — Inspecter le Containerfile généré

```bash
cat ../context-fixed/Containerfile
```

Vous voyez un build **multi-stage** : `base`, `galaxy`, `builder`, `final`. Le stage `final` ne contient que ce qui est utile au runtime (pas les compilers Python qui ont servi au build des wheels).

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible votre poste local + un EE existant ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi ansible-builder accepte-t-il un fichier sans `version:` au lieu de retourner une erreur ?

2. Quelle commande Podman vous permet d'**ouvrir un shell interactif dans l'EE** pour inspecter les fichiers ?

3. Comment **détecter automatiquement** dans la CI qu'un EE construit ne contient pas ansible-core ?

4. **Cache Podman** : modifier `requirements.yml` ne déclenche pas toujours un rebuild de la couche galaxy. Comment forcer ?

## 🚀 Challenge final

Le challenge ([`challenge/tests/`](challenge/tests/)) valide via **6 tests pytest** :

- Les fichiers buggy sont présents (pour le diagnostic).
- Le buggy n'a **pas** `version: 3` (illustration du bug).
- La version corrigée a **bien** `version: 3`.
- La collection inexistante est remplacée.
- La version Python inexistante est corrigée.
- `bindep.txt` ajoute les system deps.

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`ansible-builder create`** (sans `build`) : génère le Containerfile sans build → debug rapide.
- **`podman build --no-cache`** : force le rebuild complet, utile quand le cache masque un bug.
- **`podman run -it --entrypoint /bin/bash <ee>`** : shell interactif dans l'EE pour inspection.
- **`ansible-navigator images --eei <ee>`** : exploration TUI structurée.
- **CI smoke test** : étape post-build qui exécute `ansible --version` dans l'image et fail si absent.

## 🔍 Sécurité — bonnes pratiques 2026

- **`version: 3`** **toujours** en première ligne de `execution-environment.yml`.
- **Smoke test post-build** : `podman run --rm $TAG ansible --version` doit retourner sans erreur.
- **`--verbosity 2`** au minimum dans la CI pour capter les warnings comme « schema v1 default ».
- **Pinning par digest** sur la base image (`@sha256:abc...`) — empêche un repush silencieux upstream.
- **CI smoke test** sur les collections **critiques** : `ansible-doc kubernetes.core.k8s` doit retourner.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/ee/debug/lab.yml
ansible-lint labs/ee/debug/challenge/solution.yml
ansible-lint --profile production labs/ee/debug/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
