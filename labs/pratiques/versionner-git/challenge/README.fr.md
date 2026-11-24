# Un playbook que personne ne peut annuler

## La situation

Votre équipe range ses playbooks dans un dossier partagé. La semaine dernière,
quelqu'un a écrasé `site.yml`, le changement a cassé la production, et impossible
de savoir à quoi ressemblait le fichier avant. Pas d'historique, pas de blame,
pas de retour arrière. La solution n'est pas une plateforme sophistiquée : c'est
Git, utilisé comme l'attend l'objectif EX294 « Manage content in a git
repository », ni plus ni moins.

Tout se passe sur **votre propre poste de contrôle**. Aucun managed node, aucune
forge distante : un dépôt **bare** local tient lieu de serveur, ce qui vous fait
pratiquer le `push` sans réseau.

Votre mission :

1. **Initialiser** un dépôt Git pour un petit projet de playbooks, sur la
   branche `main`.
2. Poser une **identité d'auteur locale** sur ce dépôt.
3. **Suivre et committer** les playbooks, puis ajouter un second playbook dans
   son propre commit pour que le dépôt ait un vrai **historique**.
4. **Pousser** l'historique vers un dépôt bare local et confirmer qu'il est bien
   arrivé (même commit des deux côtés).

Restez au niveau de l'objectif : pas de CI, pas de GitOps, pas de forge
distante. Juste init, add, commit, push, faits correctement.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/versionner-git/

## 🎯 Challenge — Versionner ses playbooks avec Git

### ✅ Objectif

Écrire un script Bash `solution.sh` à la racine de **ce répertoire**
(`labs/pratiques/versionner-git/challenge/solution.sh`) qui automatise tout le
cycle de versionnage, dans un **dossier isolé** `challenge/work/` (jamais dans
le dépôt Git du repo ansible-training).

Le script doit :

1. Repartir d'un état propre, puis **initialiser** un dépôt Git dans
   `challenge/work/playbooks` sur la branche `main`.
2. Poser une **identité d'auteur locale** (`git config user.name` et
   `user.email`).
3. Créer des **playbooks** (au moins un `.yml`) et les **suivre** (`git add`).
4. **Committer** avec un message non vide, puis ajouter un **second commit**
   pour construire un historique.
5. Terminer avec un **arbre de travail propre** (tout est committé).
6. Monter un **dépôt bare local** dans `challenge/work/playbooks.git`
   (`git init --bare`), l'ajouter en `origin`, et y **pousser** la branche
   `main`.
7. **Exit 0** si tout s'est bien passé.

Squelette à compléter :

```bash
#!/usr/bin/env bash
set -euo pipefail

# Chemins ABSOLUS, dérivés de l'emplacement du script : le workdir est isolé
# et aucune commande git ne peut remonter vers le dépôt parent.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$SCRIPT_DIR/work"
REPO="$WORKDIR/playbooks"
BARE="$WORKDIR/playbooks.git"

# 0. Repartir d'un état vierge (lab rejouable).
rm -rf "$WORKDIR"; mkdir -p "$REPO"

# 1. Écrire les playbooks dans "$REPO" (site.yml, etc.).
#    Astuce : cat > "$REPO/site.yml" <<'EOF' ... EOF

# 2. git -C "$REPO" init ???   # branche main
# 3. git -C "$REPO" config ??? # identité locale

# 4. git -C "$REPO" add ???    # suivre les fichiers
#    git -C "$REPO" commit ??? # message non vide
#    (ajouter un second playbook + un second commit)

# 5. git init --bare ??? "$BARE"
#    git -C "$REPO" remote add origin "$BARE"
#    git -C "$REPO" push ???   # pousser main
```

> ⚠️ **Piège bash** : dans les `cat <<'EOF'`, gardez le délimiteur entre
> apostrophes (`<<'EOF'`) pour éviter toute interprétation, et méfiez-vous des
> apostrophes dans les messages de commit entre guillemets doubles.

### 🧪 Validation

Les tests **n'inspectent pas le texte** de votre script (ce serait forgeable) :
ils exécutent `solution.sh`, puis interrogent l'**état réel** du dépôt Git
produit (`git log`, `git ls-files`, `git ls-remote`, `git config --local`).

```bash
pytest -v labs/pratiques/versionner-git/challenge/tests/
```

Ce qui est prouvé :

- un dépôt réellement initialisé (`.git/` + `rev-parse --is-inside-work-tree`) ;
- des playbooks **suivis** (`git ls-files` non vide) ;
- un **historique** (au moins deux commits sur la branche `main`), un
  **message** non vide, une **identité locale** posée ;
- un **arbre propre** (rien d'oublié au commit) ;
- un **push reçu** par le bare (même SHA que le HEAD local).

### 🚀 Pour aller plus loin

- Ajoutez un `git tag v1.0` après le second commit et vérifiez-le avec
  `git tag -l`.
- Clonez le bare ailleurs (`git clone challenge/work/playbooks.git /tmp/clone`)
  et constatez que l'historique est intact.
