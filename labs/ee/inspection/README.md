# Lab 85 — Inspection d'Execution Environments

> 💡 **Pré-requis** : avoir terminé le [lab 84](../84-ee-hello/) (Podman + ansible-navigator installés).

## 🧠 Rappel

🔗 [**Inspecter un EE — images, doc, collections**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/lookup-doc/)

Avant de **builder son propre EE** (lab 86), il faut savoir **inspecter** un EE existant : quelles collections embarquées ? quelle version d'ansible-core ? quelles dépendances Python ? quels packages système ? Ansible Navigator fournit **`ansible-navigator images`** pour cette exploration en TUI, et **`ansible-navigator doc`** pour la doc d'un module donné depuis l'EE.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Lister** les collections d'un EE (`ansible-navigator images` ou `podman run ... ansible-galaxy`).
2. **Comparer** 3 EE communautaires : `creator-ee`, `awx-ee`, `community-ee-minimal`.
3. **Lire la doc** d'un module dans le contexte de l'EE (`ansible-navigator doc`).
4. **Choisir** l'EE adapté à un cas d'usage : formation, AWX, prod minimaliste.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/ee/inspection/
./inspect.sh
```

## ⚙️ Arborescence

```text
labs/ee/inspection/
├── README.md
├── inspect.sh                       ← compare 3 EE et liste collections
└── challenge/
    └── tests/
        └── test_ee_inspection.py    ← tests structurels (4 tests)
```

## 📚 Exercice 1 — Inspection TUI avec ansible-navigator images

```bash
ansible-navigator images --eei quay.io/ansible/creator-ee:latest
```

L'interface TUI s'ouvre avec **5 sections** numérotées :

```text
0 │ Image information     ← ID, taille, registry
1 │ Image layers          ← layers du Dockerfile
2 │ OS release            ← UBI 9 / RHEL 9 / Fedora
3 │ System packages       ← rpm -qa
4 │ Ansible version       ← ansible-core
5 │ Ansible collections   ← ansible-galaxy collection list
6 │ Python packages       ← pip list
7 │ Python version        ← python3 --version
```

Naviguez dans `5` (collections) — vous y trouvez `ansible.posix`, `community.general`, `ansible.utils`, `community.kubernetes`, etc., **avec leurs versions précises**.

🔍 **Observation** : c'est **la** commande pour répondre à « avant de build mon EE, qu'est-ce qui est déjà dans `creator-ee` ? ». Évite de réinstaller des collections déjà présentes.

## 📚 Exercice 2 — Comparer 3 EE communautaires

| EE | Taille | Cas d'usage |
|----|--------|-------------|
| **`quay.io/ansible/creator-ee`** | ~1.2 GB | Formation, dev. Riche : ansible-lint, navigator deps, nombreuses collections. |
| **`quay.io/ansible/awx-ee`** | ~900 MB | AWX upstream. Collections AWX par défaut. |
| **`quay.io/ansible/community-ee-minimal`** | ~400 MB | Base **minimale** — point de départ pour custom EE. |

Lancez le script :

```bash
./inspect.sh
```

Le script pull les 3 EE, affiche les tailles, liste les collections de creator-ee, et compare les versions ansible-core.

🔍 **Observation** : pour **un EE custom production**, partir de **`community-ee-minimal`** et n'ajouter **que** les collections nécessaires est la stratégie qui produit l'image la plus petite et la moins exposée.

## 📚 Exercice 3 — Lire la doc d'un module dans l'EE

```bash
ansible-navigator doc ansible.builtin.copy --eei quay.io/ansible/creator-ee:latest
```

L'interface TUI affiche :

- **Synopsis** du module.
- **Paramètres** avec types, valeurs par défaut, exemples.
- **Examples** YAML directement copiables.
- **Return values** : ce que le module renvoie en `register:`.

🔍 **Observation** : la doc affichée est **celle de la version embarquée dans l'EE**, pas la doc internet. Garantit que les paramètres mentionnés sont bien disponibles avec la version Ansible utilisée.

## 📚 Exercice 4 — Lister les collections embarquées (mode CLI)

```bash
ansible-navigator collections --eei quay.io/ansible/creator-ee:latest
```

Sortie :

```text
0 │ ansible.builtin           2.18.1
1 │ ansible.posix             2.0.0
2 │ community.general         10.5.0
3 │ kubernetes.core            5.1.1
…
```

Pour un format scriptable :

```bash
podman run --rm quay.io/ansible/creator-ee:latest \
  ansible-galaxy collection list --format json | jq
```

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible votre poste local ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pour une formation Ansible **avec K8s**, quel EE prendre ? Pourquoi ?

2. Pour une production prod **minimaliste** ne déployant **que** des serveurs Linux, quel EE ?

3. Comment **vérifier** qu'un EE contient une collection précise et sa version, **sans** le pull localement ?

4. Pourquoi `creator-ee` est-il le plus volumineux ? Que peut-on retirer pour faire son propre EE plus léger ?

## 🚀 Challenge final

Le challenge ([`challenge/tests/`](challenge/tests/)) valide que le script d'inspection référence bien les 3 EE et utilise les commandes de référence.

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`ansible-navigator config`** : voir la config Ansible **dans** l'EE (différente de la config locale).
- **`skopeo inspect docker://quay.io/...`** : inspecter sans pull (économise la bande passante).
- **`crane manifest`** : alternative à skopeo, plus rapide.
- **Lab 86** : créer son propre EE custom.
- **Red Hat AAP EE** : `ee-supported-rhel9` contient les collections **certifiées Red Hat**.
