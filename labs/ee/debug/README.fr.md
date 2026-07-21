# Lab 88 — Debug d'un Execution Environment cassé

> 💡 **Pré-requis** : labs 84, 85, 86 validés (vous savez builder et tester un EE).

## 🧠 Rappel

🔗 [**Déboguer un Execution Environment cassé**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/debug-ee-casse/)

Les définitions d'EE cassent de façon souvent **silencieuse** : un schéma
mal déclaré fait ignorer des sections entières, une dépendance introuvable
se noie dans des logs verbeux, et un build qui « réussit » peut produire
une image inutilisable. La page liée ci-dessus détaille les pièges
classiques d'ansible-builder.

Ce lab fournit un EE **volontairement cassé** (4 défauts plantés) et vous
demande de **diagnostiquer** puis **corriger**. Les défauts ne sont pas
listés ici : les trouver EST l'exercice.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Reconnaître** un EE qui build "OK" mais ne contient pas ansible-core.
2. **Lire** les logs `ansible-builder build --verbosity 2` pour identifier l'étape qui échoue.
3. **Diagnostiquer** une collection Galaxy inexistante.
4. **Diagnostiquer** une version PyPI inexistante.
5. **Inspecter** un EE construit avec `podman run --rm <ee> ansible --version`.

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING/labs/ee/debug/

# Inspecter le fichier buggy
cat execution-environment-buggy.yml
cat requirements-buggy.yml
cat requirements-buggy.txt
```

## ⚙️ Arborescence

```text
labs/ee/debug/
├── README.md
├── execution-environment-buggy.yml      ← VERSION CASSÉE (4 défauts)
├── requirements-buggy.yml
├── requirements-buggy.txt
└── challenge/
    ├── README.md                         ← votre mission
    └── tests/                            ← validation pytest
        └── test_functional.py

# À produire par vos soins (absents du dépôt) :
# challenge/execution-environment.yml, requirements.yml,
# requirements.txt, bindep.txt
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

🔍 **Lisez TOUT** : les warnings du tout début de build comptent autant que
les erreurs rouges de la fin. Notez chaque anomalie avant de toucher au
moindre fichier.

## 📚 Exercice 2 : un build « réussi » ne prouve rien

```bash
podman run --rm local/lab88-buggy:dev ansible --version
```

🔍 Si cette commande échoue alors que le build est passé, c'est qu'une
partie de votre définition a été **silencieusement ignorée**. Quel warning
du build l'annonçait ? Quelle ligne manque dans la définition pour que
`dependencies.*` soit réellement pris en compte ?

## 📚 Exercice 3 : vérifier chaque dépendance individuellement

Ne croyez pas la définition sur parole : chaque collection et chaque
paquet Python déclarés doivent exister là où ils sont censés être
téléchargés.

```bash
# Une collection déclarée existe-t-elle vraiment, dans cette version ?
ansible-galaxy collection install <namespace.collection>:<version>

# Une version Python déclarée existe-t-elle vraiment sur PyPI ?
pip index versions <paquet>
```

🔍 **Diagnostic** : notez précisément quel composant échoue et pourquoi
(404 Galaxy, no matching distribution PyPI...). C'est ce diagnostic que
vous corrigerez dans `challenge/`.

## 📚 Exercice 4 : les dépendances système

Les collections embarquées s'appuient souvent sur des binaires système
(git, clients ssh...). Comment ansible-builder les installe-t-il dans
l'image ? Quelle section et quel fichier manquent à la définition buggy ?

## 📚 Exercice 5 : build de votre version corrigée

Une fois vos 4 corrections déposées dans `challenge/` :

```bash
cd challenge/
ansible-builder build \
  --tag local/lab88-fixed:dev \
  --container-runtime podman \
  --file execution-environment.yml \
  --context ../context-fixed \
  --verbosity 2

# Vérifier que l'EE est réellement utilisable
podman run --rm local/lab88-fixed:dev ansible --version | head -1
podman run --rm local/lab88-fixed:dev ansible-galaxy collection list
```

🔍 **Validation finale** : ansible-core présent, collections **réellement**
installées, dépendances Python résolues.

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
- **Reset isolé** : `dsoxlab clean <id-du-lab>` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi ansible-builder accepte-t-il un fichier sans `version:` au lieu de retourner une erreur ?

2. Quelle commande Podman vous permet d'**ouvrir un shell interactif dans l'EE** pour inspecter les fichiers ?

3. Comment **détecter automatiquement** dans la CI qu'un EE construit ne contient pas ansible-core ?

4. **Cache Podman** : modifier `requirements.yml` ne déclenche pas toujours un rebuild de la couche galaxy. Comment forcer ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) : les tests pytest
vérifient que vos 4 fichiers corrigés dans `challenge/` règlent chacun des
défauts plantés, et soumettent votre définition à `ansible-builder create`
si l'outil est présent.

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`ansible-builder create`** (sans `build`) : génère le Containerfile sans build → debug rapide.
- **`podman build --no-cache`** : force le rebuild complet, utile quand le cache masque un bug.
- **`podman run -it --entrypoint /bin/bash <ee>`** : shell interactif dans l'EE pour inspection.
- **`ansible-navigator images --eei <ee>`** : exploration TUI structurée.
- **CI smoke test** : étape post-build qui exécute `ansible --version` dans l'image et fail si absent.

## 🔍 Sécurité — bonnes pratiques 2026

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
